from typing import List, Dict
import mido
from .models import Note


def parse_midi(filename: str) -> Dict[int, List[Note]]:
    """Parse a MIDI file and extract notes by channel.
    
    Args:
        filename: Path to the MIDI file
        
    Returns:
        Dictionary mapping channel numbers to lists of Note objects
    """
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
                note = Note(
                    channel=msg.channel,
                    pitch=msg.note,
                    velocity_on=vel_on,
                    velocity_off=msg.velocity,
                    start_tick=start_tick,
                    end_tick=abs_tick,
                    start_sec=mido.tick2second(start_tick, ticks_per_beat, tempo),
                    end_sec=mido.tick2second(abs_tick, ticks_per_beat, tempo),
                )
                notes_by_channel[msg.channel].append(note)

    return notes_by_channel