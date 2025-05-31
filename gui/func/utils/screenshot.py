import sys
import pyautogui
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PIL import ImageGrab

class ScreenshotSelector(QWidget):
    def __init__(self):
        super().__init__()
        # Simplified the window setup for testing
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure focus is set
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Disable transparency
        self.setMouseTracking(True)

        screen_size = pyautogui.size()
        self.setGeometry(100, 100, screen_size.width // 2, screen_size.height // 2)  # Set a smaller window for testing

        self.start_point = QPoint()
        self.end_point = QPoint()

        self.selection_done = False
        self.show()  # Make sure window is visible and interactive

    def paintEvent(self, event):
        """Draw a selection rectangle."""
        if self.start_point != self.end_point:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        """Start tracking mouse position when clicked."""
        self.start_point = QPoint(int(event.globalPosition().x()), int(event.globalPosition().y()))
        self.end_point = self.start_point
        print(f"Mouse Press at {self.start_point}")
        self.update()

    def mouseMoveEvent(self, event):
        """Update the selection rectangle as the mouse moves."""
        if not self.selection_done:
            self.end_point = QPoint(int(event.globalPosition().x()), int(event.globalPosition().y()))
            print(f"Mouse Move to {self.end_point}")
            self.update()

    def mouseReleaseEvent(self, event):
        """Finish selection and take screenshot when the mouse is released."""
        self.end_point = QPoint(int(event.globalPosition().x()), int(event.globalPosition().y()))
        self.selection_done = True
        print(f"Mouse Release at {self.end_point}")
        self.take_screenshot()

    def take_screenshot(self):
        """Capture the screenshot of the selected area."""
        rect = QRect(self.start_point, self.end_point).normalized()
        if rect.width() < 5 or rect.height() < 5:
            print("选择区域太小")
            return

        try:
            print(f"尝试截图区域: {rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

            # Using Pillow's ImageGrab for screenshot
            screenshot = ImageGrab.grab(bbox=(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height()))
            screenshot.save(filename)
            print(f"截图已保存: {filename}")
        except Exception as e:
            print(f"截图失败: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    selector = ScreenshotSelector()
    sys.exit(app.exec())
