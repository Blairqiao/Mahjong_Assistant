import math

import cv2
import numpy as np
import Quartz
import Quartz.CoreGraphics as CG
from ultralytics import YOLO

class VisionEngine:
    def __init__(self, model_path):
        """
        Initializes the YOLO model and Quartz window capture.
        """
        self.model = YOLO(model_path)
        pass

    def get_window_id(self, app_name):
        """Finds the window ID matching the app name."""
        
        if not app_name:
            return None
            
        window_list = CG.CGWindowListCopyWindowInfo(
            CG.kCGWindowListOptionAll | CG.kCGWindowListExcludeDesktopElements,
            CG.kCGNullWindowID
        )
        for win in window_list:
            name = win.get(CG.kCGWindowName, '')
            bounds = win.get(CG.kCGWindowBounds)
            win_id = win.get(CG.kCGWindowNumber)
            
            if name.lower() == app_name.lower() and bounds and bounds['Height'] > 50 and bounds['Width'] > 50:
                return win_id
        return None

    def capture_frame(self, window_id, crop_x, crop_y, crop_w, crop_h):
        """
        Grabs a frame from the specific window via Quartz, processes it, and applies cropping.
        """
        if not window_id:
            return None

        cg_image = CG.CGWindowListCreateImage(
            CG.CGRectNull,
            CG.kCGWindowListOptionIncludingWindow,
            window_id,
            CG.kCGWindowImageBoundsIgnoreFraming
        )
        if not cg_image:
            return None
            
        width = CG.CGImageGetWidth(cg_image)
        height = CG.CGImageGetHeight(cg_image)
        bytes_per_row = CG.CGImageGetBytesPerRow(cg_image)
        
        provider = CG.CGImageGetDataProvider(cg_image)
        data = CG.CGDataProviderCopyData(provider)
        
        if not data:
            return None

        arr = np.frombuffer(data, dtype=np.uint8)
        arr = arr.reshape((height, bytes_per_row // 4, 4))
        arr = arr[:, :width, :] # Real width
        
        # Apply crop (safely)
        cx = max(0, crop_x)
        cy = max(0, crop_y)
        cw = min(width - cx, crop_w) if crop_w > 0 else width - cx
        ch = min(height - cy, crop_h) if crop_h > 0 else height - cy
        
        arr = arr[cy:cy+ch, cx:cx+cw, :]
        
        # Prevent OpenCV error (-215:Assertion failed) !_src.empty() 
        # when crop parameters shrink the box to 0 size
        if arr.size == 0:
            return None
        
        img = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        return img

    def remove_duplicates_by_distance(self,yolo_boxes, min_distance_px=20):
        """
        Filters out duplicate tiles based on physical distance,
        and returns the data in the exact same Ultralytics 'Boxes' format.
        """
        # Safety check: if no boxes were detected, just return the empty object
        if len(yolo_boxes) == 0:
            return yolo_boxes

        # 1. Get the confidence scores as a standard Python list
        confidences = yolo_boxes.conf.tolist()
        
        # 2. Pair each original index with its confidence, then sort by highest confidence
        # Example: [(index 0, conf 0.8), (index 1, conf 0.9)] -> [(1, 0.9), (0, 0.8)]
        indexed_confs = sorted(enumerate(confidences), key=lambda x: x[1], reverse=True)
        
        keep_indices = []
        kept_centers = []
        
        # 3. Loop through the sorted list
        for original_idx, _ in indexed_confs:
            # Extract the coordinates using the original index
            x1, y1, x2, y2 = yolo_boxes.xyxy[original_idx].tolist()
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            is_duplicate = False
            
            # Compare distance against already kept centers
            for kx, ky in kept_centers:
                distance = math.hypot(center_x - kx, center_y - ky)
                if distance < min_distance_px:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                keep_indices.append(original_idx)
                kept_centers.append((center_x, center_y))
                
        return yolo_boxes[keep_indices]

    def predict(self, frame):
        """
        Run the YOLO model against the current frame.
        Use agnostic NMS to prevent identical overlapping bounds across classes.
        """
        if frame is None:
            return [], None
            
        # Hardcoding confidence and iou parameters for now
        results = self.model.predict(frame, imgsz=640, conf=0.15, iou=0.25, agnostic_nms=True, verbose=False)
        
        clean_boxes = self.remove_duplicates_by_distance(results[0].boxes, min_distance_px=25)
        debug_frame = results[0].plot()    

        return clean_boxes, debug_frame

