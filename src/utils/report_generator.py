import markdown
import pdfkit

def generate_html_report(md_text: str) -> str:
    return markdown.markdown(md_text)

def generate_pdf_report(md_text: str, output_path="report.pdf") -> None:
    html = markdown.markdown(md_text)
    pdfkit.from_string(html, output_path)