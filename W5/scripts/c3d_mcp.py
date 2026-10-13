"""Client for the civil3d-roslyn MCP server (nezolder/civil3d-mcp-roslyn, installed at C:\\mcp\\civil3d-mcp-roslyn): speaks
MCP over stdio to the same Node server Claude Code uses, so scripts can run C# inside Civil 3D from Python.
    s = McpSession(); s.identity(); s.query(code); s.execute(code, save=False); s.skills("list"); s.api_lookup("ProfileViewStyle")
A query runs read-only (no commit); execute commits its transaction and, with save=True, saves the named drawing.
The C# code is a method body with the globals Document, CivilDoc, Database, Transaction, Editor; `return x;` comes back as JSON.
Usage from the command line:  python c3d_mcp.py query  file.cs   |   python c3d_mcp.py execute file.cs [--save]"""
import json, os, subprocess, sys, threading, queue, itertools, time
SERVER = ["node", r"C:\mcp\civil3d-mcp-roslyn\build\index.js"]
LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log", "c3d_mcp.log")


class McpError(RuntimeError):
    pass


class McpSession:
    def __init__(self, command_timeout_ms=600000, log_level="warn"):
        env = dict(os.environ); env["CIVIL3D_COMMAND_TIMEOUT"] = str(command_timeout_ms); env["LOG_LEVEL"] = log_level
        port = self.discover_port()
        if port: env["CIVIL3D_PORT"] = str(port)   # pin the Roslyn plugin: the older Sacred-G plugin on 8080 is otherwise probed as a second instance
        self.p = subprocess.Popen(SERVER, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  encoding="utf-8", bufsize=1, env=env)
        self.q = queue.Queue(); self.ids = itertools.count(1); self.err = []; self._identity = None
        threading.Thread(target=self._pump, daemon=True).start(); threading.Thread(target=self._err, daemon=True).start()
        self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "w5-client", "version": "0.1"}}, 30)
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    @staticmethod
    def discover_port():
        """The port of the newest live Roslyn plugin from its endpoint record (%LOCALAPPDATA%\\Civil3dMcpRoslyn\\endpoints)."""
        d = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Civil3dMcpRoslyn", "endpoints")
        try: recs = sorted(os.listdir(d))
        except OSError: return None
        for name in reversed(recs):
            try:
                r = json.load(open(os.path.join(d, name), encoding="utf-8"))
                if subprocess.run(["tasklist", "/FI", "PID eq %d" % r["processId"]], capture_output=True, text=True).stdout.find(str(r["processId"])) >= 0: return r["port"]
            except Exception: continue
        return None

    # ---- transport
    def _pump(self):
        for line in self.p.stdout:
            line = line.strip()
            if not line: continue
            try: self.q.put(json.loads(line))
            except json.JSONDecodeError: self.err.append("stdout: " + line[:300])

    def _err(self):
        for line in self.p.stderr: self.err.append(line.rstrip())

    def _send(self, msg):
        self.p.stdin.write(json.dumps(msg) + "\n"); self.p.stdin.flush()

    def request(self, method, params, timeout=660):
        rid = next(self.ids); self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}); t0 = time.time()
        while True:
            left = timeout - (time.time() - t0)
            if left <= 0: raise McpError("timeout waiting for %s (%d s); stderr tail: %s" % (method, timeout, self.err[-3:]))
            try: msg = self.q.get(timeout=min(left, 5))
            except queue.Empty: continue
            if msg.get("id") == rid:
                if "error" in msg: raise McpError(json.dumps(msg["error"])[:2000])
                return msg["result"]
            # notifications and server requests are ignored (logged)
            self.err.append("other message: " + json.dumps(msg)[:300])

    # ---- tools
    def call(self, name, args, timeout=660):
        r = self.request("tools/call", {"name": name, "arguments": args}, timeout)
        text = "\n".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s %s\n%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), name, "ERROR" if r.get("isError") else "ok", text[:4000]))
        if r.get("isError"): raise McpError(text[:4000] + ("\n" + json.dumps(r.get("structuredContent"))[:1000] if r.get("structuredContent") else ""))
        return text

    @staticmethod
    def parse(text):
        try: return json.loads(text)
        except json.JSONDecodeError: return text

    def identity(self):
        """Bootstrap: the active drawing's identity, required for every execute."""
        t = self.call("civil3d_query", {"code": "return new { filename = Database.Filename, guid = Database.FingerprintGuid.ToString(), name = Document.Name };"}, 60)
        d = self.parse(t); d = d.get("result", d) if isinstance(d, dict) else d
        self._identity = {"databaseFilename": d["filename"], "fingerprintGuid": d["guid"]}
        return d

    def query(self, code, timeout=660):
        args = {"code": code}
        if self._identity: args["expectedDrawing"] = self._identity
        return self.parse(self.call("civil3d_query", args, timeout))

    def execute(self, code, save=False, description=None, timeout=660):
        if not self._identity: self.identity()
        args = {"code": code, "expectedDrawing": self._identity, "saveDrawing": bool(save)}
        if description: args["description"] = description
        return self.parse(self.call("civil3d_execute", args, timeout))

    def skills(self, action="list", **kw):
        return self.parse(self.call("civil3d_skills", dict(action=action, **kw), 60))

    def api_lookup(self, query, namespace=None, limit=40):
        args = {"action": "api_lookup", "query": query, "limit": limit}
        if namespace: args["namespace"] = namespace
        return self.parse(self.call("civil3d_skills", args, 60))

    def close(self):
        try: self.p.stdin.close(); self.p.wait(5)
        except Exception: self.p.kill()


def load_cs(path, **subst):
    """Read a C# body and substitute {{KEY}} placeholders."""
    code = open(path, encoding="utf-8").read()
    for k, v in subst.items(): code = code.replace("{{%s}}" % k, str(v))
    return code


if __name__ == "__main__":
    mode, path = sys.argv[1], sys.argv[2]; save = "--save" in sys.argv
    out_path = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    s = McpSession(); print("identity:", s.identity(), file=sys.stderr)
    code = load_cs(path)
    out = s.query(code) if mode == "query" else s.execute(code, save=save)
    if isinstance(out, dict) and set(out) >= {"result"}: out = out["result"]
    text = json.dumps(out, indent=1, ensure_ascii=False) if not isinstance(out, str) else out
    if out_path: open(out_path, "w", encoding="utf-8").write(text); print("written", out_path, len(text), "chars", file=sys.stderr)
    else: print(text)
    s.close()
