import time
import threading
from Vision.VisionEngine import VisionEngine
from Logic.GameState import GameState
from Logic.LogicCalculator import LogicCalculator
from UI.UIOverlay import AssistantWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import pyqtSignal, QObject
import sys

class SignalEmitter(QObject):
    update_ui_signal = pyqtSignal(dict)

def main_loop(emitter, initial_settings):
    # Setup Logic
    state = GameState()
    calc = LogicCalculator()
    
    import os
    # We will initialize VisionEngine here and pass it the best.pt weights
    # Resolve the model path relative to this script so it works from any directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "..", "runs", "detect", "mahjong_nano_v4", "weights", "best.pt")
    vision = VisionEngine(model_path)
    
    # We will poll this shared variable
    # In a real app we'd use a thread lock, but python dict updates are atomic enough for our simple case
    current_settings = initial_settings
    
    # Provide a simple callback setter for the UI to execute
    def update_settings(new_settings):
        nonlocal current_settings
        current_settings = new_settings
    
    # Attach setter to emitter so UI thread can push data
    emitter.settings_changed = update_settings

    print("Starting Main Logic Loop...")
    while True:
        app_name = current_settings.get("app_name", "")
        crop_x = current_settings.get("crop_x", 0)
        crop_y = current_settings.get("crop_y", 0)
        crop_w = current_settings.get("crop_w", 0)
        crop_h = current_settings.get("crop_h", 0)
        debug_mode = current_settings.get("show_debug", False)
        
        window_id = vision.get_window_id(app_name)
        if not window_id:
            emitter.update_ui_signal.emit({
                "status": f"Application '{app_name}' not found.",
                "hand_data": [],
                "discards": [],
                "shanten": "--"
            })
            time.sleep(2.0)
            continue
            
        frame = vision.capture_frame(window_id, crop_x, crop_y, crop_w, crop_h)
        if frame is None:
            emitter.update_ui_signal.emit({"status": f"Failed to grab frame from '{app_name}'."})
            time.sleep(1.0)
            continue
            
        boxes, debug_frame = vision.predict(frame)
        
        state.update_from_vision(boxes, vision.model.names)
        
        # Calculate exactly how many tiles the vision engine sees in our hand
        tile_count = sum(state.hand_array)
        
        # Map the current hand regardless of turn condition so we can see what the model sees
        hand_data = []
        for index, count in enumerate(state.hand_array):
            for _ in range(count):
                hand_data.append({'filename': GameState.TILE_INDEX_TO_ASSET[index], 'ukeire': 0})
                
        if tile_count == 14:
            current_shanten = calc.calculate_shanten(state.hand_array)
            min_shanten_result, best_discards = calc.calculate_best_discards(state.hand_array)
            
            ukeire_map = dict(best_discards)
            
            hand_data = []
            for index, count in enumerate(state.hand_array):
                for _ in range(count):
                    ukeire = ukeire_map.get(index, 0)
                    hand_data.append({'filename': GameState.TILE_INDEX_TO_ASSET.get(index, ""), 'ukeire': ukeire})
            
            discard_tiles = [
                {
                    "filename": GameState.TILE_INDEX_TO_ASSET.get(tile_index, ""),
                    "ukeire": ukeire_count,
                }
                for tile_index, ukeire_count in best_discards[:3]
            ]
            
            emitter.update_ui_signal.emit({
                "status": "Locked (Turn active)",
                "shanten": current_shanten,
                "hand_data": hand_data,
                "discards": discard_tiles,
                "debug_frame": debug_frame
            })
        else:
            # We don't have 14 tiles, meaning it's someone else's turn or we're mid-animation
            if tile_count == 13:
                current_shanten = calc.calculate_shanten(state.hand_array)
            else:
                current_shanten = "--"
            emitter.update_ui_signal.emit({
                "status": f"Locked (Waiting for turn: {tile_count} tiles)",
                "shanten": current_shanten,
                "hand_data": hand_data,
                "discards": [],
                "debug_frame": debug_frame
            })
            
        time.sleep(0.5) # Rate limit

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = AssistantWindow()
    window.show()
    
    emitter = SignalEmitter()
    emitter.update_ui_signal.connect(window.update_data)
    
    # Hook the settings changed signal from UI back into the main loop via a custom attribute
    window.settings_changed_signal.connect(lambda settings: getattr(emitter, 'settings_changed', lambda s: None)(settings))
    
    backend_thread = threading.Thread(target=main_loop, args=(emitter, window.settings), daemon=True)
    backend_thread.start()
    
    sys.exit(app.exec())
