import pymupdf
import base64

def extract_pages(file_bytes: bytes) -> list[dict]:
    """
    Returns: [{"page_num": 0, "image_bytes": b"...(PNG)", "text": "..."}]
    
    - Opens PDF from memory
    - Renders at 150 DPI for Gemini Vision
    - Extracts text layer if available
    """
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    mat = pymupdf.Matrix(150/72, 150/72)  # 150 DPI
    pages = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        pages.append({
            "page_num": i,
            "image_bytes": pix.tobytes("png"),
            "text": page.get_text().strip()
        })
    doc.close()
    return pages

def to_base64(image_bytes: bytes) -> str:
    """Encode PNG bytes to base64 for LLM prompts."""
    return base64.b64encode(image_bytes).decode("utf-8")
