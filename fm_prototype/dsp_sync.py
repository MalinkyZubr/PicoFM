from math import pi


def range_wraparound(value: float, max_value: float, min_value: float) -> float:
    while value > max_value:
        value -= max_value
    while value < min_value:
        value += max_value
    
    return value


class DSPTimeSync:
    def __init__(self, sps: int):
        self.sps: int = sps
        self.time: float = 0.0
        self.time_step: float = 1.0 / self.sps
    
    def get_time(self) -> float:
        time_value: float = self.time
        self.time = range_wraparound(time_value + self.time_step, 0, 2 * pi)

        return time_value