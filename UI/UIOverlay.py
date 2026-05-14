from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QFormLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QImage
import sys
import os
import json
import numpy as np

class AssistantWindow(QMainWindow):
    # Signals for threading/communication
    settings_changed_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        
        # Make the window draggable and stay on top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Give it a dark aesthetic
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")
        
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        self.settings = self.load_settings()
        
        self.init_ui()
        
    def load_settings(self):
        default = {
            "app_name": "Mahjong Soul",
            "autolock": False,
            "crop_x": 0,
            "crop_y": 0,
            "crop_w": 0,
            "crop_h": 0
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    default.update(data)
            except Exception:
                pass
        return default

    def save_settings(self):
        try:
            self.settings["app_name"] = self.app_input.text()
            self.settings["crop_x"] = int(self.cx_input.text() or 0)
            self.settings["crop_y"] = int(self.cy_input.text() or 0)
            self.settings["crop_w"] = int(self.cw_input.text() or 0)
            self.settings["crop_h"] = int(self.ch_input.text() or 0)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                
            self.settings_changed_signal.emit(self.settings)
        except ValueError:
            print("Invalid crop bounds")

    def init_ui(self):
        self.setWindowTitle("Mahjong Assistant")
        self.setGeometry(100, 100, 600, 400)
        
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        
        # --- Settings UI Section ---
        self.settings_label = QLabel("Capture Settings", self)
        self.settings_label.setStyleSheet("color: #ffa500; font-size: 16px; font-weight: bold; padding: 5px;")
        self.layout.addWidget(self.settings_label)
        
        settings_hbox = QHBoxLayout()
        self.app_input = QLineEdit(self.settings["app_name"])
        self.app_input.setPlaceholderText("Application Name")
        settings_hbox.addWidget(QLabel("App Name:", styleSheet="color: white;"))
        settings_hbox.addWidget(self.app_input)
        
        for p in ["x", "y", "w", "h"]:
            lbl = QLabel(f"Crop {p.upper()}:", styleSheet="color: white;")
            inp = QLineEdit(str(self.settings[f"crop_{p}"]))
            inp.setFixedWidth(50)
            setattr(self, f"c{p}_input", inp)
            settings_hbox.addWidget(lbl)
            settings_hbox.addWidget(inp)
            
        self.save_btn = QPushButton("Save & Apply")
        self.save_btn.setStyleSheet("background-color: #333; color: white;")
        self.save_btn.clicked.connect(self.save_settings)
        settings_hbox.addWidget(self.save_btn)
        
        self.layout.addLayout(settings_hbox)
        
        # Engine Status UI
        self.status_label = QLabel("Engine Status: Waiting to lock...", self)
        self.status_label.setStyleSheet("color: cyan; font-size: 14px; padding-top: 10px;")
        self.layout.addWidget(self.status_label)
        
        # Debug Vision Window (hidden by default unless active)
        self.debug_label = QLabel(self)
        self.debug_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.debug_label.setStyleSheet("background-color: #000; border: 1px solid #444;")
        self.layout.addWidget(self.debug_label)
        
        # Current Hand UI Section 
        self.hand_label = QLabel("Current Hand:", self)
        self.hand_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background-color: rgba(50, 50, 50, 255); padding: 5px; border-radius: 5px;")
        self.layout.addWidget(self.hand_label)
        
        # HBox for the current hand tiles
        self.hand_layout = QHBoxLayout()
        self.hand_tile_widgets = []
        for i in range(14):  # 14 tiles in a full hand
            vbox = QVBoxLayout()
            
            ukeire_lbl = QLabel(self)
            ukeire_lbl.setStyleSheet("color: limegreen; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 100); border-radius: 3px;")
            ukeire_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            tile_lbl = QLabel(self)
            tile_lbl.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 5px; padding: 2px;")
            tile_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            vbox.addWidget(ukeire_lbl)
            vbox.addWidget(tile_lbl)
            self.hand_layout.addLayout(vbox)
            self.hand_tile_widgets.append((ukeire_lbl, tile_lbl))
        self.layout.addLayout(self.hand_layout)
        
        # Shanten UI Element
        self.shanten_label = QLabel("Shanten: --", self)
        self.shanten_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        self.layout.addWidget(self.shanten_label)
        
        # Discards UI Section
        self.discards_label = QLabel("Best Discards:", self)
        self.discards_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 5px; border-radius: 5px;")
        self.layout.addWidget(self.discards_label)
        
        # HBox for tiles
        self.tiles_layout = QHBoxLayout()
        self.tile_labels = []
        for i in range(3):
            lbl = QLabel(self)
            # Default empty styling
            lbl.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 5px; padding: 5px;")
            self.tiles_layout.addWidget(lbl)
            self.tile_labels.append(lbl)
            
        self.layout.addLayout(self.tiles_layout)
        
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def _build_tile_pixmap(self, tile_name):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tiles_dir = os.path.join(base_dir, "..", "assets", "tiles")
        front_path = os.path.join(tiles_dir, "Front.png")
        tile_path = os.path.join(tiles_dir, tile_name)
        
        if not os.path.exists(front_path) or not os.path.exists(tile_path):
            return QPixmap()
            
        base_pixmap = QPixmap(front_path)
        symbol_pixmap = QPixmap(tile_path)
        
        # Shrink the symbol slightly so it fits inside the tile borders and composite it onto the base tile
        symbol_pixmap = symbol_pixmap.scaled(base_pixmap.size() * 0.8, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        painter = QPainter(base_pixmap)
        painter.drawPixmap((base_pixmap.width() - symbol_pixmap.width()) // 2, (base_pixmap.height() - symbol_pixmap.height()) // 2, symbol_pixmap)
        painter.end()
        
        # High DPI scaling
        base_pixmap = base_pixmap.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
        base_pixmap.setDevicePixelRatio(2)
        return base_pixmap

    def update_data(self, current_state):
        if "status" in current_state:
            self.status_label.setText(f"Engine Status: {current_state['status']}")
            
        shanten_val = current_state.get('shanten')
        if shanten_val is not None:
            self.shanten_label.setText(f"Shanten: {shanten_val}")
        else:
            self.shanten_label.setText("Shanten: --")
            
        hand_data = current_state.get('hand_data', [])
        discard_filenames = current_state.get('discards', [])
        
        # Display debug vision frame
        debug_frame = current_state.get('debug_frame')
        if debug_frame is not None:
            height, width, channel = debug_frame.shape
            bytesPerLine = 3 * width
            # Convert BGR to RGB for Qt displaying properly
            qImg = QImage(debug_frame.data, width, height, bytesPerLine, QImage.Format.Format_BGR888)
            pix = QPixmap.fromImage(qImg)
            # Scale it down so it fits nicely
            self.debug_label.setPixmap(pix.scaled(600, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # Clear out existing labels in case they get shortened
        for ukeire_lbl, tile_lbl in self.hand_tile_widgets:
            tile_lbl.clear()
            ukeire_lbl.setText("")
        for lbl in self.tile_labels:
            lbl.clear()
            
        # Update current hand tiles natively from list of dicts
        if hand_data:
            for idx, data in enumerate(hand_data):
                if idx < len(self.hand_tile_widgets):
                    ukeire_lbl, tile_lbl = self.hand_tile_widgets[idx]
                    
                    pixmap = self._build_tile_pixmap(data['filename'])
                    tile_lbl.setPixmap(pixmap)
                    
                    if data.get('ukeire', 0) > 0:
                        ukeire_lbl.setText(f"{data['ukeire']}")
                    else:
                        ukeire_lbl.setText("")
                    
        # Update best discard tiles
        if discard_filenames:
            for idx, filename in enumerate(discard_filenames):
                if idx < len(self.tile_labels):
                    pixmap = self._build_tile_pixmap(filename)
                    self.tile_labels[idx].setPixmap(pixmap)
                    self.tile_labels[idx].setAlignment(Qt.AlignmentFlag.AlignCenter)

def run_overlay():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_overlay()
