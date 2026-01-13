
import io
import os
import tempfile
import streamlit as st
from pypdf import PdfReader, PdfWriter


st.set_page_config(page_title="PDF 도구")
st.title("PDF 편집기")


def create_pdf_from_text(text: str, font_path: str | None = None) -> bytes:
    # Local import to avoid hard dependency on import error at module load
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    # Try to register provided font (TTF/OTF) for Korean support
    font_name = "Helvetica"
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("UserFont", font_path))
            font_name = "UserFont"
        except Exception:
            font_name = "Helvetica"

    style = ParagraphStyle(
        name="Normal",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=12,
        leading=15,
        alignment=TA_LEFT,
    )

    flow = []
    for para in text.split("\n\n"):
        flow.append(Paragraph(para.replace("\n", "<br/>"), style))
        flow.append(Spacer(1, 6))

    doc.build(flow)
    return buf.getvalue()


def auto_find_korean_font() -> str | None:
    # Common font locations on Debian-like systems
    paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
        "/usr/share/fonts/truetype/unfonts-core/UnBatang.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def _write_temp_font(font_upload) -> str:
    # Writes uploaded font bytes to a temporary file and returns path
    tmp = tempfile.NamedTemporaryFile(suffix=os.path.splitext(font_upload.name)[1], delete=False)
    tmp.write(font_upload.read())
    tmp.flush()
    tmp.close()
    return tmp.name


def convert_to_pdf(uploaded_file, font_path: str | None = None) -> bytes:
    name = uploaded_file.name if hasattr(uploaded_file, "name") else "file"
    ext = name.split(".")[-1].lower()
    data = uploaded_file.read()

    # PDF passthrough
    if ext == "pdf":
        return data

    # Image -> PDF via Pillow
    if ext in ["png", "jpg", "jpeg", "bmp", "gif", "tiff"]:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        out = io.BytesIO()
        img.save(out, format="PDF")
        return out.getvalue()

    # Plain text
    if ext in ["txt", "md"]:
        text = data.decode("utf-8", errors="replace")
        return create_pdf_from_text(text, font_path=font_path)

    # docx -> extract text then create PDF
    if ext == "docx":
        from docx import Document

        doc = Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs]
        text = "\n\n".join(paragraphs)
        return create_pdf_from_text(text, font_path=font_path)

    raise ValueError(f"지원하지 않는 파일 형식: {ext}")


st.header("#1. PDF 페이지 추출기")
uploaded = st.file_uploader("PDF 파일 업로드", type=["pdf"])

if uploaded is not None:
    try:
        pdf_bytes = uploaded.read()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        num_pages = len(reader.pages)
        st.write(f"페이지 수: {num_pages}")

        pages = st.multiselect(
            "추출할 페이지 선택 (1부터 시작)",
            options=list(range(1, num_pages + 1)),
            default=[],
        )

        if st.button("선택한 페이지 추출"):
            if not pages:
                st.warning("적어도 한 페이지를 선택하세요.")
            else:
                writer = PdfWriter()
                for p in pages:
                    writer.add_page(reader.pages[p - 1])

                out = io.BytesIO()
                writer.write(out)
                out.seek(0)

                st.download_button(
                    label="다운로드: 선택한 페이지 PDF",
                    data=out.getvalue(),
                    file_name="extracted_pages.pdf",
                    mime="application/pdf",
                )

    except Exception as e:
        st.error(f"PDF 처리 중 오류가 발생했습니다: {e}")

st.warning("PDF파일을 업로드 한 뒤, 원하는 페이지를 선택하면 선택된 페이지가 추출되어 PDF로 저장됩니다")

st.markdown("---")  


st.header("#2. 두개의 파일을 하나의 PDF로 합치기")
st.write("")
st.write("")

file1 = st.file_uploader("파일 1 업로드", type=["pdf", "png", "jpg", "jpeg", "bmp", "gif", "tiff", "txt", "md", "docx"], key="f1")
file2 = st.file_uploader("파일 2 업로드", type=["pdf", "png", "jpg", "jpeg", "bmp", "gif", "tiff", "txt", "md", "docx"], key="f2")

if st.button("합쳐서 PDF 만들기"):
    if not file1 or not file2:
        st.warning("두 파일을 모두 업로드하세요.")
    else:
        try:
            pdf1 = convert_to_pdf(file1)
            pdf2 = convert_to_pdf(file2)

            reader1 = PdfReader(io.BytesIO(pdf1))
            reader2 = PdfReader(io.BytesIO(pdf2))

            writer = PdfWriter()
            for p in reader1.pages:
                writer.add_page(p)
            for p in reader2.pages:
                writer.add_page(p)

            out = io.BytesIO()
            writer.write(out)
            out.seek(0)

            st.download_button(
                label="다운로드: 합쳐진 파일",
                data=out.getvalue(),
                file_name="merged.pdf",
                mime="application/pdf",
            )

        except Exception as e:
            st.error(f"파일 변환/병합 중 오류가 발생했습니다: {e}")

st.warning("두 개의 파일을 하나의 PDF로 만들어 주는 기능입니다.  \n 텍스트문서나 워드를 바로 업로드 하면 한글폰트가 깨질 수 있으니 pdf로 변환 후 업로드 하세요")
st.link_button("@코딩튜터 블로그", 'https://blog.naver.com/pinksoya')