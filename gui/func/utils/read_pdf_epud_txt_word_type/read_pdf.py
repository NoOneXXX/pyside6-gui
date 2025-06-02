
'''
这个是为了后期好维护
'''
import os
import shutil
import sys
from urllib.parse import quote

from PySide6.QtCore import QUrl, QCoreApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

class PDFPreviewer:
    def __init__(self):
        # 判断是否为打包运行
        if getattr(sys, 'frozen', False):
            # 打包后，获取 .exe 所在目录
            base_dir = QCoreApplication.applicationDirPath()
        else:
            # 开发阶段，获取当前文件所在目录
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        # 拼接路径
        self.viewer_dir = os.path.join(base_dir, "pdfjs", "web")
        self.viewer_html = os.path.join(self.viewer_dir, "viewer.html")

        self.pdf_output_dir = os.path.join(base_dir, "pdfjs", "pdfs")
        os.makedirs(self.pdf_output_dir, exist_ok=True)


    def get_webview(self, pdf_file_path: str) -> QWebEngineView:
        target_pdf_name = os.path.basename(pdf_file_path)
        target_pdf_path = os.path.join(self.pdf_output_dir, target_pdf_name)

        if not os.path.exists(target_pdf_path):
            shutil.copy(pdf_file_path, target_pdf_path)

        encoded_pdf_name = quote(target_pdf_name)
        viewer_url = QUrl.fromLocalFile(self.viewer_html).toString()
        final_url = f"{viewer_url}?file=../pdfs/{encoded_pdf_name}"

        print("[PDFPreviewer] Loading URL:", final_url)

        webview = QWebEngineView()
        webview.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        webview.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        webview.load(QUrl(final_url))
        return webview
