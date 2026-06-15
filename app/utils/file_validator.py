import io

PDF_MAGIC = b"%PDF"
DOCX_MAGIC = b"PK\x03\x04"
TXT_MAGIC = None


def detect_file_type(data: bytes) -> str:
    if data.startswith(PDF_MAGIC):
        return "pdf"
    if data.startswith(DOCX_MAGIC):
        return "docx"
    try:
        data.decode("utf-8")
        return "txt"
    except UnicodeDecodeError:
        try:
            data.decode("latin-1")
            return "txt"
        except UnicodeDecodeError:
            return "unknown"


def validate_file(data: bytes, filename: str) -> tuple[bool, str]:
    detected = detect_file_type(data)
    if detected == "unknown":
        return False, "Unrecognized file format. Supported: PDF, DOCX, TXT."
    ext = (filename or "").lower()
    ext_map = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}
    expected = None
    for suffix, ftype in ext_map.items():
        if ext.endswith(suffix):
            expected = ftype
            break
    if expected and detected != expected:
        return False, f"File extension '.{expected}' does not match actual content type '{detected}'."
    return True, detected


def extract_text_from_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
