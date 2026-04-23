"""
Markdown 编辑器组件
==================

支持编辑和预览两种模式的 Markdown 编辑器。
使用 markdown_renderer 模块进行渲染。

特性：
- 编辑/预览/分屏三种模式
- 语法高亮（编辑器）
- 图片粘贴支持
- PDF 导出
"""

import os
import time
import shutil
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QTextEdit, QMenu, QMessageBox, QFileDialog, QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QStackedWidget, QFrame, QPlainTextEdit, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtGui import (
    QImage, QClipboard, QAction, QTextCharFormat,
    QFont, QCursor, QIcon, QKeySequence, QColor,
    QSyntaxHighlighter
)
from PySide6.QtCore import (
    QUrl, Qt, Signal, QRegularExpression, QTimer, QObject, Slot
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from gui.data.NoteDB import NoteDB
from gui.func.utils import logger
from gui.func.right_bottom_corner.MarkdownRenderer import render_markdown


class CopyHandler(QObject):
    """处理 WebView 中的复制操作"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    @Slot(str)
    def copyText(self, text):
        """复制文本到剪贴板"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            print(f"[CopyHandler] 已复制 {len(text)} 字符到剪贴板")
        except Exception as e:
            logger.error(f"复制失败: {e}")


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown 语法高亮器 - 用于编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # 标题 # ## ###
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#2E7D32"))
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'^#{1,6}\s.*'), header_format))
        
        # 粗体 **text**
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#D32F2F"))
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\*\*[^*]+\*\*'), bold_format))
        self.highlighting_rules.append((QRegularExpression(r'__[^_]+__'), bold_format))
        
        # 斜体 *text*
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#F57C00"))
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r'\*[^*]+\*'), italic_format))
        self.highlighting_rules.append((QRegularExpression(r'_[^_]+_'), italic_format))
        
        # 行内代码 `code`
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#1976D2"))
        code_format.setBackground(QColor("#F5F5F5"))
        code_format.setFontFamily("Consolas, Monaco, monospace")
        self.highlighting_rules.append((QRegularExpression(r'`[^`]+`'), code_format))
        
        # 代码块 ```code```
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#1976D2"))
        code_block_format.setBackground(QColor("#F5F5F5"))
        code_block_format.setFontFamily("Consolas, Monaco, monospace")
        self.highlighting_rules.append((QRegularExpression(r'^```.*$'), code_block_format))
        
        # 链接 [text](url)
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#7B1FA2"))
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((QRegularExpression(r'\[([^\]]+)\]\(([^)]+)\)'), link_format))
        
        # 图片 ![alt](url)
        image_format = QTextCharFormat()
        image_format.setForeground(QColor("#00796B"))
        self.highlighting_rules.append((QRegularExpression(r'!\[([^\]]*)\]\(([^)]+)\)'), image_format))
        
        # 引用 >
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#5D4037"))
        quote_format.setBackground(QColor("#FFF8E1"))
        self.highlighting_rules.append((QRegularExpression(r'^>\s.*'), quote_format))
        
        # 列表 - * +
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#C62828"))
        self.highlighting_rules.append((QRegularExpression(r'^\s*[-*+]\s'), list_format))
        
        # 数字列表 1. 2.
        num_list_format = QTextCharFormat()
        num_list_format.setForeground(QColor("#C62828"))
        self.highlighting_rules.append((QRegularExpression(r'^\s*\d+\.\s'), num_list_format))
        
        # 分隔线 ---
        hr_format = QTextCharFormat()
        hr_format.setForeground(QColor("#9E9E9E"))
        hr_format.setBackground(QColor("#EEEEEE"))
        self.highlighting_rules.append((QRegularExpression(r'^-{3,}$'), hr_format))
        self.highlighting_rules.append((QRegularExpression(r'^\*{3,}$'), hr_format))
        
        # HTML 标签
        html_format = QTextCharFormat()
        html_format.setForeground(QColor("#E91E63"))
        self.highlighting_rules.append((QRegularExpression(r'<[^>]+>'), html_format))
    
    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class MarkdownEditor(QWidget):
    """
    Markdown 编辑器组件
    支持编辑、预览和分屏三种模式
    """
    
    content_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.md_file_path = None
        self._is_preview_mode = False
        self._split_preview_initialized = False
        self._preview_update_timer = QTimer(self)
        self._preview_update_timer.setSingleShot(True)
        self._preview_update_timer.timeout.connect(self._do_update_split_preview)

        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部工具栏
        toolbar = QFrame()
        toolbar.setFixedHeight(45)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 0, 12, 0)
        toolbar_layout.setSpacing(8)
        
        # 模式切换按钮
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setChecked(True)
        self.edit_btn.setStyleSheet(self._get_toolbar_btn_style(False))
        
        self.preview_btn = QPushButton("预览")
        self.preview_btn.setCheckable(True)
        self.preview_btn.setStyleSheet(self._get_toolbar_btn_style(False))
        
        self.split_btn = QPushButton("分屏")
        self.split_btn.setCheckable(True)
        self.split_btn.setStyleSheet(self._get_toolbar_btn_style(True))
        
        toolbar_layout.addWidget(self.edit_btn)
        toolbar_layout.addWidget(self.preview_btn)
        toolbar_layout.addWidget(self.split_btn)

        toolbar_layout.addStretch()

        # 文件路径标签
        self.path_label = QLabel("未保存")
        self.path_label.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 12px;
                font-family: 'Microsoft YaHei UI', sans-serif;
            }
        """)
        toolbar_layout.addWidget(self.path_label)
        
        layout.addWidget(toolbar)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        
        # 编辑模式
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background-color: #FFFFFF;
                font-family: 'Consolas', 'Microsoft YaHei Mono', 'Monaco', monospace;
                font-size: 14px;
                line-height: 1.6;
                padding: 16px;
                color: #1E293B;
            }
            QPlainTextEdit:focus {
                outline: none;
            }
        """)
        self.editor.setPlaceholderText("在此输入 Markdown 内容...\n\n支持标准 Markdown 语法：\n# 标题\n**粗体**\n*斜体*\n[链接](url)\n![图片](url)\n- 列表项")
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        self.editor.installEventFilter(self)
        
        # 添加语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 预览模式
        self.preview = QWebEngineView()
        self.preview.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #1e1e2e;
            }
        """)
        # 设置 QWebChannel 支持复制功能
        self._setup_web_channel(self.preview)
        QTimer.singleShot(0, lambda: self.preview.setHtml("<html><body style='background-color:#1e1e2e;'></body></html>"))
        
        # 分屏模式
        self.split_editor = QPlainTextEdit()
        self.split_editor.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background-color: #FFFFFF;
                font-family: 'Consolas', 'Microsoft YaHei Mono', 'Monaco', monospace;
                font-size: 14px;
                line-height: 1.6;
                padding: 16px;
                color: #1E293B;
            }
            QPlainTextEdit:focus {
                outline: none;
            }
        """)
        self.split_highlighter = MarkdownHighlighter(self.split_editor.document())
        self.split_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.split_editor.customContextMenuRequested.connect(self._show_context_menu)
        self.split_editor.installEventFilter(self)
        
        self.split_preview = QWebEngineView()
        self.split_preview.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #1e1e2e;
            }
        """)
        # 设置 QWebChannel 支持复制功能
        self._setup_web_channel(self.split_preview)
        QTimer.singleShot(0, lambda: self.split_preview.setHtml("<html><body style='background-color:#1e1e2e;'></body></html>"))
        
        # 分屏容器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.split_editor)
        self.splitter.addWidget(self.split_preview)
        self.splitter.setSizes([400, 400])
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E2E8F0;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #CBD5E1;
            }
        """)
        
        self.content_stack.addWidget(self.editor)      # 0 - 编辑
        self.content_stack.addWidget(self.preview)     # 1 - 预览
        self.content_stack.addWidget(self.splitter)    # 2 - 分屏
        
        layout.addWidget(self.content_stack)
        
        # 设置默认模式
        self._set_mode("edit", update_preview=False)


    def _setup_web_channel(self, webview):
        """为 QWebEngineView 设置 QWebChannel，支持复制功能"""
        channel = QWebChannel(self)
        copy_handler = CopyHandler(self)
        channel.registerObject("copyHandler", copy_handler)
        webview.page().setWebChannel(channel)
    
    def _get_toolbar_btn_style(self, active):
        """获取工具栏按钮样式"""
        if active:
            return """
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 13px;
                    font-family: 'Microsoft YaHei UI', sans-serif;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: transparent;
                    color: #64748B;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 13px;
                    font-family: 'Microsoft YaHei UI', sans-serif;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    color: #334155;
                }
                QPushButton:checked {
                    background-color: #3B82F6;
                    color: white;
                }
            """
    
    def _setup_connections(self):
        """设置信号连接"""
        self.edit_btn.clicked.connect(lambda: self._set_mode("edit"))
        self.preview_btn.clicked.connect(lambda: self._set_mode("preview"))
        self.split_btn.clicked.connect(lambda: self._set_mode("split"))
        
        self.editor.textChanged.connect(self._on_content_changed)
        self.split_editor.textChanged.connect(self._on_split_content_changed)
        
        self.split_editor.verticalScrollBar().valueChanged.connect(self._on_split_editor_scroll)
        self.editor.verticalScrollBar().valueChanged.connect(self._on_editor_scroll)
        
    def _on_split_content_changed(self):
        """分屏编辑器内容变化时同步"""
        self.content_changed.emit()
        self._update_split_preview()
    
    def _on_split_editor_scroll(self, value):
        """分屏编辑器滚动时同步到预览"""
        if self.content_stack.currentIndex() == 2:
            editor_scrollbar = self.split_editor.verticalScrollBar()
            if editor_scrollbar.maximum() > 0:
                scroll_percent = value / editor_scrollbar.maximum()
                js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent:.4f});"
                self.split_preview.page().runJavaScript(js_code)
    
    def _on_editor_scroll(self, value):
        """编辑器滚动时同步到预览"""
        if self.content_stack.currentIndex() == 1:
            editor_scrollbar = self.editor.verticalScrollBar()
            if editor_scrollbar.maximum() > 0:
                scroll_percent = value / editor_scrollbar.maximum()
                js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent:.4f});"
                self.preview.page().runJavaScript(js_code)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        sender = self.sender()
        active_editor = self.split_editor if sender == self.split_editor else self.editor
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 4px;
                font-size: 14px;
                font-family: 'Microsoft YaHei', 'Arial', sans-serif;
            }
            QMenu::item {
                padding: 6px 24px 6px 8px;
                border-radius: 4px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QMenu::separator {
                height: 1px;
                background: #f0f0f0;
                margin: 4px 0px;
            }
        """)
        
        copy_action = QAction(QIcon(":images/document-copy.png"), "复制", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(active_editor.copy)
        copy_action.setEnabled(active_editor.textCursor().hasSelection())
        
        paste_action = QAction(QIcon(":images/clipboard-paste-document-text.png"), "粘贴", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: self._handle_paste(active_editor))
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(clipboard.mimeData().hasText() or clipboard.mimeData().hasImage() or clipboard.mimeData().hasHtml())
        
        export_pdf_action = QAction(QIcon(":images/question.png"), "导出PDF", self)
        export_pdf_action.triggered.connect(self.export_to_pdf)
        
        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(export_pdf_action)
        
        menu.exec(QCursor.pos())
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理 Ctrl+V 粘贴图片"""
        if obj in (self.editor, self.split_editor):
            if event.type() == event.Type.KeyPress:
                if event.matches(QKeySequence.StandardKey.Paste):
                    self._handle_paste(obj)
                    return True
        return super().eventFilter(obj, event)
    
    def _handle_paste(self, editor):
        """处理粘贴操作，支持图片粘贴"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self._insert_image_from_qimage(editor, image)
                return
        
        if mime_data.hasUrls():
            urls = mime_data.urls()
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in image_extensions:
                        self._insert_image_from_file(editor, file_path)
                        return
        
        editor.paste()
    
    def _insert_image_from_qimage(self, editor, image):
        """从 QImage 插入图片"""
        if not self.md_file_path:
            QMessageBox.warning(self, "无法插入图片", "请先保存 Markdown 文件")
            return
        
        try:
            md_dir = os.path.dirname(self.md_file_path)
            images_dir = os.path.join(md_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_name = f"image_{timestamp}.png"
            image_path = os.path.join(images_dir, image_name)
            
            if not image.save(image_path, "PNG"):
                QMessageBox.warning(self, "保存失败", "无法保存图片文件")
                return
            
            relative_path = f"images/{image_name}"
            md_image = f"![图片]({relative_path})"
            
            cursor = editor.textCursor()
            cursor.insertText(md_image)
            
            logger.info(f"图片已保存: {image_path}")
            
        except Exception as e:
            logger.error(f"插入图片失败: {str(e)}")
            QMessageBox.critical(self, "插入失败", f"插入图片时出错:\n{str(e)}")
    
    def _insert_image_from_file(self, editor, source_path):
        """从文件路径插入图片"""
        if not self.md_file_path:
            QMessageBox.warning(self, "无法插入图片", "请先保存 Markdown 文件")
            return
        
        try:
            md_dir = os.path.dirname(self.md_file_path)
            images_dir = os.path.join(md_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            original_name = os.path.basename(source_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(original_name)
            new_name = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(images_dir, new_name)
            
            shutil.copy2(source_path, dest_path)
            
            relative_path = f"images/{new_name}"
            md_image = f"![{name}]({relative_path})"
            
            cursor = editor.textCursor()
            cursor.insertText(md_image)
            
            logger.info(f"图片已复制: {dest_path}")
            
        except Exception as e:
            logger.error(f"插入图片失败: {str(e)}")
            QMessageBox.critical(self, "插入失败", f"插入图片时出错:\n{str(e)}")
    
    def export_to_pdf(self):
        """导出当前内容为PDF文件"""
        default_filename = "导出文档.pdf"
        if self.md_file_path:
            default_filename = os.path.splitext(os.path.basename(self.md_file_path))[0] + ".pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", default_filename, "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            from PySide6.QtPrintSupport import QPrinter
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageSize(QPrinter.A4)
            
            current_widget = self.content_stack.currentWidget()
            active_editor = self.split_editor if current_widget == self.splitter else self.editor
            
            active_editor.document().print_(printer)
            
            logger.info(f"PDF导出成功: {file_path}")
            QMessageBox.information(self, "导出成功", f"PDF文件已保存到:\n{file_path}")
        except Exception as e:
            logger.error(f"PDF导出失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出PDF时出错:\n{str(e)}")
        
    def _update_split_preview(self):
        """更新分屏预览内容（带防抖）"""
        self._preview_update_timer.start(100)
    
    def _do_update_split_preview(self):
        """实际执行分屏预览更新，保持滚动位置"""
        md_content = self.split_editor.toPlainText()
        html_content = render_markdown(md_content, dark_mode=False)
        
        # 获取当前滚动位置（使用 JavaScript）
        self.split_preview.page().runJavaScript("window.pageYOffset || document.documentElement.scrollTop;", 
            lambda scroll_y: self._update_preview_with_scroll(md_content, html_content, scroll_y or 0))
    
    def _update_preview_with_scroll(self, md_content, html_content, scroll_y):
        """更新预览并恢复滚动位置，使用JS更新避免闪烁"""
        # 提取 body 内容用于 JS 更新
        import re
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
        if body_match:
            body_content = body_match.group(1).strip()
        else:
            body_content = html_content

        # 转义用于 JavaScript 字符串
        body_content = body_content.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')

        if not self._split_preview_initialized:
            # 首次加载使用 setHtml
            # 设置 base URL 为 Markdown 文件所在目录，使本地图片资源可以加载
            if self.md_file_path:
                base_url = QUrl.fromLocalFile(os.path.dirname(self.md_file_path) + '/')
                self.split_preview.setHtml(html_content, base_url)
            else:
                self.split_preview.setHtml(html_content)
            self._split_preview_initialized = True
        else:
            # 使用 JavaScript 更新内容，避免闪烁
            js_code = f"""
                document.querySelector('article.markdown-body').innerHTML = '{body_content}';
                if (typeof renderMathInElement !== 'undefined') {{
                    renderMathInElement(document.body, {{
                        delimiters: [
                            {{left: '$$', right: '$$', display: true}},
                            {{left: '$', right: '$', display: false}}
                        ],
                        throwOnError: false
                    }});
                }}
                if (typeof mermaid !== 'undefined') {{
                    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                }}
            """
            self.split_preview.page().runJavaScript(js_code)
        
        # 延迟恢复滚动位置
        def restore_scroll():
            if scroll_y and scroll_y > 0:
                self.split_preview.page().runJavaScript(f"window.scrollTo(0, {scroll_y});")
        
        from PySide6.QtCore import QTimer
        QTimer.singleShot(30, restore_scroll)
    
    def _set_mode(self, mode, update_preview=True):
        """设置显示模式"""
        self.edit_btn.setChecked(mode == "edit")
        self.preview_btn.setChecked(mode == "preview")
        self.split_btn.setChecked(mode == "split")
        
        self.edit_btn.setStyleSheet(self._get_toolbar_btn_style(mode == "edit"))
        self.preview_btn.setStyleSheet(self._get_toolbar_btn_style(mode == "preview"))
        self.split_btn.setStyleSheet(self._get_toolbar_btn_style(mode == "split"))
        
        # 获取当前模式，用于判断是否需要同步内容
        current_mode = self.content_stack.currentIndex()
        
        if mode == "edit":
            # 如果从分屏模式切换到编辑模式，且分屏编辑器有修改，需要同步内容
            if current_mode == 2 and self.split_editor.document().isModified():
                self.editor.blockSignals(True)
                self.editor.setPlainText(self.split_editor.toPlainText())
                self.editor.blockSignals(False)
            self.content_stack.setCurrentIndex(0)
            self._is_preview_mode = False
        elif mode == "preview":
            # 如果从分屏模式切换到预览模式，且分屏编辑器有修改，需要同步内容
            if current_mode == 2 and self.split_editor.document().isModified():
                self.editor.blockSignals(True)
                self.editor.setPlainText(self.split_editor.toPlainText())
                self.editor.blockSignals(False)
            if update_preview:
                self._update_preview()
            self.content_stack.setCurrentIndex(1)
            self._is_preview_mode = True
        elif mode == "split":
            # 切换到分屏模式时，从主编辑器同步内容到分屏编辑器
            # 临时阻塞信号避免触发不必要的更新
            self.split_editor.blockSignals(True)
            self.split_editor.setPlainText(self.editor.toPlainText())
            # 重置分屏编辑器的修改标记，因为内容是刚从主编辑器同步的
            self.split_editor.document().setModified(False)
            self.split_editor.blockSignals(False)
            self._split_preview_initialized = False
            if update_preview:
                self._update_split_preview()
            self.content_stack.setCurrentIndex(2)
            self._is_preview_mode = False
            
    def _on_content_changed(self):
        """内容变化时触发（仅在非分屏模式下使用）"""
        self.content_changed.emit()
            
    def _update_preview(self):
        """更新预览内容"""
        md_content = self.editor.toPlainText()
        html_content = render_markdown(md_content, dark_mode=False)

        # 设置 base URL 为 Markdown 文件所在目录，使本地图片资源可以加载
        if self.md_file_path:
            base_url = QUrl.fromLocalFile(os.path.dirname(self.md_file_path) + '/')
            self.preview.setHtml(html_content, base_url)
        else:
            self.preview.setHtml(html_content)
        
        # 延迟执行 KaTeX 和 Mermaid 渲染（确保脚本已加载）
        def render_math_and_mermaid():
            js_code = """
                console.log('Python triggered render');
                if (typeof renderMathInElement !== 'undefined') {
                    console.log('KaTeX available, rendering...');
                    renderMathInElement(document.body, {
                        delimiters: [
                            {left: '$$', right: '$$', display: true},
                            {left: '$', right: '$', display: false}
                        ],
                        throwOnError: false
                    });
                } else {
                    console.log('KaTeX not available');
                }
                if (typeof mermaid !== 'undefined') {
                    console.log('Mermaid available, rendering...');
                    mermaid.initialize({startOnLoad: false, securityLevel: 'loose'});
                    try {
                        mermaid.run({querySelector: '.mermaid'});
                    } catch (e) {
                        console.error('Mermaid run failed:', e);
                        mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                    }
                } else {
                    console.log('Mermaid not available');
                }
            """
            self.preview.page().runJavaScript(js_code)
        
        # 多次尝试渲染
        from PySide6.QtCore import QTimer
        for delay in [500, 1500, 3000]:
            QTimer.singleShot(delay, render_math_and_mermaid)
        
    def set_file_path(self, file_path):
        """设置文件路径"""
        self.md_file_path = file_path
        if file_path:
            self.path_label.setText(os.path.basename(file_path))
            self.path_label.setToolTip(file_path)
        else:
            self.path_label.setText("未保存")
            self.path_label.setToolTip("")
            
    def load_file(self, file_path):
        """加载 Markdown 文件"""
        # 处理空路径：清空编辑器并重置状态
        if not file_path:
            self.editor.blockSignals(True)
            self.split_editor.blockSignals(True)
            self.editor.clear()
            self.split_editor.clear()
            self.set_file_path(None)  # 清空文件路径
            self.editor.document().setModified(False)
            self.split_editor.document().setModified(False)
            self.editor.blockSignals(False)
            self.split_editor.blockSignals(False)
            return True
        
        try:
            # 临时阻塞信号，避免加载过程中触发不必要的更新
            self.editor.blockSignals(True)
            self.split_editor.blockSignals(True)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.split_editor.setPlainText(content)
            self.set_file_path(file_path)

            # 重置修改标记
            self.editor.document().setModified(False)
            self.split_editor.document().setModified(False)

            # 恢复信号
            self.editor.blockSignals(False)
            self.split_editor.blockSignals(False)

            # 根据当前模式更新预览
            current_mode = self.content_stack.currentIndex()
            if current_mode == 1:
                self._update_preview()
            elif current_mode == 2:
                self._split_preview_initialized = False
                self._update_split_preview()

            return True
        except Exception as e:
            # 确保信号恢复
            self.editor.blockSignals(False)
            self.split_editor.blockSignals(False)
            logger.error(f"加载 Markdown 文件失败: {e}")
            return False
            
    def save_file(self, file_path=None):
        """保存 Markdown 文件"""
        # 保存当前要使用的文件路径（避免在保存过程中被修改）
        target_path = file_path if file_path else self.md_file_path
        
        if not target_path:
            logger.error("保存失败：没有指定文件路径")
            return False

        try:
            parent_dir = os.path.dirname(target_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            # 获取内容的逻辑：
            # 1. 如果分屏编辑器有修改（无论当前是否在分屏模式），优先使用分屏编辑器的内容
            # 2. 否则使用主编辑器的内容
            # 3. 最后同步两个编辑器的内容
            current_mode = self.content_stack.currentIndex()
            
            # 检查分屏编辑器是否有修改 - 这是关键！
            # 即使用户切换到了其他模式，只要分屏编辑器有修改，就应该保存它
            if self.split_editor.document().isModified():
                content = self.split_editor.toPlainText()
                content = self.change_time_tag_persistence(content)
                logger.debug(f"保存分屏编辑器内容到: {target_path}")
                # 同步到主编辑器（阻塞信号避免触发自动保存循环）
                self.editor.blockSignals(True)
                self.editor.setPlainText(content)
                self.editor.blockSignals(False)
            elif current_mode == 2:  # 分屏模式（但上面的条件未触发，可能是新建文件等情况）
                content = self.split_editor.toPlainText()
                content = self.change_time_tag_persistence(content)
                logger.debug(f"分屏模式下保存内容到: {target_path}")
                # 同步到主编辑器
                self.editor.blockSignals(True)
                self.editor.setPlainText(content)
                self.editor.blockSignals(False)
            else:
                # 使用主编辑器的内容
                content = self.editor.toPlainText()
                content = self.change_time_tag_persistence(content)
                logger.debug(f"保存主编辑器内容到: {target_path}")
                # 同步到分屏编辑器
                self.split_editor.blockSignals(True)
                self.split_editor.setPlainText(content)
                self.split_editor.blockSignals(False)

            # 使用 target_path 而不是 self.md_file_path，确保保存到正确的路径
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 只有在保存成功后才更新文件路径
            self.md_file_path = target_path
            self.set_file_path(self.md_file_path)

            # 重置修改标记
            self.editor.document().setModified(False)
            self.split_editor.document().setModified(False)


            # 持久化索引表格
            db = NoteDB("recent_notebooks.db")
            indexing_db = NoteDB("indexing_queue.db")
            # 获取笔记本的根目录
            list_path = db.get_recent_notebooks(1)
            if list_path:
                root_path = list_path[0]
                rel_path = os.path.relpath(target_path, root_path)
                # 更新到sqlite表格中
                indexing_db.add_to_index_queue(rel_path)
            # 3. 检查是否触发批处理
            if indexing_db.get_queue_size() >= 2:
                self._execute_batch_indexing(indexing_db, root_path)

            logger.info(f"Markdown 文件保存成功: {target_path}")
            return True

        except Exception as e:
            logger.error(f"保存 Markdown 文件失败: {e}")
            return False

    # 进行时间持久化
    def change_time_tag_persistence(self, content):
        if "[time]" in content:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = content.replace("[time]", f"[time:{now_str}]")
        return content

    def get_content(self):
        """获取当前内容"""
        # 根据当前模式获取正确的编辑器内容
        current_mode = self.content_stack.currentIndex()
        if current_mode == 2:  # 分屏模式
            return self.split_editor.toPlainText()
        return self.editor.toPlainText()
        
    def set_content(self, content):
        """设置内容"""
        self.editor.setPlainText(content)
        
    def is_modified(self):
        """检查是否有修改"""
        # 根据当前模式检查正确的编辑器
        current_mode = self.content_stack.currentIndex()
        if current_mode == 2:  # 分屏模式
            return self.split_editor.document().isModified()
        return self.editor.document().isModified()

    def clear(self):
        """清空内容"""
        self.editor.clear()
        self.md_file_path = None
        self.path_label.setText("未保存")

    def _execute_batch_indexing(self, indexing_db, root_path):
        """
        触发后台线程执行批量索引插入（异步执行，不阻塞 GUI）

        Args:
            indexing_db: NoteDB 实例（indexing_queue.db）
            root_path: 笔记本根目录的绝对路径
        """
        # 启动后台线程处理索引，避免阻塞 GUI
        thread = threading.Thread(
            target=self._batch_indexing_worker,
            args=(root_path,),
            daemon=True
        )
        thread.start()
        logger.info("🚀 批量索引后台任务已启动")

    def _batch_indexing_worker(self, root_path):
        """
        批量索引工作线程（在后台执行）

        Args:
            root_path: 笔记本根目录的绝对路径
        """
        try:
            from gui.data.ChromaDBManager import get_chroma_manager
            from gui.data.NoteDB import NoteDB

            # 在线程中创建新的数据库连接（线程安全）
            indexing_db = NoteDB("indexing_queue.db")

            # 获取 ChromaDBManager 实例（带重试机制）
            try:
                chroma_manager = get_chroma_manager()
            except Exception as e:
                logger.error(f"ChromaDBManager 初始化失败，跳过本次索引: {e}")
                return

            # 验证 ChromaDBManager 是否已正确初始化
            if not hasattr(chroma_manager, 'notes_collection') or chroma_manager.notes_collection is None:
                logger.error("ChromaDBManager 未正确初始化，跳过本次索引")
                return

            # 循环处理直到队列为空
            while True:
                # 1. 从队列中读取一条记录（按时间顺序）
                cursor = indexing_db.conn.execute(
                    'SELECT rel_path, action FROM indexing_queue ORDER BY timestamp LIMIT 1'
                )
                task = cursor.fetchone()

                if not task:
                    break  # 队列为空，退出循环

                rel_path, action = task

                # 2. 转换为绝对路径
                abs_path = os.path.join(root_path, rel_path)
                abs_path = os.path.normpath(abs_path)

                # 3. 检查文件是否存在
                if not os.path.exists(abs_path):
                    logger.warning(f"文件不存在，跳过索引: {abs_path}")
                    # 删除不存在的文件记录
                    indexing_db.conn.execute(
                        'DELETE FROM indexing_queue WHERE rel_path = ?', (rel_path,)
                    )
                    indexing_db.conn.commit()
                    continue

                # 4. 直接执行索引插入（不使用队列）
                try:
                    # 检测文件类型
                    file_type = chroma_manager._detect_file_type(abs_path)

                    # 直接索引文件（同步执行）
                    chroma_manager._index_file(abs_path, file_type)

                    # 5. 插入成功后，立即删除该条记录
                    indexing_db.conn.execute(
                        'DELETE FROM indexing_queue WHERE rel_path = ?', (rel_path,)
                    )
                    indexing_db.conn.commit()

                    logger.info(f"✅ 索引成功并删除记录: {rel_path}")

                except Exception as e:
                    logger.error(f"❌ 索引失败 {rel_path}: {e}")
                    # 索引失败时不删除记录，留待下次重试
                    # 为避免无限循环，暂时跳过这一条
                    break

            logger.info("批量索引后台任务完成")

        except Exception as e:
            logger.error(f"批量索引后台任务失败: {e}")


