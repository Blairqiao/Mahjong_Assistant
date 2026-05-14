class GameState:
    # A mapping from the 34-array index to the actual tile asset filenames
    TILE_INDEX_TO_ASSET = {
        # Man (0-8)
        0: "Man1.png", 1: "Man2.png", 2: "Man3.png", 3: "Man4.png", 4: "Man5.png",
        5: "Man6.png", 6: "Man7.png", 7: "Man8.png", 8: "Man9.png", 
        # Pin (9-17)
        9: "Pin1.png", 10: "Pin2.png", 11: "Pin3.png", 12: "Pin4.png", 13: "Pin5.png",
        14: "Pin6.png", 15: "Pin7.png", 16: "Pin8.png", 17: "Pin9.png", 
        # Sou (18-26)
        18: "Sou1.png", 19: "Sou2.png", 20: "Sou3.png", 21: "Sou4.png", 22: "Sou5.png",
        23: "Sou6.png", 24: "Sou7.png", 25: "Sou8.png", 26: "Sou9.png",
        # Honors (27-33)
        27: "Ton.png",     # East
        28: "Nan.png",     # South
        29: "Shaa.png",    # West
        30: "Pei.png",     # North
        31: "Haku.png",    # White
        32: "Hatsu.png",   # Green
        33: "Chun.png"     # Red
    }

    def __init__(self):
        # A 34-length array where the index corresponds to a tile type, and the value is the count.
        # 0-8: Man, 9-17: Pin, 18-26: Sou, 27-33: Honors (East, South, West, North, Haku, Hatsu, Chun)
        self.hand_array = [0] * 34
        
        # Additional state required for full Mahjong logic
        self.dora_indicators = []
        self.pond = []
        
        self.round_wind = 27  # Default East
        self.seat_wind = 27   # Default East

    def update_from_vision(self, boxes, yolo_names):
        """
        Translates raw YOLO bounding box detections into structured game domains
        by looking at the spatial layout (e.g. Y-coordinates for player hand).
        """
        self.hand_array = [0] * 34
        
        if boxes is None:
            return
            
        cls_array = boxes.cls.cpu().numpy()
        for i in range(len(cls_array)):
            class_id = int(cls_array[i])
            class_name = yolo_names.get(class_id)
            if not class_name:
                continue
                
            suit = class_name[-1] # 'm', 'p', 's', 'z'
            rank = int(class_name[0]) # 0-9
            
            # Convert normal 1-9 to index 0-8 for m,p,s
            if rank == 0:
                rank = 5 # Red fives count as 5
            
            idx = -1
            if suit == 'm':
                idx = rank - 1
            elif suit == 'p':
                idx = rank - 1 + 9
            elif suit == 's':
                idx = rank - 1 + 18
            elif suit == 'z':
                idx = rank - 1 + 27
                
            if 0 <= idx < 34 and self.hand_array[idx] < 4:
                self.hand_array[idx] += 1

    def generate_test_hand(self):
        """
        Creates a semi-random 14-tile test hand array for logic testing.
        Includes 1-3 completed sets (triplets/runs) and 1-2 one-off sets.
        """
        # Reset hand
        self.hand_array = [0] * 34
        
        self.hand_array[2] += 1
        self.hand_array[3] += 1
        self.hand_array[4] += 1
        self.hand_array[5] += 1

        self.hand_array[8] += 1

        self.hand_array[10] += 1
        self.hand_array[11] += 1
        self.hand_array[16] += 1
        
        self.hand_array[21] += 1
        self.hand_array[23] += 1

        self.hand_array[27] += 2

        self.hand_array[29] += 1
        self.hand_array[30] += 1


        
