import io
from datetime import datetime

from fpdf import FPDF


def analysis_to_pdf(analysis: dict, resume: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Resume Analysis Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Candidate Information", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"Name: {resume.get('candidate_name') or 'Unknown'}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Current Role: {resume.get('current_role') or 'N/A'}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Filename: {resume.get('filename') or 'N/A'}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    scores = [
        ("Overall Score", analysis.get("overall_score")),
        ("ATS Score", analysis.get("ats_score")),
        ("Skills Score", analysis.get("skills_score")),
        ("Experience Score", analysis.get("experience_score")),
        ("Education Score", analysis.get("education_score")),
        ("Formatting Score", analysis.get("formatting_score")),
    ]

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Scores (out of 100)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for label, score in scores:
        val = f"{score:.0f}" if score is not None else "N/A"
        pdf.cell(0, 6, f"{label}: {val}/100", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    sections = [
        ("Summary", analysis.get("summary")),
        ("Strengths", analysis.get("strengths")),
        ("Weaknesses", analysis.get("weaknesses")),
        ("Suggestions", analysis.get("suggestions")),
        ("Missing Keywords", analysis.get("missing_keywords")),
        ("Matched Keywords", analysis.get("matched_keywords")),
    ]

    for label, value in sections:
        if not value:
            continue
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        if isinstance(value, list):
            for item in value:
                pdf.multi_cell(0, 5, f"  - {item}")
        else:
            pdf.multi_cell(0, 5, str(value))
        pdf.ln(3)

    return pdf.output()
