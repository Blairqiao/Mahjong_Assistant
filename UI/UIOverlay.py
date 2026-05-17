from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QSizePolicy, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QFormLayout, QGridLayout, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QImage, QColor
from . import theme
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
        self.setStyleSheet(f"QMainWindow {{ background-color: {theme.BG_COLOR}; }}")
        
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        self.settings = self.load_settings()
        self.settings_visible = True
        
        self.init_ui()
        
    def load_settings(self):
        default = {
            "app_name": "Mahjong Soul",
            "crop_x": 0,
            "crop_y": 0,
            "crop_w": 0,
            "crop_h": 0,
            "show_debug": True
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
            self.settings["show_debug"] = self.debug_checkbox.isChecked()
            
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                
            self.settings_changed_signal.emit(self.settings)
        except ValueError:
            print("Invalid crop bounds")

    def init_ui(self):
        self.setWindowTitle("Mahjong Assistant")
        self.setGeometry(100, 100, 850, 400)
        
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        # --- Settings UI Section ---
        self.settings_toggle_btn = QPushButton("Capture Settings")
        self.settings_toggle_btn.setCheckable(True)
        self.settings_toggle_btn.setChecked(True)
        self.settings_toggle_btn.clicked.connect(self.toggle_settings_panel)
        self.settings_toggle_btn.setStyleSheet(
            "QPushButton { color: #ffa500; font-size: 16px; font-weight: bold; padding: 6px; background-color: rgba(255, 255, 255, 15); border: 1px solid rgba(255, 255, 255, 30); border-radius: 6px; text-align: left; }"
            "QPushButton:checked { background-color: rgba(255, 165, 0, 35); }"
        )
        self.layout.addWidget(self.settings_toggle_btn)

        self.settings_panel = QWidget(self)
        self.settings_panel_layout = QVBoxLayout(self.settings_panel)
        self.settings_panel_layout.setContentsMargins(4, 0, 4, 0)
        self.settings_panel_layout.setSpacing(4)

        settings_hbox = QHBoxLayout()
        settings_hbox.setContentsMargins(10, 0, 10, 0)
        settings_hbox.setSpacing(4)
        self.settings_panel_layout.addLayout(settings_hbox)

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
            
        # Debug toggle
        self.debug_checkbox = QCheckBox("Show Debug")
        self.debug_checkbox.setChecked(self.settings.get('show_debug', True))
        self.debug_checkbox.setStyleSheet("margin-right: 10px;")
        settings_hbox.addWidget(self.debug_checkbox)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("background-color: #333; color: white;")
        self.save_btn.clicked.connect(self.save_settings)
        settings_hbox.addWidget(self.save_btn)
        
        self.layout.addWidget(self.settings_panel)
        
        # Engine Status UI
        self.status_label = QLabel("Engine Status: Waiting to lock...", self)
        self.status_label.setStyleSheet("color: cyan; font-size: 14px; padding-top: 2px; margin-bottom: 2px;")
        self.layout.addWidget(self.status_label)
        
        # Debug Vision Window
        self.debug_label = QLabel(self)
        self.debug_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.debug_label.setStyleSheet("background-color: #000; border: 1px solid #444;")
        self.debug_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.debug_label.setMaximumHeight(theme.DEBUG_HEIGHT)
        self.layout.addWidget(self.debug_label)
        
        # Current Hand UI Section 
        self.hand_label = QLabel("Current Hand:", self)
        self.hand_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background-color: rgba(50, 50, 50, 255); padding: 8px; border-radius: 5px;")
        self.hand_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.hand_label.setMaximumHeight(40)
        self.layout.addWidget(self.hand_label)
        
        # Grid for the current hand tiles (responsive)
        self.hand_layout = QGridLayout()
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
            self.hand_layout.addLayout(vbox, 0, i)
            self.hand_tile_widgets.append((ukeire_lbl, tile_lbl))
        self.layout.addLayout(self.hand_layout)
        
        # Shanten UI Element
        self.shanten_label = QLabel("Shanten: --", self)
        self.shanten_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        self.shanten_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.shanten_label.setMaximumHeight(40)
        self.layout.addWidget(self.shanten_label)
        
        # Discards UI Section
        self.discards_label = QLabel("Best Discards:", self)
        self.discards_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 5px; border-radius: 5px;")
        self.discards_label.setMaximumHeight(40)
        self.discards_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.discards_label)
        
        # HBox for tiles        
        self.tiles_layout = QGridLayout()
        self.tile_widgets = []
        for i in range(3):  # 14 tiles in a full hand
            vbox = QVBoxLayout()

            ukeire_lbl = QLabel(self)
            ukeire_lbl.setStyleSheet("color: limegreen; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 100); border-radius: 3px;")
            ukeire_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            tile_lbl = QLabel(self)
            tile_lbl.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 5px; padding: 2px;")
            tile_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            vbox.addWidget(ukeire_lbl)
            vbox.addWidget(tile_lbl)
            self.tiles_layout.addLayout(vbox, 0, i)
            self.tile_widgets.append((ukeire_lbl, tile_lbl))
        self.layout.addLayout(self.tiles_layout)
        
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        self._update_window_geometry()

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
        
        # High DPI scaling (base size)
        base_pixmap = base_pixmap.scaledToHeight(theme.TILE_HEIGHT, Qt.TransformationMode.SmoothTransformation)
        base_pixmap.setDevicePixelRatio(2)
        return base_pixmap

    def _ukeire_style(self, value, min_value, max_value):
        if max_value <= min_value:
            color = QColor(255, 165, 0) if value > 0 else QColor(200, 60, 60)
        else:
            ratio = (value - min_value) / (max_value - min_value)
            red = int(220 - (140 * ratio))
            green = int(70 + (170 * ratio))
            color = QColor(red, green, 70)

        return (
            f"color: {color.name()}; "
            "font-size: 14px; font-weight: bold; "
            "background-color: rgba(0, 0, 0, 100); border-radius: 3px;"
        )

    def update_data(self, current_state):
        if self.settings.get("show_debug", True):
            # Ensure status label is visible and sized normally when debug is shown
            self.status_label.setVisible(True)
            self.status_label.setMaximumHeight(16777215)
            self.status_label.setMinimumHeight(0)
            self.status_label.setText(f"Engine Status: {current_state.get('status', '')}")
        else:
            # Fully hide and collapse the status label so it doesn't reserve layout space
            self.status_label.clear()
            self.status_label.setVisible(False)
            self.status_label.setMaximumHeight(0)
            self.status_label.setMinimumHeight(0)

        shanten_val = current_state.get('shanten')
        if shanten_val is not None:
            self.shanten_label.setText(f"Shanten: {shanten_val}")
        else:
            self.shanten_label.setText("Shanten: --")
            
        hand_data = current_state.get('hand_data', [])
        discard_filenames = current_state.get('discards', [])
        
        # Display debug vision frame
        debug_frame = current_state.get('debug_frame')
        if debug_frame is not None and self.settings.get("show_debug", True):
            self.set_debug_preview_visible(True)
            height, width, channel = debug_frame.shape
            bytesPerLine = 3 * width
            # Convert BGR to RGB for Qt displaying properly
            qImg = QImage(debug_frame.data, width, height, bytesPerLine, QImage.Format.Format_BGR888)
            pix = QPixmap.fromImage(qImg)
            # Scale it down so it fits nicely
            self.debug_label.setPixmap(pix.scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.set_debug_preview_visible(False)

        # Clear out existing labels in case they get shortened
        for ukeire_lbl, tile_lbl in self.hand_tile_widgets:
            tile_lbl.clear()
            ukeire_lbl.setText("")
            ukeire_lbl.setStyleSheet("color: limegreen; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 100); border-radius: 3px;")
        for ukeire_lbl, tile_lbl in self.tile_widgets:
            tile_lbl.clear()
            ukeire_lbl.setText("")
            ukeire_lbl.setStyleSheet("color: limegreen; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 100); border-radius: 3px;")

            
        # Update current hand
        ukeire_values = [data.get('ukeire', 0) for data in hand_data]
        max_ukeire = max(ukeire_values) if ukeire_values else 0
        min_ukeire = min([v for v in ukeire_values if v > 0], default=0)
        if hand_data:

            for idx, data in enumerate(hand_data):
                if idx < len(self.hand_tile_widgets):
                    ukeire_lbl, tile_lbl = self.hand_tile_widgets[idx]

                    pixmap = self._build_tile_pixmap(data['filename'])
                    if not pixmap.isNull():
                        tile_lbl.setPixmap(pixmap)
                        tile_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    ukeire_value = data.get('ukeire', 0)
                    if ukeire_value > 0:
                        ukeire_lbl.setText(f"{ukeire_value}")
                    else:
                        ukeire_lbl.setText("")

                    ukeire_lbl.setStyleSheet(self._ukeire_style(ukeire_value, min_ukeire, max_ukeire))
                    
        # Update best discard tiles
        if discard_filenames:
            for idx, filename in enumerate(discard_filenames):
                if idx < len(self.tile_widgets):
                    discard_data = filename if isinstance(filename, dict) else {"filename": filename, "ukeire": 0}
                    ukeire_lbl, tile_lbl = self.tile_widgets[idx]

                    pixmap = self._build_tile_pixmap(discard_data.get("filename", ""))
                    if not pixmap.isNull():
                        tile_lbl.setPixmap(pixmap)
                        tile_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        tile_lbl.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 5px; padding: 5px;")

                    discard_ukeire = discard_data.get("ukeire", 0)
                    if discard_ukeire > 0:
                        ukeire_lbl.setText(f"{discard_ukeire}")
                    else:
                        ukeire_lbl.setText("")
                    ukeire_lbl.setStyleSheet(self._ukeire_style(discard_ukeire, 0, discard_ukeire))

    def set_debug_preview_visible(self, visible: bool):
        if visible:
            self.debug_label.setVisible(True)
            self.debug_label.setMaximumHeight(theme.DEBUG_HEIGHT)
            self.debug_label.setMinimumHeight(0)
        else:
            self.debug_label.clear()
            self.debug_label.setMaximumHeight(0)
            self.debug_label.setMinimumHeight(0)
            self.debug_label.setVisible(False)

    def toggle_settings_panel(self):
        self.settings_visible = self.settings_toggle_btn.isChecked()
        if self.settings_visible:
            self.settings_panel.setVisible(True)
            self.settings_panel.setMaximumHeight(16777215)
            self.settings_panel.setMinimumHeight(0)
        else:
            self.settings_panel.setMaximumHeight(0)
            self.settings_panel.setMinimumHeight(0)
            self.settings_panel.setVisible(False)
        self._update_window_geometry()

    def _update_window_geometry(self):
        self.layout.activate()
        self.central_widget.adjustSize()
        self.adjustSize()
        self.resize(self.central_widget.sizeHint())

def run_overlay():
    app = QApplication(sys.argv)
    sys.exit(app.exec())

if __name__ == "__main__":
    run_overlay()
