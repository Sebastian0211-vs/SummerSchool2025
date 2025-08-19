from dataclasses import dataclass
from typing import List, Dict
import mido

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

def parse_midi(filename: str) -> Dict[int, List[Note]]:
    mid = mido.MidiFile(filename)

    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000
    tempo_changes = [(0, tempo)]


    active_notes = {}
    notes_by_channel: Dict[int, List[Note]] = {ch: [] for ch in range(16)}

    abs_tick = 0
    for msg in mid:
        abs_tick += msg.time

        if msg.type == 'set_tempo':
            tempo_changes.append((abs_tick, msg.tempo))

        elif msg.type == 'note_on' and msg.velocity > 0:
            active_notes[(msg.channel, msg.note)] = (abs_tick, msg.velocity)

        elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if key in active_notes:
                start_tick, vel_on = active_notes.pop(key)
                n = Note(
                    channel=msg.channel,
                    pitch=msg.note,
                    velocity_on=vel_on,
                    velocity_off=msg.velocity,
                    start_tick=start_tick,
                    end_tick=abs_tick,
                    start_sec=mido.tick2second(start_tick, ticks_per_beat, tempo),
                    end_sec=mido.tick2second(abs_tick, ticks_per_beat, tempo),
                )
                notes_by_channel[msg.channel].append(n)

    return notes_by_channel



notes = parse_midi("bad apple.mid")

for channel, notes_list in notes.items():
    print(f"Channel {channel}:")
    for note in notes_list:
        print(note)
    print()

