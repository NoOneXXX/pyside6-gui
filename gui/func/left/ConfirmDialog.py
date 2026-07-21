# -*- coding: utf-8 -*-
"""
通用确认弹窗组件
无边框 + 圆角容器 + 阴影，风格与 EncryptPasswordDialog 系列保持一致
"""

from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor


class ConfirmDialog(QDialog):
    """自定义确认弹窗，替代原生 QMessageBox.question"""

    def __init__(self, title, message, icon="⚠️", icon_bg="#FEF3C7",
                 confirm_text="确认", cancel_text="取消",
                 confirm_color="#6366F1", confirm_hover_color="#4F46E5",
                 parent=None):
        super().__init__(parent)
        self._title = title
        self._message = message
        self._icon = icon
        self._icon_bg = icon_bg
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._confirm_color = confirm_color
        self._confirm_hover_color = confirm_hover_color

        self._setup_ui()
        self._center_dialog()

    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(380)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        container = QWidget()
        container.setObjectName("confirmContainer")
        container.setStyleSheet("""
            #confirmContainer {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #F3F4F6;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(28, 26, 28, 22)
        container_layout.setSpacing(0)

        # === 图标 ===
        icon_label = QLabel(self._icon)
        icon_label.setFixedSize(52, 52)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self._icon_bg};
                border-radius: 16px;
                font-size: 24px;
            }}
        """)
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()
        container_layout.addLayout(icon_layout)
        container_layout.addSpacing(16)

        # === 标题 ===
        title_label = QLabel(self._title)
        title_label.setStyleSheet("""
            QLabel {
                color: #111827;
                font-size: 17px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI';
            }
        """)
        container_layout.addWidget(title_label)
        container_layout.addSpacing(10)

        # === 正文 ===
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 13px;
                line-height: 20px;
            }
        """)
        container_layout.addWidget(message_label)
        container_layout.addSpacing(24)

        # === 按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton(self._cancel_text)
        cancel_btn.setFixedHeight(38)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #9CA3AF;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton(self._confirm_text)
        confirm_btn.setFixedHeight(38)
        confirm_btn.setCursor(QCursor(Qt.PointingHandCursor))
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._confirm_color};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._confirm_hover_color};
            }}
        """)
        confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(confirm_btn, 1)
        container_layout.addLayout(btn_layout)

        main_layout.addWidget(container)

    def _center_dialog(self):
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)

    @staticmethod
    def ask(parent, title, message, icon="⚠️", icon_bg="#FEF3C7",
            confirm_text="确认", cancel_text="取消",
            confirm_color="#6366F1", confirm_hover_color="#4F46E5"):
        """便捷方法：弹出确认框，返回 True/False"""
        dialog = ConfirmDialog(
            title, message, icon=icon, icon_bg=icon_bg,
            confirm_text=confirm_text, cancel_text=cancel_text,
            confirm_color=confirm_color, confirm_hover_color=confirm_hover_color,
            parent=parent
        )
        return dialog.exec() == QDialog.Accepted


if __name__ == '__main__':
    import sys
    from PySide6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 9))

    ok = ConfirmDialog.ask(
        None,
        "文件过大",
        "该附件大小为 235.6M，超过了 100M。\n超过 100M 的文件无法上传到 GitHub 仓库。\n是否仍然添加该附件？（添加后将不会纳入 GitHub 管理）",
        icon="⚠️",
        icon_bg="#FEF3C7",
        confirm_text="仍然添加",
        cancel_text="取消",
        confirm_color="#F59E0B",
        confirm_hover_color="#D97706",
    )
    print("confirmed:", ok)
    sys.exit(0)
