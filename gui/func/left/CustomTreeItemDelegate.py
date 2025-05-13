from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit

'''
这个是控制左边的树的边框高度
'''
class CustomTreeItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMinimumHeight(23)  # 关键：设置更高高度
        editor.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 0px;
                border: 1px solid #3A8EDB;
                border-radius: 6px;
                background-color: white;
            }
        """)
        return editor
