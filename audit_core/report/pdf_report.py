"""
PDF report generator. Renders the audit_input's check results into a
structured document: summary -> per-category sections (only categories
with FLAG/FAIL are meaningfully expanded; PASS entries are counted but
not detailed to keep the report scannable).
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)

STATUS_COLORS = {
    "FAIL": colors.HexColor("#B3261E"),
    "FLAG": colors.HexColor("#B8860B"),
    "PASS": colors.HexColor("#2E7D32"),
}

CATEGORY_ORDER = [
    ("arithmetic", "Arithmetic Reconciliation"),
    ("statistics", "Statistical Validity"),
    ("consistency", "Cross-Section Consistency"),
    ("independence", "Independence / Overlap"),
    ("definitions", "Definition Drift"),
    ("formulas", "Formula / Scoring Sanity"),
]


def _category_of(check_name):
    return check_name.split(".")[0]


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="AuditTitle", fontSize=20, leading=24,
                               spaceAfter=6, textColor=colors.HexColor("#1a1a1a")))
    styles.add(ParagraphStyle(name="SectionHeading", fontSize=14, leading=18,
                               spaceBefore=16, spaceAfter=8,
                               textColor=colors.HexColor("#1a1a1a")))
    styles.add(ParagraphStyle(name="IssueTitle", fontSize=10.5, leading=13,
                               spaceBefore=8, spaceAfter=2, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="IssueBody", fontSize=9.5, leading=13,
                               spaceAfter=2, textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle(name="Evidence", fontSize=8.5, leading=11,
                               fontName="Courier", textColor=colors.HexColor("#444444"),
                               backColor=colors.HexColor("#f5f5f5"), spaceAfter=6))
    return styles


def _summary_table(summary, styles):
    data = [["Status", "Count"]]
    for status in ("FAIL", "FLAG", "PASS"):
        data.append([status, str(summary.get(status, 0))])
    t = Table(data, colWidths=[2 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TEXTCOLOR", (0, 1), (0, 1), STATUS_COLORS["FAIL"]),
        ("TEXTCOLOR", (0, 2), (0, 2), STATUS_COLORS["FLAG"]),
        ("TEXTCOLOR", (0, 3), (0, 3), STATUS_COLORS["PASS"]),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _format_evidence(evidence):
    lines = []
    for k, v in evidence.items():
        lines.append(f"{k}: {v}")
    return "<br/>".join(lines)


def generate_pdf(report, output_path):
    styles = _build_styles()
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                             topMargin=0.75 * inch, bottomMargin=0.75 * inch,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    story = []

    story.append(Paragraph("Numerical Audit Report", styles["AuditTitle"]))
    story.append(Paragraph(report["document_title"], styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This report flags numerical, statistical, and internal-consistency issues. "
        "It does not correct values — every item below requires manual verification "
        "and, where applicable, a decision by the author.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))
    story.append(_summary_table(report["summary"], styles))
    story.append(PageBreak())

    results_by_category = {}
    for r in report["results"]:
        cat = _category_of(r["check"])
        results_by_category.setdefault(cat, []).append(r)

    for cat_key, cat_title in CATEGORY_ORDER:
        items = results_by_category.get(cat_key, [])
        if not items:
            continue
        flagged = [r for r in items if r["status"] != "PASS"]
        passed = [r for r in items if r["status"] == "PASS"]

        story.append(Paragraph(cat_title, styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#cccccc")))
        story.append(Paragraph(
            f"{len(flagged)} flagged, {len(passed)} passed.", styles["Normal"]
        ))

        for r in flagged:
            color = STATUS_COLORS.get(r["status"], colors.black)
            story.append(Paragraph(
                f'<font color="{color.hexval()}">[{r["status"]}]</font> {r["issue"]}',
                styles["IssueTitle"]
            ))
            story.append(Paragraph(f"Location: {r['location']}", styles["IssueBody"]))
            if r.get("evidence"):
                story.append(Paragraph(_format_evidence(r["evidence"]), styles["Evidence"]))
            if r.get("suggested_direction"):
                story.append(Paragraph(
                    f"<i>Suggested direction:</i> {r['suggested_direction']}",
                    styles["IssueBody"]
                ))
        story.append(Spacer(1, 10))

    doc.build(story)
    return output_path
