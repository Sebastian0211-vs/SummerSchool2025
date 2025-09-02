import mido
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

@dataclass
class Note:
    """Represents a musical note with timing and pitch information."""
    pitch: int
    start_time: float
    end_time: float
    velocity: int
    channel: int

class MIDIComparator:
    """
    A class to compare two MIDI files and analyze note and time accuracy.
    """
    
    def __init__(self, reference_file: str, test_file: str):
        self.reference_file = reference_file
        self.test_file = test_file
        self.reference_notes = []
        self.test_notes = []
        
    def extract_notes(self, midi_file: str) -> List[Note]:
        """Extract note information from a MIDI file."""
        notes = []
        
        try:
            mid = mido.MidiFile(midi_file)
            
            # Convert delta time to absolute time and extract notes
            for track_idx, track in enumerate(mid.tracks):
                current_time = 0.0
                active_notes = {}  # key: (note, channel), value: note start info
                
                for msg in track:
                    # Convert MIDI ticks to seconds
                    current_time += mido.tick2second(msg.time, mid.ticks_per_beat, 500000)  # Default tempo
                    
                    if hasattr(msg, 'note'):  # Only process note messages
                        if msg.type == 'note_on' and msg.velocity > 0:
                            # Note starts
                            key = (msg.note, msg.channel)
                            active_notes[key] = {
                                'start_time': current_time,
                                'velocity': msg.velocity
                            }
                        
                        elif (msg.type == 'note_off' or 
                              (msg.type == 'note_on' and msg.velocity == 0)):
                            # Note ends
                            key = (msg.note, msg.channel)
                            if key in active_notes:
                                note_info = active_notes.pop(key)
                                # Only add notes with positive duration
                                if current_time > note_info['start_time']:
                                    notes.append(Note(
                                        pitch=msg.note,
                                        start_time=note_info['start_time'],
                                        end_time=current_time,
                                        velocity=note_info['velocity'],
                                        channel=msg.channel
                                    ))
                    
                    # Handle tempo changes for more accurate timing
                    elif msg.type == 'set_tempo':
                        # This would require more complex tempo tracking
                        # For now, we'll use the default tempo
                        pass
                
                # Handle any remaining active notes (notes that didn't get note_off)
                for key, note_info in active_notes.items():
                    notes.append(Note(
                        pitch=key[0],
                        start_time=note_info['start_time'],
                        end_time=current_time + 0.1,  # Add small default duration
                        velocity=note_info['velocity'],
                        channel=key[1]
                    ))
            
        except Exception as e:
            print(f"Error reading MIDI file {midi_file}: {e}")
            print(f"Exception details: {type(e).__name__}: {str(e)}")
            return []
        
        # Sort notes by start time
        notes.sort(key=lambda x: x.start_time)
        print(f"Extracted {len(notes)} notes from {midi_file}")
        
        # Debug: Print first few notes
        if notes:
            print(f"First note: pitch={notes[0].pitch}, start={notes[0].start_time:.3f}s, duration={notes[0].end_time - notes[0].start_time:.3f}s")
        
        return notes
    
    def load_files(self):
        """Load and extract notes from both MIDI files."""
        print("Loading reference file...")
        self.reference_notes = self.extract_notes(self.reference_file)
        print(f"Found {len(self.reference_notes)} notes in reference file")
        
        print("Loading test file...")
        self.test_notes = self.extract_notes(self.test_file)
        print(f"Found {len(self.test_notes)} notes in test file")
    
    def find_matching_notes(self, time_tolerance: float = 0.1, 
                           pitch_tolerance: int = 0) -> List[Tuple[int, int, float]]:
        """
        Find matching notes between reference and test files.
        
        Args:
            time_tolerance: Maximum time difference (in seconds) to consider notes matching
            pitch_tolerance: Maximum pitch difference (in semitones) to consider notes matching
        
        Returns:
            List of tuples (ref_idx, test_idx, time_error)
        """
        matches = []
        used_test_indices = set()
        
        for ref_idx, ref_note in enumerate(self.reference_notes):
            best_match = None
            best_score = float('inf')
            
            for test_idx, test_note in enumerate(self.test_notes):
                if test_idx in used_test_indices:
                    continue
                
                # Check pitch match
                pitch_diff = abs(ref_note.pitch - test_note.pitch)
                if pitch_diff > pitch_tolerance:
                    continue
                
                # Check time match
                time_diff = abs(ref_note.start_time - test_note.start_time)
                if time_diff > time_tolerance:
                    continue
                
                # Calculate combined score (weighted by time difference)
                score = time_diff + (pitch_diff * 0.01)  # Pitch is less important for matching
                
                if score < best_score:
                    best_score = score
                    best_match = (test_idx, time_diff)
            
            if best_match:
                test_idx, time_error = best_match
                matches.append((ref_idx, test_idx, time_error))
                used_test_indices.add(test_idx)
        
        return matches
    
    def calculate_note_accuracy(self, matches: List[Tuple[int, int, float]]) -> Dict:
        """Calculate note detection accuracy metrics."""
        total_reference_notes = len(self.reference_notes)
        total_test_notes = len(self.test_notes)
        matched_notes = len(matches)
        
        # True Positives: correctly detected notes
        true_positives = matched_notes
        
        # False Negatives: missed notes (in reference but not detected)
        false_negatives = total_reference_notes - matched_notes
        
        # False Positives: extra notes (detected but not in reference)
        false_positives = total_test_notes - matched_notes
        
        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'total_reference_notes': total_reference_notes,
            'total_test_notes': total_test_notes,
            'matched_notes': matched_notes,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
    
    def calculate_timing_accuracy(self, matches: List[Tuple[int, int, float]]) -> Dict:
        """Calculate timing accuracy metrics."""
        if not matches:
            return {'mean_timing_error': 0, 'std_timing_error': 0, 'timing_errors': []}
        
        timing_errors = [error for _, _, error in matches]
        
        return {
            'mean_timing_error': np.mean(timing_errors),
            'std_timing_error': np.std(timing_errors),
            'max_timing_error': np.max(timing_errors),
            'min_timing_error': np.min(timing_errors),
            'timing_errors': timing_errors
        }
    
    def calculate_pitch_accuracy(self, matches: List[Tuple[int, int, float]]) -> Dict:
        """Calculate pitch accuracy metrics."""
        if not matches:
            return {'pitch_accuracy': 0, 'pitch_errors': []}
        
        pitch_errors = []
        correct_pitches = 0
        
        for ref_idx, test_idx, _ in matches:
            ref_pitch = self.reference_notes[ref_idx].pitch
            test_pitch = self.test_notes[test_idx].pitch
            pitch_error = abs(ref_pitch - test_pitch)
            pitch_errors.append(pitch_error)
            
            if pitch_error == 0:
                correct_pitches += 1
        
        pitch_accuracy = correct_pitches / len(matches) if matches else 0
        
        return {
            'pitch_accuracy': pitch_accuracy,
            'mean_pitch_error': np.mean(pitch_errors),
            'std_pitch_error': np.std(pitch_errors),
            'pitch_errors': pitch_errors
        }
    
    def analyze_duration_accuracy(self, matches: List[Tuple[int, int, float]]) -> Dict:
        """Analyze note duration accuracy."""
        if not matches:
            return {'mean_duration_error': 0, 'duration_errors': []}
        
        duration_errors = []
        
        for ref_idx, test_idx, _ in matches:
            ref_duration = self.reference_notes[ref_idx].end_time - self.reference_notes[ref_idx].start_time
            test_duration = self.test_notes[test_idx].end_time - self.test_notes[test_idx].start_time
            duration_error = abs(ref_duration - test_duration)
            duration_errors.append(duration_error)
        
        return {
            'mean_duration_error': np.mean(duration_errors),
            'std_duration_error': np.std(duration_errors),
            'duration_errors': duration_errors
        }
    
    def generate_comparison_report(self, time_tolerance: float = 0.1, 
                                 pitch_tolerance: int = 0) -> Dict:
        """
        Generate a comprehensive comparison report.
        
        Args:
            time_tolerance: Time tolerance for matching notes (seconds)
            pitch_tolerance: Pitch tolerance for matching notes (semitones)
        
        Returns:
            Dictionary containing all comparison metrics
        """
        # Load files if not already loaded
        if not self.reference_notes or not self.test_notes:
            self.load_files()
        
        # Find matching notes
        matches = self.find_matching_notes(time_tolerance, pitch_tolerance)
        
        # Calculate various accuracy metrics
        note_accuracy = self.calculate_note_accuracy(matches)
        timing_accuracy = self.calculate_timing_accuracy(matches)
        pitch_accuracy = self.calculate_pitch_accuracy(matches)
        duration_accuracy = self.analyze_duration_accuracy(matches)
        
        # Combine all results
        report = {
            'matching_parameters': {
                'time_tolerance': time_tolerance,
                'pitch_tolerance': pitch_tolerance
            },
            'note_detection': note_accuracy,
            'timing_accuracy': timing_accuracy,
            'pitch_accuracy': pitch_accuracy,
            'duration_accuracy': duration_accuracy,
            'matches': matches
        }
        
        return report
    
    def print_summary(self, report: Dict):
        """Print a human-readable summary of the comparison results."""
        print("\n" + "="*60)
        print("MIDI COMPARISON REPORT")
        print("="*60)
        
        note_det = report['note_detection']
        timing = report['timing_accuracy']
        pitch = report['pitch_accuracy']
        duration = report['duration_accuracy']
        
        print(f"\n📊 NOTE DETECTION ACCURACY:")
        print(f"   Reference notes: {note_det['total_reference_notes']}")
        print(f"   Test notes: {note_det['total_test_notes']}")
        print(f"   Matched notes: {note_det['matched_notes']}")
        print(f"   Precision: {note_det['precision']:.3f} ({note_det['precision']*100:.1f}%)")
        print(f"   Recall: {note_det['recall']:.3f} ({note_det['recall']*100:.1f}%)")
        print(f"   F1-Score: {note_det['f1_score']:.3f}")
        print(f"   False Positives: {note_det['false_positives']}")
        print(f"   False Negatives: {note_det['false_negatives']}")
        
        print(f"\n⏱️  TIMING ACCURACY:")
        if timing['timing_errors']:
            print(f"   Mean timing error: {timing['mean_timing_error']:.4f}s")
            print(f"   Std timing error: {timing['std_timing_error']:.4f}s")
            print(f"   Max timing error: {timing['max_timing_error']:.4f}s")
            print(f"   Min timing error: {timing['min_timing_error']:.4f}s")
        else:
            print("   No timing data available (no matches found)")
        
        print(f"\n🎵 PITCH ACCURACY:")
        if pitch['pitch_errors']:
            print(f"   Pitch accuracy: {pitch['pitch_accuracy']:.3f} ({pitch['pitch_accuracy']*100:.1f}%)")
            print(f"   Mean pitch error: {pitch['mean_pitch_error']:.2f} semitones")
            print(f"   Std pitch error: {pitch['std_pitch_error']:.2f} semitones")
        else:
            print("   No pitch data available (no matches found)")
        
        print(f"\n⏳ DURATION ACCURACY:")
        if duration['duration_errors']:
            print(f"   Mean duration error: {duration['mean_duration_error']:.4f}s")
            print(f"   Std duration error: {duration['std_duration_error']:.4f}s")
        else:
            print("   No duration data available (no matches found)")
        
        # Overall assessment
        overall_score = (note_det['f1_score'] + pitch['pitch_accuracy']) / 2
        print(f"\n🎯 OVERALL ACCURACY SCORE: {overall_score:.3f} ({overall_score*100:.1f}%)")
        
        if overall_score >= 0.9:
            print("   Assessment: Excellent conversion quality! 🎉")
        elif overall_score >= 0.7:
            print("   Assessment: Good conversion quality 👍")
        elif overall_score >= 0.5:
            print("   Assessment: Moderate conversion quality ⚠️")
        else:
            print("   Assessment: Conversion needs improvement 🔧")
    
    def plot_comparison_charts(self, report: Dict):
        """Generate visualization charts for the comparison results."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('MIDI Conversion Analysis', fontsize=16, fontweight='bold')
        
        # 1. Note Detection Metrics (Bar Chart)
        ax1 = axes[0, 0]
        note_det = report['note_detection']
        metrics = ['Precision', 'Recall', 'F1-Score']
        values = [note_det['precision'], note_det['recall'], note_det['f1_score']]
        bars = ax1.bar(metrics, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_ylim(0, 1)
        ax1.set_ylabel('Score')
        ax1.set_title('Note Detection Accuracy')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # 2. Timing Error Distribution (Histogram)
        ax2 = axes[0, 1]
        timing = report['timing_accuracy']
        if timing['timing_errors']:
            ax2.hist(timing['timing_errors'], bins=20, color='#96CEB4', alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Timing Error (seconds)')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Timing Error Distribution')
            ax2.axvline(timing['mean_timing_error'], color='red', linestyle='--', 
                       label=f'Mean: {timing["mean_timing_error"]:.4f}s')
            ax2.legend()
        else:
            ax2.text(0.5, 0.5, 'No timing data\navailable', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=12)
            ax2.set_title('Timing Error Distribution')
        
        # 3. Pitch Error Distribution (Histogram)
        ax3 = axes[1, 0]
        pitch = report['pitch_accuracy']
        if pitch['pitch_errors']:
            ax3.hist(pitch['pitch_errors'], bins=max(1, len(set(pitch['pitch_errors']))), 
                    color='#FECA57', alpha=0.7, edgecolor='black')
            ax3.set_xlabel('Pitch Error (semitones)')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Pitch Error Distribution')
        else:
            ax3.text(0.5, 0.5, 'No pitch data\navailable', ha='center', va='center',
                    transform=ax3.transAxes, fontsize=12)
            ax3.set_title('Pitch Error Distribution')
        
        # 4. Note Count Comparison (Bar Chart)
        ax4 = axes[1, 1]
        categories = ['Reference', 'Test', 'Matched']
        counts = [note_det['total_reference_notes'], note_det['total_test_notes'], note_det['matched_notes']]
        bars = ax4.bar(categories, counts, color=['#A8E6CF', '#FFB3BA', '#B3B3FF'])
        ax4.set_ylabel('Number of Notes')
        ax4.set_title('Note Count Comparison')
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                    f'{count}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
    
    def save_detailed_analysis(self, report: Dict, output_file: str = 'midi_comparison_report.txt'):
        """Save detailed analysis to a text file."""
        with open(output_file, 'w') as f:
            f.write("DETAILED MIDI COMPARISON ANALYSIS\n")
            f.write("="*50 + "\n\n")
            
            f.write("FILES COMPARED:\n")
            f.write(f"Reference: {self.reference_file}\n")
            f.write(f"Test: {self.test_file}\n\n")
            
            # Note detection details
            note_det = report['note_detection']
            f.write("NOTE DETECTION ANALYSIS:\n")
            f.write(f"Reference notes: {note_det['total_reference_notes']}\n")
            f.write(f"Test notes: {note_det['total_test_notes']}\n")
            f.write(f"Matched notes: {note_det['matched_notes']}\n")
            f.write(f"Precision: {note_det['precision']:.4f}\n")
            f.write(f"Recall: {note_det['recall']:.4f}\n")
            f.write(f"F1-Score: {note_det['f1_score']:.4f}\n\n")
            
            # Timing analysis
            timing = report['timing_accuracy']
            f.write("TIMING ANALYSIS:\n")
            if timing['timing_errors']:
                f.write(f"Mean timing error: {timing['mean_timing_error']:.6f}s\n")
                f.write(f"Std timing error: {timing['std_timing_error']:.6f}s\n")
                f.write(f"Max timing error: {timing['max_timing_error']:.6f}s\n")
                f.write(f"Min timing error: {timing['min_timing_error']:.6f}s\n\n")
            
            # Pitch analysis
            pitch = report['pitch_accuracy']
            f.write("PITCH ANALYSIS:\n")
            if pitch['pitch_errors']:
                f.write(f"Pitch accuracy: {pitch['pitch_accuracy']:.4f}\n")
                f.write(f"Mean pitch error: {pitch['mean_pitch_error']:.4f} semitones\n")
                f.write(f"Std pitch error: {pitch['std_pitch_error']:.4f} semitones\n")
        
        print(f"Detailed analysis saved to {output_file}")

def compare_midi_files(reference_file: str, test_file: str, 
                      time_tolerance: float = 0.1, pitch_tolerance: int = 0,
                      show_plots: bool = True, save_report: bool = True):
    """
    Main function to compare two MIDI files.
    
    Args:
        reference_file: Path to the reference MIDI file
        test_file: Path to the test MIDI file
        time_tolerance: Time tolerance for matching notes (seconds)
        pitch_tolerance: Pitch tolerance for matching notes (semitones)
        show_plots: Whether to display visualization plots
        save_report: Whether to save detailed report to file
    
    Returns:
        Dictionary containing comparison results
    """
    
    comparator = MIDIComparator(reference_file, test_file)
    comparator.load_files()
    
    # Generate comparison report
    report = comparator.generate_comparison_report(time_tolerance, pitch_tolerance)
    
    # Print summary
    comparator.print_summary(report)
    
    # Generate plots if requested
    if show_plots:
        try:
            comparator.plot_comparison_charts(report)
        except Exception as e:
            print(f"Could not generate plots: {e}")
    
    # Save detailed report if requested
    if save_report:
        comparator.save_detailed_analysis(report)
    
    return report

# Example usage
if __name__ == "__main__":
    # Example usage - replace with your file paths
    reference_midi = "reference.mid"  # Original/ground truth MIDI
    test_midi = "converted.mid"       # Your converted MIDI
    
    # Run comparison with default settings
    results = compare_midi_files(
        reference_file=reference_midi,
        test_file=test_midi,
        time_tolerance=0.1,  # 100ms tolerance
        pitch_tolerance=0,   # Exact pitch match required
        show_plots=True,
        save_report=True
    )
    
    # You can also access specific metrics
    print(f"\nOverall F1-Score: {results['note_detection']['f1_score']:.3f}")
    print(f"Pitch Accuracy: {results['pitch_accuracy']['pitch_accuracy']:.3f}")
    print(f"Mean Timing Error: {results['timing_accuracy']['mean_timing_error']:.4f}s")