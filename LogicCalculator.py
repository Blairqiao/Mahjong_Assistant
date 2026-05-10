from mahjong.shanten import Shanten
# from mahjong.hand_calculating.hand import HandCalculator # To be used later for Yaku

class LogicCalculator:
    def __init__(self):
        self.shanten_calc = Shanten()
        # self.hand_calc = HandCalculator()
        
    def calculate_shanten(self, hand_34_array):
        """
        Returns the tiles away from tenpai.
        -1 = Tsuigou/Agari, 0 = Tenpai, 1 = 1-shanten...
        """
        return self.shanten_calc.calculate_shanten(hand_34_array)
        
    def calculate_ukeire(self, hand_34_array):
        """
        For a given imperfect hand, simulates discards to find the 
        widest tile acceptance (Ukeire).
        """
        pass
