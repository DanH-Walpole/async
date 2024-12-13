import PyPDF2
import pdfminer
import pdfplumber
import pymupdf
from io import BytesIO
from typing import List

class DocumentHandler:
    def __init__(self):
        self.provider = "PyPDF2"

    def convert_pdf_to_text(self, pdf_content: bytes) -> str:
        if self.provider == "PyPDF2":
            return self.convert_with_pypdf2(pdf_content)
        elif self.provider == "pdfminer":
            return self.convert_with_pdfminer(pdf_content)
        elif self.provider == "pdfplumber":
            return self.convert_with_pdfplumber(pdf_content)
        elif self.provider == "PyMuPDF":
            return self.convert_with_pymupdf(pdf_content)
        else:
            raise ValueError(f"Unknown PDF provider: {self.provider}")

    # Provider implementations
    def convert_with_pypdf2(self, pdf_content: bytes) -> str:
        pdf_file = BytesIO(pdf_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    def convert_with_pdfminer(self, pdf_content: bytes) -> str:
        from pdfminer.high_level import extract_text
        pdf_file = BytesIO(pdf_content)
        text = extract_text(pdf_file)
        return text

    def convert_with_pdfplumber(self, pdf_content: bytes) -> str:
        pdf_file = BytesIO(pdf_content)
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text

    def convert_with_pymupdf(self, pdf_content: bytes) -> str:
        pdf_file = BytesIO(pdf_content)
        doc = pymupdf.open(pdf_file)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text