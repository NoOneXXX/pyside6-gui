import os
import sys

# Import the resource file to register the resources
from gui.ui import resource_rc


from PySide6.QtCore import QSize, Qt, QtMsgType, qInstallMessageHandler, QUrl
from PySide6.QtGui import QAction, QActionGroup, QFont, QIcon, QKeySequence, QTextCharFormat, QColor, QTextDocument, QImage
from PySide6.QtPrintSupport import QPrintDialog
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QWidget,
    QMenu,
    QColorDialog,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QSizePolicy
)

# Import the generated UI class from ui_main_window.py
from gui.ui.ui_main_window import Ui_MainWindow

# Custom Qt message handler for debugging
def qt_message_handler(msg_type: QtMsgType, context, msg: str):
    print(f"Qt Message [{msg_type}]: {msg} ({context.file}:{context.line})")

class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        font = QFont("Times", 20)
        self.setFont(font)
        self.setFontPointSize(20)

    def insertFromMimeData(self, source):
        """Handle paste events to support images from clipboard."""
        cursor = self.textCursor()
        document = self.document()

        if source.hasImage():
            image = source.imageData()
            if image.isNull():
                super().insertFromMimeData(source)
                return

            image_name = f"image_{id(image)}.png"
            document.addResource(QTextDocument.ImageResource, QUrl(image_name), image)
            cursor.insertImage(image_name)
            self.setTextCursor(cursor)
        elif source.hasUrls():
            for u in source.urls():
                file_ext = os.path.splitext(str(u.toLocalFile()))[1].lower()
                if u.isLocalFile() and file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())
                else:
                    break
            else:
                return
        else:
            super().insertFromMimeData(source)

    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def contextMenuEvent(self, event):
        """Customize the context menu to fix text shadow issue."""
        menu = self.createStandardContextMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #CCCCCC;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #E0E0E0;
            }
        """)
        menu.exec(event.globalPos())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create editor using RichTextEdit
        self.editor = RichTextEdit(self)
        self.editor.selectionChanged.connect(self.update_format)

        # Add editor to noteContentTable
        self.ui.noteContentTable.setCellWidget(0, 0, self.editor)

        # Adjust table size
        self.ui.noteContentTable.setRowHeight(0, self.ui.noteContentTable.height())
        self.ui.noteContentTable.setColumnWidth(0, self.ui.noteContentTable.width())

        # Ensure the table resizes with the window
        self.ui.noteContentTable.horizontalHeader().setStretchLastSection(True)
        self.ui.noteContentTable.verticalHeader().setStretchLastSection(True)

        self.path = None

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(14, 14))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        open_file_action = QAction(
            QIcon(":/images/blue-folder-open-document.png"),
            "Open file...",
            self,
        )
        open_file_action.setStatusTip("Open file")
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        file_toolbar.addAction(open_file_action)

        save_file_action = QAction(
            QIcon(":/images/disk.png"), "Save", self
        )
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        file_toolbar.addAction(save_file_action)

        saveas_file_action = QAction(
            QIcon(":/images/disk--pencil.png"),
            "Save As...",
            self,
        )
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        print_action = QAction(
            QIcon(":/images/printer.png"),
            "Print...",
            self,
        )
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        file_toolbar.addAction(print_action)

        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction(
            QIcon(":/images/arrow-curve-180-left.png"),
            "Undo",
            self,
        )
        undo_action.setStatusTip("Undo last change")
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction(
            QIcon(":/images/arrow-curve.png"),
            "Redo",
            self,
        )
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(":/images/scissors.png"), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(
            QIcon(":/images/document-copy.png"),
            "Copy",
            self,
        )
        copy_action.setStatusTip("Copy selected text")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(
            QIcon(":/images/clipboard-paste-document-text.png"),
            "Paste",
            self,
        )
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(
            QIcon(":/images/selection-input.png"),
            "Select all",
            self,
        )
        select_action.setStatusTip("Select all text")
        select_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QAction(
            QIcon(":/images/arrow-continue.png"),
            "Wrap text to window",
            self,
        )
        wrap_action.setStatusTip("Toggle wrap text to window")
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(format_toolbar)
        format_menu = self.menuBar().addMenu("&Format")

        self.fonts = QFontComboBox()
        self.fonts.currentFontChanged.connect(self.editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        # Define font sizes locally since constants.FONT_SIZES is unavailable
        FONT_SIZES = [8, 10, 12, 14, 16, 18, 20, 24, 36]
        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])
        self.fontsize.currentTextChanged.connect(
            lambda s: self.editor.setFontPointSize(float(s))
        )
        format_toolbar.addWidget(self.fontsize)

        self.bold_action = QAction(
            QIcon(":/images/edit-bold.png"), "Bold", self
        )
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        self.italic_action = QAction(
            QIcon(":/images/edit-italic.png"),
            "Italic",
            self,
        )
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self.toggle_italic)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(
            QIcon(":/images/edit-underline.png"),
            "Underline",
            self,
        )
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self.toggle_underline)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        format_menu.addSeparator()

        self.alignl_action = QAction(
            QIcon(":/images/edit-alignment.png"),
            "Align left",
            self,
        )
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
        )
        format_toolbar.addAction(self.alignl_action)
        format_menu.addAction(self.alignl_action)

        self.alignc_action = QAction(
            QIcon(":/images/edit-alignment-center.png"),
            "Align center",
            self,
        )
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        )
        format_toolbar.addAction(self.alignc_action)
        format_menu.addAction(self.alignc_action)

        self.alignr_action = QAction(
            QIcon(":/images/edit-alignment-right.png"),
            "Align right",
            self,
        )
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        )
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.alignj_action = QAction(
            QIcon(":/images/edit-alignment-justify.png"),
            "Justify",
            self,
        )
        self.alignj_action.setStatusTip("Justify text")
        self.alignj_action.setCheckable(True)
        self.alignj_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify)
        )
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)

        # Add search box and button
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_text)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        # Add a spacer widget to push search_widget to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        format_toolbar.addWidget(spacer)
        format_toolbar.addWidget(search_widget)

        self._format_actions = [
            self.fonts,
            self.fontsize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
        ]

        self.update_format()
        self.update_title()

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def update_format(self):
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.editor.currentFont())
        self.fontsize.setCurrentText(str(int(self.editor.fontPointSize())))

        self.italic_action.setChecked(self.editor.fontItalic())
        self.underline_action.setChecked(self.editor.fontUnderline())
        self.bold_action.setChecked(self.editor.fontWeight() == QFont.Weight.Bold)

        self.alignl_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignLeft
        )
        self.alignc_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignCenter
        )
        self.alignr_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignRight
        )
        self.alignj_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignJustify
        )

        self.block_signals(self._format_actions, False)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        try:
            with open(path, "rU") as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.editor.setText(text)
            self.update_title()

    def file_save(self):
        if self.path is None:
            return self.file_saveas()

        text = (
            self.editor.toHtml()
            if os.path.splitext(self.path)[1].lower() in ['.html', '.htm']
            else self.editor.toPlainText()
        )

        try:
            with open(self.path, "w") as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        if not path:
            return

        text = (
            self.editor.toHtml()
            if os.path.splitext(path)[1].lower() in ['.html', '.htm']
            else self.editor.toPlainText()
        )

        try:
            with open(path, "w") as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle(
            "%s - Megasolid Idiom"
            % (os.path.basename(self.path) if self.path else "Untitled")
        )

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(1 if self.editor.lineWrapMode() == 0 else 0)

    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        weight = QFont.Bold if not cursor.charFormat().font().bold() else QFont.Normal
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def toggle_italic(self):
        """Toggle italic formatting for selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        italic = not cursor.charFormat().fontItalic()
        fmt.setFontItalic(italic)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def toggle_underline(self):
        """Toggle underline formatting for selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        underline = not cursor.charFormat().fontUnderline()
        fmt.setFontUnderline(underline)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def change_text_color(self):
        """Change the color of selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return

        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            self.editor.setTextCursor(cursor)

    def search_text(self):
        """Search for text in the editor."""
        search_text = self.search_input.text()
        if not search_text:
            return

        cursor = self.editor.document().find(search_text, self.editor.textCursor())
        if not cursor.isNull():
            self.editor.setTextCursor(cursor)
        else:
            self.status.showMessage("Text not found", 5000)

    def resizeEvent(self, event):
        """Maintain splitter sizes on resize."""
        super().resizeEvent(event)
        self.ui.splitter.setSizes([300, self.width() - 300])
        self.ui.verticalSplitter.setSizes([215, self.height() - 215])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Megasolid Idiom")
    qInstallMessageHandler(qt_message_handler)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())