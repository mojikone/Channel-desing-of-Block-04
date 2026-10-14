Block 04 - conduits of the SewerGEMS hydraulic design, revision R9, with the designed sizes (for the HEC-RAS check)

Geometry: the 212 conduits as exported from SewerGEMS (same lines and node labels as Channels.shp / Nodes.shp). CRS: WGS 84 / UTM zone 40N (EPSG:32640).
Do not use SPAN or SIZE of Channels.shp: SPAN there is the conduit's stored value (10 m for all, never updated for catalogue conduits) and SIZE is the catalogue item identifier. The designed sizes are in this file.

Section: rectangular (SewerGEMS catalogue class 'Rect- Natural', Manning n 0.030), WIDTH_M = designed bed width at 200 years, DEPTH_M = clear depth of the class (2.5 m, 3.0 m where deeper).
Fields: LABEL conduit; CHANNEL, CLASS channel and class (FP flood protection, Sw M stormwater main, Sw S stormwater secondary); FROM_NODE, TO_NODE node labels;
  LENGTH_M; INV_UP_M, INV_DN_M upstream and downstream inverts (m, 200-year scenario); SLOPE (m/m); SHAPE, CLASS_SG SewerGEMS shape and class; SIZE as text 'depth x width';
  Q200_M3S design flow 200-year (m3/s); V200_MS velocity; Y200_IN_M, Y200_OUT_M flow depth at the upstream and downstream ends (200-year, GVF).
  W_<rp>, D_<rp>, Q_<rp>, S_<rp>: designed width, depth, flow and slope of the scenario of each return period (2, 5, 10, 25, 50, 100, 200, 500 years); the inverts of those scenarios differ from the 200-year ones where the slope differs.

Source: SewerGEMS Block 04 R9 (all eight scenarios designed), sizes resolved per conduit from the catalogue class and item.
