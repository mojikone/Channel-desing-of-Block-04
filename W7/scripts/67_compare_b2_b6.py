"""Basin 2 (no reservoirs) vs Basin 6 (reservoirs, Shafan 08 included): peak flows at the dam junctions / reservoir outflows and the outfalls."""
import sys, pandas as pd
R = sys.argv[1].rstrip("/\\") + "/"
p2 = pd.read_excel(R + "basin2_peak_flow_volume.xlsx", sheet_name="peak flow m3s", index_col=0); p3 = pd.read_excel(R + "basin6_peak_flow_volume.xlsx", sheet_name="peak flow m3s", index_col=0)
dams = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
rps = ["10yr", "100yr", "200yr", "1000yr", "PMP"]
rows = []
for d in dams:
    for rp in rps:
        rows.append(dict(dam=d, rp=rp, inflow=round(p2.loc[d, rp]), outflow=round(p3.loc[d + " Reservoir", rp]), attenuation_pct=round((1 - p3.loc[d + " Reservoir", rp] / p2.loc[d, rp]) * 100, 1)))
dd = pd.DataFrame(rows); pd.set_option("display.width", 250)
print("dam inflow (Basin 2 junction) vs reservoir outflow (Basin 3), m3/s:"); print(dd.pivot(index="dam", columns="rp", values="outflow")[rps].to_string()); print("\nattenuation %:"); print(dd.pivot(index="dam", columns="rp", values="attenuation_pct")[rps].to_string())
outs = [i for i in p2.index if "-O" in i and i.split("-O")[1].isdigit()]
o = pd.DataFrame({f"B2 {rp}": p2.loc[outs, rp].round(0) for rp in ["100yr", "200yr"]} | {f"B6 {rp}": p3.loc[outs, rp].round(0) for rp in ["100yr", "200yr"]})
o["change 200yr %"] = ((o["B6 200yr"] / o["B2 200yr"] - 1) * 100).round(1); print("\noutfalls:"); print(o.to_string())
dd.to_csv(R + "dams_inflow_vs_outflow_B6.csv", index=False); o.to_csv(R + "outfalls_B2_vs_B6.csv")
