import os
import re
import sys


from gui.func.utils.json_utils import JsonEditor
# Import the resource file to register the resources
# 这个文件的引用不能删除 否则下面的图片就会找不到文件
from gui.ui import resource_rc

from PySide6.QtCore import QSize, Qt, QtMsgType, qInstallMessageHandler, Slot, QUrl, QTimer
from PySide6.QtGui import QAction, QActionGroup, QFont, QIcon, QKeySequence, QTextCharFormat, QTextDocument, QImage
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
    QColorDialog,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QSizePolicy, QFrame, QTreeWidgetItem, QTableWidgetItem, QVBoxLayout
)

# Import the generated UI class from ui_main_window.py
from gui.ui.ui_main_window import Ui_MainWindow
from gui.func.left.XPNotebookTree import XPNotebookTree
from gui.func.right_top_corner.XPTreeRightTop import XPTreeRightTop
from gui.func.right_bottom_corner.RichTextEdit import RichTextEdit
from gui.func.top_menu.file_action import FileActions
from gui.func.singel_pkg.single_manager import sm
try:
    import sip
except ImportError:
    sip = None
from gui.func.under_top_menu.color_picker import ColorPickerTool
# Custom Qt message handler for debugging
def qt_message_handler(msg_type: QtMsgType, context, msg: str):
    print(f"Qt Message [{msg_type}]: {msg} ({context.file}:{context.line})")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # 创建占位框（仅初始化时显示）
        self.placeholder_frame = QFrame()
        self.placeholder_frame.setMinimumWidth(200)
        self.placeholder_frame.setFrameShape(QFrame.StyledPanel)
        self.placeholder_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 100);  /* 白色半透明遮罩 */
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-image: url(:images/grandidier.jpg);
                background-repeat: no-repeat;
                background-position: center;
                background-origin: content;
            }
        """)

        # 加入左侧 verticalLayout（树位置）
        self.ui.verticalLayout.addWidget(self.placeholder_frame)

        # 绑定这个展示树状图的方法
        sm.left_tree_structure_rander_after_create_new_notebook_signal.connect(self.xp_tree_widget_)

        # 绑定又上角-------------------------------------------
        self.ui.noteTreeContainer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置 layout，如果没有则添加
        if self.ui.noteTreeContainer.layout() is None:
            self.layout = QVBoxLayout(self.ui.noteTreeContainer)
        else:
            self.layout = self.ui.noteTreeContainer.layout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # 必须加
        self.layout.setSpacing(0)
        # 清除旧内容
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        # 加载 XPNotebookTree 右上角的树
        tree = XPTreeRightTop("")
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 设置扩展策略
        self.layout.addWidget(tree)
        # 绑定又上角-----------------结束--------------------------

        # 用来接收富文本框的路径
        self.richtext_saved_path = None
        sm.send_current_file_path_2_main_richtext_signal.connect(self.receiver_path)
        # Create editor using RichTextEdit
        # 富文本框
        self.rich_text_editor = RichTextEdit(self)
        # 监听文件改动 只要文件改动就进行保存
        self.rich_text_editor.textChanged.connect(self.auto_save_note)
        self.rich_text_editor.selectionChanged.connect(self.update_format)

        # Add editor to noteContentTable
        self.ui.noteContentTable.setCellWidget(0, 0, self.rich_text_editor)

        # Adjust table size
        self.ui.noteContentTable.setRowHeight(0, self.ui.noteContentTable.height())
        self.ui.noteContentTable.setColumnWidth(0, self.ui.noteContentTable.width())

        # Ensure the table resizes with the window
        self.ui.noteContentTable.horizontalHeader().setStretchLastSection(True)
        self.ui.noteContentTable.verticalHeader().setStretchLastSection(True)

        # Ensure the cell widget (RichTextEdit) fits perfectly
        self.ui.noteContentTable.setRowHeight(0, self.ui.noteContentTable.height())
        self.ui.noteContentTable.setColumnWidth(0, self.ui.noteContentTable.width())
        # Remove any default margins in the table
        self.ui.noteContentTable.setContentsMargins(0, 0, 0, 0)
        self.path = None

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # 初始化功能类
        self.file_actions = FileActions(self)  # 传入 self 以便弹窗等能绑定主窗口
        self.ui.menuFile.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 8px;  /* 设置圆角半径 */
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;  /* 给 item 也加圆角，避免选中时遮住菜单圆角 */
            }
            QMenu::item:selected {
                background-color: #cce8ff;  /* 浅蓝色 */
                border-radius: 4px;
            }
        """)

        # 创建笔记
        self.ui.menuFile.addAction(self.file_actions.create_file_action())
        # 打开笔记
        self.ui.menuFile.addAction(self.file_actions.open_notebook_action())
        # 打开最近的笔记本
        self.ui.menuFile.addAction(self.file_actions.open_recent_notebook_action())


        save_file_action = QAction(
            QIcon(":/images/disk.png"), "Save", self
        )
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)


        saveas_file_action = QAction(
            QIcon(":/images/disk--pencil.png"),
            "Save As...",
            self,
        )
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)


        print_action = QAction(
            QIcon(":/images/printer.png"),
            "Print...",
            self,
        )
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.file_print)


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
        undo_action.triggered.connect(self.rich_text_editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction(
            QIcon(":/images/arrow-curve.png"),
            "Redo",
            self,
        )
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.rich_text_editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(":/images/scissors.png"), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.rich_text_editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(
            QIcon(":/images/document-copy.png"),
            "Copy",
            self,
        )
        copy_action.setStatusTip("Copy selected text")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.rich_text_editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(
            QIcon(":/images/clipboard-paste-document-text.png"),
            "Paste",
            self,
        )
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.rich_text_editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(
            QIcon(":/images/selection-input.png"),
            "Select all",
            self,
        )
        select_action.setStatusTip("Select all text")
        select_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_action.triggered.connect(self.rich_text_editor.selectAll)
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
        self.fonts.currentFontChanged.connect(self.rich_text_editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        # Define font sizes locally since constants.FONT_SIZES is unavailable
        FONT_SIZES = [8, 10, 12, 14, 16, 18, 20, 24, 36]
        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])
        self.fontsize.currentTextChanged.connect(
            lambda s: self.rich_text_editor.setFontPointSize(float(s))
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

        # '''颜色选择 '''
        self.color_picker = ColorPickerTool(self.rich_text_editor, self)
        format_toolbar.addWidget(self.color_picker.tool_button)


        format_menu.addSeparator()

        self.alignl_action = QAction(
            QIcon(":/images/edit-alignment.png"),
            "Align left",
            self,
        )
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
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
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignRight)
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
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignJustify)
        )
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)

        color_toolbar = QToolBar("Color")
        color_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(color_toolbar)
        color_menu = self.menuBar().addMenu("&Format")
        self.bold_action = QAction(
            QIcon(":/images/edit-bold.png"), "Bold", self
        )
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)
        color_toolbar.addAction(self.bold_action)
        color_menu.addAction(self.bold_action)

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
        color_toolbar.addWidget(spacer)
        # color_toolbar.addWidget(search_widget)

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

        self.fonts.setCurrentFont(self.rich_text_editor.currentFont())
        self.fontsize.setCurrentText(str(int(self.rich_text_editor.fontPointSize())))

        self.italic_action.setChecked(self.rich_text_editor.fontItalic())
        self.underline_action.setChecked(self.rich_text_editor.fontUnderline())
        self.bold_action.setChecked(self.rich_text_editor.fontWeight() == QFont.Weight.Bold)

        self.alignl_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignLeft
        )
        self.alignc_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignCenter
        )
        self.alignr_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignRight
        )
        self.alignj_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignJustify
        )

        self.block_signals(self._format_actions, False)
    '''
    修改了富文本的内容 就自动的保存
    '''
    def auto_save_note(self):
        """Auto-save note and ensure all inserted images are saved and displayable."""
        #
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(self.richtext_saved_path)
        if content_type == "file" and self.richtext_saved_path is not None:
            # 写入到对应的文件
            file_path = os.path.join(self.richtext_saved_path, ".note.html")
            self.rich_text_editor.html_file_path = file_path
            self.rich_text_editor.clean_base64_images()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.rich_text_editor.toHtml())



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
            self.rich_text_editor.setText(text)
            self.update_title()

    def file_save(self):
        if self.path is None:
            return self.file_saveas()

        text = (
            self.rich_text_editor.toHtml()
            if os.path.splitext(self.path)[1].lower() in ['.html', '.htm']
            else self.rich_text_editor.toPlainText()
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
            self.rich_text_editor.toHtml()
            if os.path.splitext(path)[1].lower() in ['.html', '.htm']
            else self.rich_text_editor.toPlainText()
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
            self.rich_text_editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle(
            "%s - Megasolid Idiom"
            % (os.path.basename(self.path) if self.path else "Untitled")
        )

    def edit_toggle_wrap(self):
        self.rich_text_editor.setLineWrapMode(1 if self.rich_text_editor.lineWrapMode() == 0 else 0)

    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        weight = QFont.Bold if not cursor.charFormat().font().bold() else QFont.Normal
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        self.rich_text_editor.setTextCursor(cursor)

    def toggle_italic(self):
        """Toggle italic formatting for selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        italic = not cursor.charFormat().fontItalic()
        fmt.setFontItalic(italic)
        cursor.mergeCharFormat(fmt)
        self.rich_text_editor.setTextCursor(cursor)

    def toggle_underline(self):
        """Toggle underline formatting for selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        underline = not cursor.charFormat().fontUnderline()
        fmt.setFontUnderline(underline)
        cursor.mergeCharFormat(fmt)
        self.rich_text_editor.setTextCursor(cursor)

    def change_text_color(self):
        """Change the color of selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            self.rich_text_editor.setTextCursor(cursor)

    def search_text(self):
        """Search for text in the editor."""
        search_text = self.search_input.text()
        if not search_text:
            return

        cursor = self.rich_text_editor.document().find(search_text, self.rich_text_editor.textCursor())
        if not cursor.isNull():
            self.rich_text_editor.setTextCursor(cursor)
        else:
            self.status.showMessage("Text not found", 5000)

    '''
    绑定树状图的结构 当创建了新的笔记的时候就将树状图重新渲染
    '''
    @Slot(str)
    def xp_tree_widget_(self, file_path):
        if self.placeholder_frame is not None:
            try:
                self.ui.verticalLayout.removeWidget(self.placeholder_frame)
                self.placeholder_frame.setParent(None)
                self.placeholder_frame.deleteLater()
            except RuntimeError:
                print("placeholder_frame 已被 Qt 删除，跳过")
            self.placeholder_frame = None

        # self.ui.verticalLayout.removeWidget(self.placeholder_frame)
        # self.placeholder_frame.deleteLater()
        print(file_path)
        # 先清空 verticalLayout 中的旧组件
        self.clear_layout(self.ui.verticalLayout)
        tree_widget = XPNotebookTree(file_path, rich_text_edit=self.rich_text_editor)

        self.ui.verticalLayout.addWidget(tree_widget)



    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                # 可能是 layout 或 spacerItem
                child_layout = item.layout()
                if child_layout is not None:
                    self.clear_layout(child_layout)

    def resizeEvent(self, event):
        """Maintain splitter sizes on resize."""
        super().resizeEvent(event)
        self.ui.splitter.setSizes([300, self.width() - 300])
        self.ui.verticalSplitter.setSizes([215, self.height() - 215])
    '''
    富文本框的路径接收
    第一个参数判断路径 第二个参数判断树状图的属性 是属于谁的
    '''
    @Slot(str, str)
    def receiver_path(self,path_, flag):
        self.richtext_saved_path = path_
        # 右上角的数据渲染
        # 获取父目录 只有左侧的树状图点击的时候才会显示 右上角的结构 防止右上角的点击出现循环
        if 'left' == flag:
            # 清空 noteTreeContainer 中旧的 XPNotebookTree（右上角）
            self.clear_layout(self.layout)
            tree = XPTreeRightTop(path_,rich_text_edit=self.rich_text_editor)
            tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # ✅ 设置扩展策略
            self.layout.addWidget(tree)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Megasolid Idiom")
    qInstallMessageHandler(qt_message_handler)
    # 增加全局样式 虽然不是很成功 先放着 后面慢慢的调试
    with open("gui/ui/qss/light.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())