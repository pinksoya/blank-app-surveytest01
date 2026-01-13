import io
import streamlit as st
from pypdf import PdfReader, PdfWriter


st.set_page_config(page_title="PDF 페이지 추출기")
st.title("PDF 페이지 추출기")

st.write("")

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
					# pypdf uses 0-based page indices
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

st.info("PDF파일을 업로드 한 뒤, 원하는 페이지를 선택하면 선택된 페이지가 추출되어 PDF로 저장됩니다")
st.link_button("@코딩튜터 블로그", 'https://blog.naver.com/pinksoya')