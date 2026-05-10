from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
import sys

class TransparentOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Frameless and Always on Top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.WindowTransparentForInput  # Makes it click-through!
        )
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()
        
    def init_ui(self):
        self.setGeometry(100, 100, 400, 200)
        
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        
        # Example UI Element
        self.shanten_label = QLabel("Shanten: --", self)
        self.shanten_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        
        self.layout.addWidget(self.shanten_label)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def update_data(self, shanten_val, ukeire_data=None):
        self.shanten_label.setText(f"Shanten: {shanten_val}")

def run_overlay():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_overlay()
