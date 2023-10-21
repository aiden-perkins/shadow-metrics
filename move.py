class Move:
    def __init__(self, name, typing, power, energy_delta, damage_window_start_ms, damage_window_end_ms, duration_ms):
        self.name = name
        self.typing = typing

        self.power = power
        self.energy_delta = energy_delta

        self.damage_window_start_ms = damage_window_start_ms
        self.damage_window_end_ms = damage_window_end_ms
        self.duration_ms = duration_ms

        self.damage_window_start_s = self.damage_window_start_ms / 1000
        self.damage_window_end_s = self.damage_window_end_ms / 1000
        self.duration_s = self.duration_ms / 1000
