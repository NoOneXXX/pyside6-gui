import base64
import os
from urllib.parse import unquote
import fitz
from docx import Document
from ebooklib import epub
from bs4 import BeautifulSoup
from .read_pdf_epud_txt_word_type.read_epud import read_epud_to_richtext

def load_file(file_path, text_widget):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text_widget.setPlainText(f.read())

    elif ext == '.docx':
        doc = Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        text_widget.setPlainText(full_text)

    elif ext == '.pdf':
        doc = fitz.open(file_path)
        content = ""
        for page in doc:
            content += page.get_text() + "\n"
        text_widget.setPlainText(content)

    elif ext == '.epub':
        # 直接的调用封装的类
        read_epud = read_epud_to_richtext(file_path, text_widget)
        read_epud.read_epud_context()
