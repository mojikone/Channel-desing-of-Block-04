"""Report-grade styling for native Excel charts built with openpyxl (one look for every W3 workbook).
Light hairline gridlines, light grey axes, Arial 9 pt labels, 11 pt bold title, no chart border, no rounded corners."""
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties, Font as DFont

GRID, AXIS, INK, MUTED = "EDEDED", "BFBFBF", "404040", "595959"

def _rich(size, bold=False, colour=INK):
    cp = CharacterProperties(sz=size, b=bold, solidFill=colour, latin=DFont(typeface="Arial"))
    return RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp)])

def _title_font(title, size, bold, colour):
    try:
        for p in title.tx.rich.p:
            cp = CharacterProperties(sz=size, b=bold, solidFill=colour, latin=DFont(typeface="Arial"))
            p.pPr = ParagraphProperties(defRPr=cp)
            for r in (p.r or []): r.rPr = cp
    except AttributeError:
        pass

def style_chart(ch, grid_y=True, grid_x=False, label_size=900, title_size=1100):
    """Apply the W3 chart style in place. Call after the title, axes and legend are set."""
    ch.style = 2
    try: ch.roundedCorners = False
    except Exception: pass
    ch.graphical_properties = GraphicalProperties(ln=LineProperties(noFill=True))          # no chart border
    ch.plot_area.graphicalProperties = GraphicalProperties(noFill=True, ln=LineProperties(noFill=True))
    for ax, grid in ((ch.y_axis, grid_y), (ch.x_axis, grid_x)):
        ax.spPr = GraphicalProperties(ln=LineProperties(solidFill=AXIS, w=9525))              # 0.75 pt axis line
        ax.txPr = _rich(label_size, colour=MUTED)
        if grid:
            from openpyxl.chart.axis import ChartLines
            ax.majorGridlines = ChartLines(spPr=GraphicalProperties(ln=LineProperties(solidFill=GRID, w=6350)))   # 0.5 pt hairline
        else:
            ax.majorGridlines = None
        ax.minorGridlines = None
        if ax.title is not None: _title_font(ax.title, label_size, False, MUTED)
    if ch.title is not None:
        ch.title.overlay = False; _title_font(ch.title, title_size, True, INK)
    if ch.legend is not None:
        ch.legend.overlay = False; ch.legend.txPr = _rich(label_size, colour=MUTED)
        ch.legend.graphicalProperties = GraphicalProperties(noFill=True, ln=LineProperties(noFill=True))
    return ch
