from dataclasses import dataclass


@dataclass
class Note:
    channel: int
    pitch: int
    velocity_on: int
    velocity_off: int
    start_tick: int
    end_tick: int
    start_sec: float
    end_sec: float

    def __str__(self):
        return (f"Note(channel={self.channel}, pitch={self.pitch}, "
                f"velocity_on={self.velocity_on}, velocity_off={self.velocity_off}, "
                f"start_tick={self.start_tick}, end_tick={self.end_tick}, "
                f"start_sec={self.start_sec:.2f}, end_sec={self.end_sec:.2f})")