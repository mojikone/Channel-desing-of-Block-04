"""Step 07 - load the W4 command assembly into the running Civil 3D and run W4BUILD on the template drawing, through
Civil 3D's COM automation interface (no dialogs, no clicks). The assembly must sit at a path without spaces.
Guard: nothing is sent unless the active document is the W4 template drawing."""
import sys, time
import win32com.client
DLL = "C:/Civil3D-mcp/tools/W4Tools.dll"; TARGET = "Block04_Channels_Surfaces_C3Dtemplate.dwg"
app = win32com.client.GetActiveObject("AutoCAD.Application"); doc = app.ActiveDocument
print("active:", doc.Name, flush=True)
if doc.Name != TARGET: print("the active document is not", TARGET, "; nothing sent"); sys.exit(1)
def cmd(s, wait=1.0): doc.SendCommand(s + "\n"); time.sleep(wait)
if "--noload" not in sys.argv:                      # the assembly stays loaded for the session: --noload just runs the command
    cmd('(setvar "FILEDIA" 0)')
    cmd('(command "NETLOAD" "%s")' % DLL, 4.0)
    cmd('(setvar "FILEDIA" 1)')
t = time.time(); cmd(next((a for a in sys.argv[1:] if not a.startswith("--")), "W4BUILD"), 2.0); print("command returned after %.0f s" % (time.time() - t), flush=True)
