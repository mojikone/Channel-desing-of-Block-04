import re, sys, collections
p=sys.argv[1]; txt=open(p,encoding="utf-8").read()
blocks=re.findall(r'^(Subbasin|Junction|Reach|Reservoir): (.+?)\n(.*?)^End:', txt, re.S|re.M)
names=[n for t,n,b in blocks]; dup=[n for n,c in collections.Counter(names).items() if c>1]
g=lambda b,k: (re.search(r'^\s*'+re.escape(k)+r': (.*)$', b, re.M) or [None,None])[1]
el={n:(t,g(b,"Downstream")) for t,n,b in blocks}
missing=[(n,d) for n,(t,d) in el.items() if d not in (None,"None") and d not in el]
up=collections.defaultdict(list)
for n,(t,d) in el.items(): up[d].append(n)
reach_in=[(n,up[n]) for n,(t,d) in el.items() if t=="Reach" and len([u for u in up[n] if el[u][0] not in ("Subbasin",)])!=1 ]
sub_to_reach=[(n,d) for n,(t,d) in el.items() if t=="Subbasin" and d in el and el[d][0]=="Reach"]
dangling_j=[n for n,(t,d) in el.items() if t=="Junction" and not up[n]]
terminals=[n for n,(t,d) in el.items() if d in (None,"None")]
cnt=collections.Counter(t for t,n,b in blocks)
# cycles
def reaches_end(n, seen=()):
    k=0
    while n in el and el[n][1] not in (None,"None"):
        n=el[n][1]; k+=1
        if k>10000: return False
    return True
cyc=[n for n in el if not reaches_end(n)]
areas=[float(g(b,"Area")) for t,n,b in blocks if t=="Subbasin"]; lags=[float(g(b,"Lag")) for t,n,b in blocks if t=="Subbasin"]; cns=[float(g(b,"Curve Number")) for t,n,b in blocks if t=="Subbasin"]
slopes=[float(g(b,"Energy Slope")) for t,n,b in blocks if t=="Reach"]; lens=[float(g(b,"Length")) for t,n,b in blocks if t=="Reach"]
print("elements:", dict(cnt), "| duplicates:", dup, "| missing downstream targets:", missing[:5], "| cycles:", cyc[:5])
print("reaches without exactly one upstream junction:", reach_in[:5], "| subbasins draining into a reach:", sub_to_reach[:5], "| junctions with no inflow:", dangling_j[:8])
print("terminal elements:", terminals)
print(f"area total {sum(areas):.1f} km2, min {min(areas):.4f} | lag {min(lags):.1f}-{max(lags):.1f} min | CN {min(cns):.1f}-{max(cns):.1f} | reach slope {min(slopes):.5f}-{max(slopes):.5f}, length {min(lens):.0f}-{max(lens):.0f} m")
