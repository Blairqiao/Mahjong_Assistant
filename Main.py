import time
import threading
from VisionEngine import VisionEngine
from GameState import GameState
from LogicCalculator import LogicCalculator
from UIOverlay import TransparentOverlay
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import pyqtSignal, QObject
import sys

class SignalEmitter(QObject):
    # Signals must be defined on QObject to cross threads safely into the UI
    update_ui_signal = pyqtSignal(int)  # e.g. sending shanten value

def main_loop(emitter):
    # Placeholder for the main logic loop.
    # We run this in a background thread so the PyQt UI doesn't block.
    
    # vision = VisionEngine()
    # state = GameState()
    # calc = LogicCalculator()
    
    print("Starting Main Logic Loop...")
    while True:
        # frame = vision.capture_frame()
        # raw_detections = vision.predict(frame)
        # state.update_from_vision(raw_detections)
        # current_shanten = calc.calculate_shanten(state.hand_array)
        
        # Mocking logic data
        mock_shanten = 3
        
        # safely emit to PyQt GUI thread
        emitter.update_ui_signal.emit(mock_shanten)
        
        time.sleep(1.0) # Rate limiting the inference

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = TransparentOverlay()
    overlay.show()
    
    # Setup Signal to safely jump thread boundaries
    emitter = SignalEmitter()
    emitter.update_ui_signal.connect(overlay.update_data)
    
    # Start the backend work on a separate thread
    backend_thread = threading.Thread(target=main_loop, args=(emitter,), daemon=True)
    backend_thread.start()
    
    sys.exit(app.exec())
