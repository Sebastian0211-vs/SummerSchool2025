from typing import List, Dict
import mido
from .models import Note


def parse_midi(filename: str) -> Dict[int, List[Note]]:
    """Parse a MIDI file and extract notes grouped by channel.

    This function reads a MIDI file, tracks active notes, and converts
    MIDI events (`note_on`, `note_off`, and `set_tempo`) into structured
    `Note` objects. Notes are grouped by their MIDI channel.

    Args:
        filename (str): Path to the MIDI file.

    Returns:
        Dict[int, List[Note]]: A dictionary mapping each channel number (0–15)
        to a list of `Note` objects extracted from the file.

    Example:
        >>> notes_by_channel = parse_midi("example.mid")
        >>> len(notes_by_channel[0])
        42
    """
    mid = mido.MidiFile(filename)

    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000  # Default tempo (microseconds per beat = 120 BPM)
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
