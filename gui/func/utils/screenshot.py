import sys
import pyautogui
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QPainter, QPen, QColor


class ScreenshotSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # 设置全屏
        screen_size = pyautogui.size()
        self.setGeometry(0, 0, screen_size.width, screen_size.height)

        self.start_point = QPoint()
        self.end_point = QPoint()

        self.selection_done = False
        self.showFullScreen()

    def paintEvent(self, event):
        if self.start_point != self.end_point:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.start_point = event.globalPosition().toPoint()
        self.end_point = self.start_point
        self.update()

    def mouseMoveEvent(self, event):
        if not self.selection_done:
            self.end_point = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        self.end_point = event.globalPosition().toPoint()
        self.selection_done = True
        self.hide()

        # 延迟截图，确保窗口完全隐藏
        QTimer.singleShot(200, self.take_screenshot)

    def take_screenshot(self):
        rect = QRect(self.start_point, self.end_point).normalized()
        if rect.width() < 5 or rect.height() < 5:
            print("选择区域太小")
            self.close()
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

            # pyautogui 不能截取当前程序窗口，需要确保当前窗口已隐藏
            pyautogui.screenshot(
                filename,
                region=(rect.x(), rect.y(), rect.width(), rect.height())
            )
            print(f"截图已保存: {filename}")
        except Exception as e:
            print(f"截图失败: {e}")
        finally:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    selector = ScreenshotSelector()
    sys.exit(app.exec())
