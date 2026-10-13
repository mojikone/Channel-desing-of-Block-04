"""Build the complete plan-profile drawing set as ONE PDF (engineer, 2026-10-11): a cover, the table of drawings, then for each
global catchment (Al Hawasinah, Sakhin, Sarami, Shafan, in the drawing-number order of config.CATCHMENT_ORDER) a divider page
followed by its channels' key maps and sheets (the latest combined PDF of each channel written by export_pdf.py). Cover, table and
dividers are A1 landscape like the sheets and repeat the sheets' own title-block lines (client, project, design stage, revision,
date); nothing else is added. Bookmarks: cover, table, catchment > channel > drawing. Beside the PDF: <name>_contents.csv.
    python make_set.py [--basis "Hydraulic design for the 200-year return period"] [--tag R5] [--out <path.pdf>]
"""
import os, sys, csv, math, datetime
import pikepdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, landscape
from reportlab.lib.units import mm
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from config import DOC_NO_PREFIX, OUT_PDF
from run_all import available_channels, assign_drawing_numbers, _channel_sort_key
from view_frames import compute_view_frames

A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
BASIS = opt("--basis", "Hydraulic design for the 200-year return period")
TAG = opt("--tag", "")                                                   # revision tag in the file name (engineer, 2026-10-12: keep earlier sets)
ONLY = [c.strip().upper() for c in opt("--only", "").split(",") if c.strip()]   # W8: the stormwater set = the SM and SS channels only
CATMAP_SUFFIX = opt("--catmap-suffix", "")                                     # W8: "_sw" = the key plans with the flood protection channels dimmed
KIND = opt("--kind", "FLOOD PROTECTION CHANNELS")
OUT = opt("--out", os.path.join(OUT_PDF, "Set", DOC_NO_PREFIX + ("_Stormwater_Channels" if ONLY else "") + "_Plan_and_Profile_Drawings_200yr" + ("_" + TAG if TAG else "") + ".pdf"))
CATCHMENT = {"HAW": "Al Hawasinah", "SAK": "Sakhin", "SAR": "Sarami", "SHA": "Shafan"}
# the lines below are the sheets' own title-block texts (template + make_sheet), repeated here so the cover invents nothing
CLIENT = ["SULTANATE OF OMAN", "MINISTRY OF AGRICULTURE, FISHERIES WEALTH AND WATER RESOURCES"]
PROJECT = ["FLOOD PROTECTION SCHEME IN", "NORTH AND SOUTH AL BATINAH GOVERNORATES", "BLOCK 04"]
STAGE = "Flood Protection Channel"; TITLE = ["PLAN AND PROFILE DRAWINGS", "OF THE " + KIND]
CONSULTANT = ["RENARDET S.A. & PARTNERS", "Consulting Engineers LLC."]
REV = "1"; DATE = datetime.date.today().strftime("%d.%m.%Y")
W, H = landscape(A1)                                              # 841 x 594 mm, the sheets' size
M = 25 * mm                                                       # margin

# ---------------------------------------------------------------- the drawings, in the order of the numbers
chs_all = sorted(available_channels(), key=_channel_sort_key); nums = assign_drawing_numbers(chs_all)   # numbers over ALL channels
chs = [c for c in chs_all if not ONLY or c.upper().rsplit("-", 1)[-1] in ONLY]
if ONLY: print("stormwater set: %d of %d channels (%s)" % (len(chs), len(chs_all), ", ".join(ONLY)))
cats = []                                                         # [(code, name, [channels])]
for ch in chs:
    code = ch.split("-")[0].upper()
    if not cats or cats[-1][0] != code: cats.append((code, CATCHMENT.get(code, code), []))
    cats[-1][2].append(ch)
rows = []                                                         # one per drawing: key map, then the sheets
for ch in chs:
    _, frames = compute_view_frames(ch); code = ch.split("-")[0].upper()
    rows.append(dict(dwg=nums[(ch, "km")], cat=CATCHMENT.get(code, code), ch=ch, drawing="Key map", s0="", s1=""))
    for f in frames: rows.append(dict(dwg=nums[(ch, f.index)], cat=CATCHMENT.get(code, code), ch=ch, drawing="Sheet %d of %d" % (f.index, len(frames)), s0=f.sta_start, s1=f.sta_end))
ROW_H = 6.5 * mm; TOP = 68 * mm; BOT = 25 * mm; HEAD = 12 * mm   # W8: the header band (TOP-HEAD .. TOP) below the document line at 50 mm
R = int((H - TOP - BOT - HEAD) // ROW_H); PER_PAGE = 2 * R; T = max(1, math.ceil(len(rows) / PER_PAGE))
page = 1 + T + 1                                                  # the first drawing follows the cover, the table pages and the first divider
pages = {}                                                        # channel -> first page (its key map); divider pages by catchment code
for code, name, lst in cats:
    pages[code] = page; page += 2                                 # W8: the divider, then the key plan of the catchment
    for ch in lst: pages[ch] = page; page += 1 + len(compute_view_frames(ch)[1])
k = 0
for ch in chs:
    for f in range(1 + len(compute_view_frames(ch)[1])): rows[k]["page"] = pages[ch] + f; k += 1
print("%d channels, %d drawings, %d table page(s), %d pages in the set" % (len(chs), len(rows), T, page - 1))


# ---------------------------------------------------------------- the pages drawn here (reportlab), A1 landscape
def centred(c, y, text, size, font="Helvetica"):
    c.setFont(font, size); c.drawCentredString(W / 2, y, text)


def frame(c):
    c.setLineWidth(1.2); c.rect(10 * mm, 10 * mm, W - 20 * mm, H - 20 * mm)


def cover(c):
    frame(c); y = H - 75 * mm
    for t in CLIENT: centred(c, y, t, 34, "Helvetica-Bold"); y -= 16 * mm
    y -= 30 * mm
    for t in PROJECT: centred(c, y, t, 44, "Helvetica-Bold"); y -= 20 * mm
    y -= 22 * mm
    for t in TITLE: centred(c, y, t, 60, "Helvetica-Bold"); y -= 27 * mm
    y -= 6 * mm; centred(c, y, BASIS, 30); y -= 18 * mm; centred(c, y, "Design stage: " + STAGE, 24); y -= 40 * mm
    centred(c, y, "Drawing set %s" % DOC_NO_PREFIX, 28, "Helvetica-Bold"); y -= 14 * mm; centred(c, y, "Revision %s    %s" % (REV, DATE), 24)
    centred(c, 50 * mm, CONSULTANT[0], 30, "Helvetica-Bold"); centred(c, 38 * mm, CONSULTANT[1], 24); c.showPage()


def table(c):
    cols = [("No.", 16), ("Drawing No.", 64), ("Catchment", 48), ("Channel", 48), ("Drawing", 56), ("Station from", 38), ("Station to", 38), ("Page", 24)]
    half = (W - 2 * M - 15 * mm) / 2
    for p in range(T):
        frame(c); centred(c, H - 40 * mm, "TABLE OF DRAWINGS" + (" (continued)" if p else ""), 36, "Helvetica-Bold")
        c.setFont("Helvetica", 14); c.drawCentredString(W / 2, H - 50 * mm, "%s    Revision %s    %s    Sheet %d of %d" % (DOC_NO_PREFIX, REV, DATE, p + 1, T))
        for col in range(2):
            x0 = M + col * (half + 15 * mm); chunk = rows[p * PER_PAGE + col * R: p * PER_PAGE + (col + 1) * R]
            if not chunk: continue
            y = H - TOP; x = x0; c.setFont("Helvetica-Bold", 12)
            for name, wmm in cols: c.drawString(x + 1.5 * mm, y + 2 * mm, name); x += wmm * mm
            c.setLineWidth(0.8); c.line(x0, y, x, y); c.line(x0, y + HEAD, x, y + HEAD)
            c.setFont("Helvetica", 11); c.setLineWidth(0.2)
            for i, r in enumerate(chunk):
                yy = y - (i + 1) * ROW_H; vals = [str(p * PER_PAGE + col * R + i + 1), r["dwg"], r["cat"], r["ch"], r["drawing"], r["s0"], r["s1"], str(r["page"])]
                x = x0
                for (name, wmm), v in zip(cols, vals): c.drawString(x + 1.5 * mm, yy + 1.8 * mm, v); x += wmm * mm
                c.line(x0, yy, x, yy)
            xx = x0
            for name, wmm in cols: c.line(xx, y + HEAD, xx, yy); xx += wmm * mm
            c.line(xx, y + HEAD, xx, yy)
        c.showPage()


def divider(c, code, name, lst):
    frame(c); centred(c, H - 150 * mm, "PLAN AND PROFILE DRAWINGS", 40); centred(c, H - 230 * mm, name.upper(), 150, "Helvetica-Bold")
    centred(c, H - 262 * mm, "%s catchment    %d channels" % (name, len(lst)), 28)
    centred(c, H - 284 * mm, "Key plan of the catchment on the next page: the channels and dykes with their names, their extents and the stations", 16)
    y = H - 320 * mm; c.setFont("Helvetica", 18)
    for ch in lst:
        n = len(compute_view_frames(ch)[1]); c.drawCentredString(W / 2, y, "%s    drawings %s to %s    pages %d to %d" % (ch, nums[(ch, "km")], nums[(ch, n)], pages[ch], pages[ch] + n)); y -= 9.5 * mm
    c.showPage()


os.makedirs(os.path.dirname(OUT), exist_ok=True)
front = os.path.join(os.path.dirname(OUT), "_front.pdf"); c = canvas.Canvas(front, pagesize=(W, H)); cover(c); table(c); c.save()
divs = {}
for code, name, lst in cats:
    f = os.path.join(os.path.dirname(OUT), "_divider_%s.pdf" % code); c = canvas.Canvas(f, pagesize=(W, H)); divider(c, code, name, lst); c.save(); divs[code] = f

# ---------------------------------------------------------------- the set (pikepdf): front pages, then per catchment the divider and the channels
out = pikepdf.new(); keep = []
def add(path):
    src = pikepdf.open(path); keep.append(src); out.pages.extend(src.pages); return len(src.pages)
add(front)
for code, name, lst in cats:
    add(divs[code])
    km = os.path.join(os.path.dirname(OUT), "_catmap_%s%s.pdf" % (code, CATMAP_SUFFIX))   # W8: the key plan built by make_catmaps.py
    if not os.path.exists(km): sys.exit("missing key plan page %s: run make_catmaps.py first" % km)
    if add(km) != 1: sys.exit("%s: the key plan must be one page" % km)
    for ch in lst:
        n = add(os.path.join(OUT_PDF, "Combined", ch + ".pdf")); expect = 1 + len(compute_view_frames(ch)[1])
        if n != expect: sys.exit("%s: combined PDF has %d pages, expected %d (key map + sheets); rebuild it with export_pdf.py" % (ch, n, expect))
with out.open_outline() as ol:
    ol.root.append(pikepdf.OutlineItem("Cover", 0)); ol.root.append(pikepdf.OutlineItem("Table of drawings", 1))
    for code, name, lst in cats:
        item = pikepdf.OutlineItem(name, pages[code] - 1)
        item.children.append(pikepdf.OutlineItem("Key plan of the catchment", pages[code]))
        for ch in lst:
            sub = pikepdf.OutlineItem(ch, pages[ch] - 1); n = len(compute_view_frames(ch)[1])
            sub.children.append(pikepdf.OutlineItem("%s  Key map" % nums[(ch, "km")], pages[ch] - 1))
            for i in range(1, n + 1): sub.children.append(pikepdf.OutlineItem("%s  Sheet %d of %d" % (nums[(ch, i)], i, n), pages[ch] + i - 1))
            item.children.append(sub)
        ol.root.append(item)
out.docinfo["/Title"] = "%s %s %s" % (DOC_NO_PREFIX, " ".join(TITLE).title(), BASIS); out.docinfo["/Author"] = CONSULTANT[0].title()
out.save(OUT); [k.close() for k in keep]
for f in [front] + list(divs.values()): os.remove(f)
with open(OUT[:-4] + "_contents.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["dwg", "cat", "ch", "drawing", "s0", "s1", "page"]); w.writeheader(); [w.writerow(r) for r in rows]
print("set: %s  (%d pages, %.0f MB)" % (OUT, len(out.pages), os.path.getsize(OUT) / 1e6))
