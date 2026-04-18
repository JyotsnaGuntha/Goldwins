"""
BOM Export Functions
PDF and Excel export functionality for BOM and technical reports.
"""

import io
import datetime
import tempfile
import os
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from .generator import generate_bom_items


class NumberedCanvas(canvas.Canvas):
    """PDF Canvas with page numbering and footer."""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def draw_footer(self, page_count):
        """Draw footer with logo, date, and page numbers."""
        self.saveState()
        logo_path = "Kirloskar Oil Engine Logo.png"
        logo_w, logo_h = 100, 35
        try:
            self.drawImage(logo_path, A4[0] - 45 - logo_w, A4[1] - 30 - logo_h,
                          width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
        
        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(45, 50, A4[0] - 45, 50)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(45, 35, "Kirloskar Oil Engines Ltd.")
        now = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
        self.drawCentredString(A4[0] / 2.0, 35, f"Report Generated: {now}")
        pg = self.getPageNumber()
        self.drawRightString(A4[0] - 45, 35, f"Page {pg} of {page_count}")
        self.restoreState()


class GACanvas(canvas.Canvas):
    """PDF Canvas for GA drawing with custom footer."""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def _draw_footer(self, page_count):
        """Draw footer for GA PDF."""
        self.saveState()
        page_size = landscape(A4)
        logo_path = "Kirloskar Oil Engine Logo.png"
        try:
            self.drawImage(logo_path, page_size[0] - 40 - 90, page_size[1] - 25 - 32,
                          width=90, height=32, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
        
        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(30, 45, page_size[0] - 30, 45)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(30, 32, "Kirloskar Oil Engines Ltd.")
        now = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
        self.drawCentredString(page_size[0] / 2.0, 32, f"Report Generated: {now}")
        self.drawRightString(page_size[0] - 30, 32, f"Page {self.getPageNumber()} of {page_count}")
        self.restoreState()


def generate_pdf_report(
    sld_svg,
    sld_svg_width,
    sld_svg_height,
    ga_svg_str,
    ga_svg_w,
    ga_svg_h,
    incomer_list,
    mccb_outputs,
    bom_items,
    solar_kw,
    grid_kw,
    num_dg,
    num_outputs,
    total_busbar_current,
    total_outgoing_rating,
    busbar_spec,
    panel_w,
    panel_h,
    panel_d,
    num_poles,
    warning_flag=False,
):
    """
    Generate main technical report PDF with SLD, BOM, and specifications.
    
    Returns:
        BytesIO buffer with PDF data
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40,
                           topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = styles["Title"]
    title_style.fontSize = 22
    title_style.textColor = colors.HexColor("#c37c5a")
    title_style.alignment = 1
    
    h2_style = styles["Heading2"]
    h2_style.fontSize = 16
    h2_style.textColor = colors.HexColor("#19988b")
    h2_style.spaceBefore = 12
    h2_style.spaceAfter = 8
    
    normal_style = styles["Normal"]
    normal_style.fontSize = 10
    normal_style.leading = 13
    normal_style.alignment = 4
    
    story = []
    story.append(Paragraph("Microgrid Panel Technical Report", title_style))
    story.append(Spacer(1, 8))
    
    # System Overview
    story.append(Paragraph("1. System Overview", h2_style))
    grid_txt = f"<b>{grid_kw} kW</b> Grid supply, " if grid_kw > 0 else ""
    solar_txt = f"and <b>{solar_kw} kWp</b> Solar PV" if solar_kw > 0 else ""
    story.append(Paragraph(
        f"This report details the configuration and material requirements for a customized Microgrid Panel. "
        f"The system handles <b>{int(num_dg)} DG(s)</b>, {grid_txt}{solar_txt}. "
        f"Managed via a centralized Microgrid Controller (MGC).", normal_style))
    story.append(Spacer(1, 8))
    
    # System Specifications
    story.append(Paragraph("2. System Specifications", h2_style))
    specs = (
        f"<b>Total Busbar Current Rating:</b> {total_busbar_current:.2f}A<br/>"
        f"<b>Total Outgoing Capacity:</b> {total_outgoing_rating:.0f}A<br/>"
        f"<b>Recommended Busbar:</b> {busbar_spec}<br/>"
        f"<b>Panel Dimensions (Computed):</b> {panel_w}W × {panel_h}H × {panel_d}D mm<br/>"
        f"<b>System Configuration:</b> {int(3)}-Phase, {int(num_outputs)} Outgoing Feeders<br/>"
    )
    if warning_flag:
        specs += "<br/><font color='red'><b>WARNING:</b> Total busbar current exceeds total outgoing rating. Review configuration.</font>"
    story.append(Paragraph(specs, normal_style))
    story.append(Spacer(1, 8))
    
    # SLD Section
    story.append(Paragraph("3. Single Line Diagram (SLD)", h2_style))
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
        f.write(sld_svg)
        temp_sld = f.name
    
    try:
        drawing = svg2rlg(temp_sld)
        if drawing:
            scale = 505.0 / sld_svg_width
            drawing.scale(scale, scale)
            drawing.width = sld_svg_width * scale
            drawing.height = sld_svg_height * scale
            sld_table = Table([[drawing]], colWidths=[505])
            sld_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(sld_table)
    except Exception as e:
        story.append(Paragraph(f"[Error rendering SLD: {e}]", normal_style))
    finally:
        try:
            os.unlink(temp_sld)
        except:
            pass
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Diagram illustrates electrical topology and power flow.</i>", normal_style))
    story.append(Spacer(1, 20))
    
    # GA Section
    story.append(Paragraph("4. General Arrangement (GA) Drawing", h2_style))
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
        f.write(ga_svg_str)
        temp_ga = f.name
    
    try:
        ga_rlg = svg2rlg(temp_ga)
        if ga_rlg:
            scale_ga = 505.0 / ga_svg_w
            ga_rlg.scale(scale_ga, scale_ga)
            ga_rlg.width = ga_svg_w * scale_ga
            ga_rlg.height = ga_svg_h * scale_ga
            ga_table = Table([[ga_rlg]], colWidths=[505])
            ga_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(ga_table)
    except Exception as e:
        story.append(Paragraph(f"[Error rendering GA: {e}]", normal_style))
    finally:
        try:
            os.unlink(temp_ga)
        except:
            pass
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Internal layout and dimensional overview.</i>", normal_style))
    story.append(Spacer(1, 15))
    
    # MCCB Schedule
    story.append(Paragraph("4.1 MCCB Schedule (from Database)", h2_style))
    sched_data = [["Tag", "Description", "Rating (A)", "Poles", "H × W × D (mm)", "Frame"]]
    from ..utils import get_mccb_dims
    for i, r in enumerate(incomer_list):
        d = get_mccb_dims(r, {})
        sched_data.append([f"I/C {i+1}", "Incomer MCCB", f"{r}A", "3P",
                          f"{d['h']}×{d['w']}×{d['d']}", d['frame']])
    for i, r in enumerate(mccb_outputs):
        d = get_mccb_dims(r, {})
        sched_data.append([f"O/G {i+1}", "Outgoing MCCB", f"{r}A", "3P",
                          f"{d['h']}×{d['w']}×{d['d']}", d['frame']])
    
    sched_table = Table(sched_data, colWidths=[40, 130, 60, 40, 115, 120])
    sched_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#19988b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(sched_table)
    story.append(PageBreak())
    
    # BOM Section
    story.append(Paragraph("5. Bill Of Material (BOM)", h2_style))
    story.append(Spacer(1, 8))
    
    table_data = [["Sr", "Component / Description", "Rating", "Qty", "UOM"]]
    for i, item in enumerate(bom_items, 1):
        table_data.append([str(i), item.description, item.rating, str(item.qty), item.uom])
    
    table = Table(table_data, colWidths=[25, 305, 75, 55, 55])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#19988b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    
    # Notes
    story.append(Paragraph("6. Notes & Remarks", h2_style))
    story.append(Paragraph(
        "• This BOM is subject to final design review.<br/>"
        "• All MCCB ratings include a 1.25× safety factor.<br/>"
        "• Busbar sizing considers thermal conductivity and current density limits.<br/>"
        "• Panel dimensions are computed dynamically from MCCB database.<br/>"
        "• All components per relevant Indian Standards and IEC guidelines.", normal_style))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


def generate_ga_pdf(ga_svg_str, ga_svg_w, ga_svg_h, incomer_list, mccb_outputs, panel_w, panel_h, panel_d, num_poles):
    """
    Generate standalone GA drawing PDF (landscape).
    
    Returns:
        BytesIO buffer with PDF data
    """
    buffer = io.BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=page_size,
                           rightMargin=30, leftMargin=30, topMargin=35, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = styles["Title"]
    title_style.fontSize = 18
    title_style.textColor = colors.HexColor("#c37c5a")
    title_style.alignment = 1
    
    h2_style = styles["Heading2"]
    h2_style.fontSize = 13
    h2_style.textColor = colors.HexColor("#19988b")
    
    normal_style = styles["Normal"]
    normal_style.fontSize = 9
    normal_style.leading = 12
    
    story = []
    story.append(Paragraph("Microgrid Panel — Internal General Arrangement (GA)", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<b>Panel Dimensions (Computed):</b> {panel_w}W × {panel_h}H × {panel_d}D mm", normal_style))
    story.append(Spacer(1, 8))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
        f.write(ga_svg_str)
        temp_ga = f.name
    
    try:
        ga_drw = svg2rlg(temp_ga)
        if ga_drw:
            avail_w = page_size[0] - 60
            avail_h = page_size[1] - 160
            scale_g = min(avail_w / ga_svg_w, avail_h / ga_svg_h)
            ga_drw.scale(scale_g, scale_g)
            ga_drw.width = ga_svg_w * scale_g
            ga_drw.height = ga_svg_h * scale_g
            ga_table = Table([[ga_drw]], colWidths=[avail_w])
            ga_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(ga_table)
    except Exception as e:
        story.append(Paragraph(f"[Error rendering GA: {e}]", normal_style))
    finally:
        try:
            os.unlink(temp_ga)
        except:
            pass
    
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<i>{len(incomer_list)} incomer(s) | {len(mccb_outputs)} outgoing feeder(s). "
        f"All dimensions in mm.</i>", normal_style))
    
    # MCCB Schedule
    story.append(Spacer(1, 8))
    story.append(Paragraph("MCCB Schedule (from Database)", h2_style))
    sched_data = [["Tag", "Description", "Rating (A)", "Poles", "H × W × D (mm)", "Frame"]]
    from ..utils import get_mccb_dims
    for i, r in enumerate(incomer_list):
        d = get_mccb_dims(r, {})
        sched_data.append([f"I/C {i+1}", "Incomer MCCB", f"{r}A", f"{num_poles}P",
                          f"{d['h']}×{d['w']}×{d['d']}", d['frame']])
    for i, r in enumerate(mccb_outputs):
        d = get_mccb_dims(r, {})
        sched_data.append([f"O/G {i+1}", "Outgoing MCCB", f"{r}A", f"{num_poles}P",
                          f"{d['h']}×{d['w']}×{d['d']}", d['frame']])
    
    sched_table = Table(sched_data, colWidths=[50, 130, 70, 45, 120, 90])
    sched_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#19988b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(sched_table)
    
    doc.build(story, canvasmaker=GACanvas)
    buffer.seek(0)
    return buffer


def generate_excel_bom(bom_items):
    """
    Generate BOM as Excel file.
    
    Args:
        bom_items: List of BOMItem objects
    
    Returns:
        bytes of Excel file
    """
    bom_dicts = []
    for i, item in enumerate(bom_items, 1):
        d = item.to_dict()
        d["Sr No"] = i
        bom_dicts.append(d)
    
    df = pd.DataFrame(bom_dicts)
    # Reorder columns
    if "Sr No" in df.columns:
        cols = ["Sr No"] + [c for c in df.columns if c != "Sr No"]
        df = df[cols]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="BOM")
    output.seek(0)
    return output.getvalue()
