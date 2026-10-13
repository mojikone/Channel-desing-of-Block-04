"""One-off: verify Basin 3 widths against the applied table, then update W2 README, live README and project memory."""
import re, pandas as pd
B = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/"
# ---- 1. widths check
txt = open(B + "Hydrology/HEC_HMS_Block_04/Basin_3.basin", encoding="utf-8").read()
g = lambda s, k: (re.search(r'^\s*' + re.escape(k) + r': (.*)$', s, re.M) or [None, None])[1]
w = {n: float(g(s, "Bottom Width")) for n, s in re.findall(r'^Reach: (.+?)\r?\n(.*?)^End:', txt, re.S | re.M)}
a = pd.read_csv(B + "Claude Block 04/W2/output/hms/Basin_3_reach_sizing_Q200.csv"); ch = a[a.kind == "channel"]
bad = [(r.reach, r.b_new, w.get(r.reach)) for r in ch.itertuples() if abs(w.get(r.reach, -1) - r.b_new) > 0.05]
print("channel reaches:", len(ch), "| mismatches:", bad[:5] or "none")
print(ch[ch.reach.str.match(r"HAW-R2\d$")][["reach", "Q200_m3s", "b_old", "b_new"]].to_string(index=False))

# ---- 2. W2 README
p = B + "Claude Block 04/W2/README.md"; L = open(p, encoding="utf-8").read().split("\n")
assert L[159].startswith("- **Channel sections in Basin 3**") and L[164].startswith("  `outfalls_B2_vs_B3.csv`"), (L[159], L[164])
new = """- **Channel sections in Basin 3** are sized separately, with the same rule (n 0.1, 1V:3H, 2 m depth) but on the
  reservoir-routed 200-year flows (`output/hms/Basin_3_reach_sizing_Q200.csv` = the applied table): pass 1 = the 13
  analyses computed with Basin 2's sections (kept as `results/*_pass1_B2sections.*`), widths derived from them and
  written to `Basin_3.basin`, then the 13 analyses recomputed (final results, 2026-10-05 late evening). Below
  Hawasinah EX the 200-year flow falls from 5 900 to about 180 m³/s and HAW-R21 from 2 308 to 66 m bottom width;
  6 reaches remain over 1 km.
- **Error found and corrected the same day.** The first version of `size_reaches.py` read `Basin_3.basin` but wrote
  the result to `Basin_2.basin` (hard-coded output name). For about ten hours the project's `Basin_2.basin` was a copy
  of Basin 3 (header "Basin 3", eight reservoirs, Basin 3 widths) while Basin 3 kept Basin 2's widths; the engineer
  noticed HAW-R21 at 2 308 m in Basin 3. Fix: Basin 2 restored from `_backup_before_reservoirs_20261005_125741`
  (byte-identical to the file that produced the Basin 2 results, HAW-R21 2 308.2 m, no reservoirs); Basin 3 re-sized
  (HAW-R21 66.1 m, all 81 channel widths verified against the table); the 13 Basin 3 analyses recomputed. The
  wrong-file versions are kept in `../../model/_sizing_backups/`. Lesson: after writing any basin file, check the
  header line, the element counts and one known value in **every** basin file of the project, not only the target.
- **Sensitivity to the sections** (`results/basin3_peak_flow_volume.xlsx` vs `*_pass1_B2sections.xlsx`): reservoir
  outflows and levels unchanged; the narrower channels attenuate less, so the 200-year peaks rise by 7–10% at HAW-O1,
  SAK-O1 and SHA-O5 and by up to 33% on SAR-R12/R13 (9 of 115 reaches change by more than 5%). A second sizing pass
  on the new flows (`results/Basin_3_reach_sizing_Q200_pass2_check.csv`, **not applied**) would widen 8 of 81 channel
  reaches by more than 10% (SAR-R12/R13 +34%, SHA-R48…R52 +14–16%, SAK-R21 +9%); the rest stay within a few %.
- Results: `output/hms/results/basin3_peak_flow_volume.xlsx`; `dams_inflow_vs_outflow.csv` and
  `outfalls_B2_vs_B3.csv` from `scripts/compare_b2_b3.py`; `reservoir_max_elevation.csv` from
  `scripts/reservoir_levels.py`.""".split("\n")
L[159:165] = new; open(p, "w", encoding="utf-8", newline="\n").write("\n".join(L)); print("W2 README updated")

# ---- 3. live README
p = B + "Claude Block 04/README.md"; s = open(p, encoding="utf-8").read(); n0 = len(s)
def rep(a, b):
    global s; assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("Last update 2026-10-05.", "Last update 2026-10-05 (late evening: Basin 3 recomputed with its own channel sections).")
rep("snapshot of the HMS project files after the runs (.hms, .run, .nals, .pdata, .dss, .met).",
    "snapshot of the HMS project files after the runs (.hms, .run, .nals, .pdata, .dss, .met); `_sizing_backups/` = basin files as they were before each width rewrite, including the wrong-file versions of the 2026-10-05 incident (see findings).")
rep("reservoir peak levels, channel sizing tables, element rename map |",
    "reservoir peak levels, channel sizing tables (applied) and the second-pass check `Basin_3_reach_sizing_Q200_pass2_check.csv` (not applied), element rename map. The first-pass Basin 3 results (computed with Basin 2's sections) are kept only in `W2/output/hms/results/*_pass1_B2sections.*` |")
rep("""- With n 0.1 and 2 m depth the undammed FP channels below the dams come out 1–6 km wide (Basin 2); with the
  reservoirs (Basin 3) the Hawasinah EX channel carries ~170 instead of 5 900 m³/s at 200 years and is 49 m wide.""",
"""- With n 0.1 and 2 m depth the undammed FP channels below the dams come out 1–6 km wide (Basin 2); with the
  reservoirs (Basin 3) the channel below Hawasinah EX (HAW-R21) carries ~180 instead of 5 900 m³/s at 200 years and
  is 66 m instead of 2 308 m wide; 6 Basin 3 reaches are still over 1 km.
- The sections feed back on the flows: Basin 3 with its own (narrower) sections gives 200-year peaks 7–10% higher at
  HAW-O1, SAK-O1 and SHA-O5 and up to 33% higher on SAR-R12/R13 than the same basin with Basin 2's sections (less
  Muskingum-Cunge attenuation); reservoir outflows and levels do not change.
- **Incident 2026-10-05:** the first sizing script read `Basin_3.basin` and wrote `Basin_2.basin`, so Basin 2 became a
  copy of Basin 3 and Basin 3 kept Basin 2's widths until the engineer spotted HAW-R21 at 2 308 m. Basin 2 was
  restored from the pre-reservoir backup (identical to the file behind the Basin 2 results), Basin 3 re-sized and
  recomputed. Rule since then: after writing any basin file, check header, element counts and one known value in
  **every** basin file of the project.""")
rep("""Six dams store the whole 100-year flood; Hawasinah 02 (11 Mm³
  on 420 km²) attenuates almost nothing""", """Five dams store the whole 100-year flood and Hawasinah 11 all but
  15 m³/s; Hawasinah 02 (11 Mm³ on 420 km²) attenuates almost nothing""")
rep("""4. Second sizing pass (widths change routing by a few %) not done; Hawasinah EX inflow differs from Basin 1 by the
   S111 merge (engineer: "no need" to revert).""", """4. Second sizing pass not applied: on Basin 3 it would widen 8 of 81 channel reaches by more than 10% (SAR-R12/R13
   +34%, SHA-R48…R52 +14–16%; `results/Basin_3_reach_sizing_Q200_pass2_check.csv`), the rest by a few %. Engineer to
   decide whether to iterate. Hawasinah EX inflow differs from Basin 1 by the S111 merge (engineer: "no need" to revert).""")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("main README updated", n0, "->", len(s))

# ---- 4. memory
p = r"C:\Users\mojtaba\.claude\projects\D--Mojtaba-Renardet-2224-WS11-Batinah-Block-4\memory\batinah-block4-flood-channels.md"; s = open(p, encoding="utf-8").read()
rep("HMS Basin 2 (dams + channels) built 2026-10-05 in W2, not yet run; hydraulics folder still empty",
    "HMS Basin 2 (dams + channels) and Basin 3 (+ reservoirs) built and run 2026-10-05 (W2, results in Claude Block 04/results); hydraulics folder still empty")
rep("Results in W2/output/hms/results. Dams fully absorb the 100-yr except Hawasinah 02 and Sakhin 08; PMP heads reach ~5 m = design Hmax.",
    "Results in `Claude Block 04/results` (current) and W2/output/hms/results (incl. `*_pass1_B2sections.*` = Basin 3 computed with Basin 2's sections). Dams fully absorb the 100-yr except Hawasinah 02 and Sakhin 08 (Hawasinah 11 passes 15 m³/s); PMP heads reach ~5 m = design Hmax. Basin 3 final results (2026-10-05 late) use its own sections; a second sizing pass was NOT applied (would widen 8/81 channel reaches >10%, SAR-R12/13 +34%) — engineer to decide. Incident 2026-10-05: `size_reaches.py` wrote Basin 3 content into `Basin_2.basin` for ~10 h; Basin 2 restored from `_backup_before_reservoirs_20261005_125741`. Rule: after writing any .basin, check header, element counts and one known width in EVERY basin file.")
rep("design flows come from HMS Basin 2 once run (dam inflows only, no attenuation)",
    "design flows come from HMS Basin 2 (no reservoirs) or Basin 3 (routed through the dam reservoirs) in `Claude Block 04/results/basin2|3_peak_flow_volume.xlsx`")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("memory updated")
