#!/usr/bin/env python3
"""
Simple test script to generate an audiobook from an existing novella text file.
"""

import os
import sys
import time
from audio_gen import AudiobookGenerator

def print_progress(progress, current, total, final_path=None):
    """Progress callback for audiobook generation"""
    bar_length = 50
    filled_length = int(bar_length * progress / 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    sys.stdout.write(f"\r[{bar}] {progress:.1f}% - Segment {current}/{total}")
    sys.stdout.flush()
    
    if final_path:
        print(f"\n\nAudiobook completed: {final_path}")

def main():
    # Check if OpenAI API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        txt_files = [f for f in os.listdir('.') if f.endswith('.txt') 
                    and f != 'requirements.txt' and f != 'VERSION.txt']
        
        if not txt_files:
            print("No text files found in the current directory.")
            sys.exit(1)
            
        print("Available novella text files:")
        for i, file in enumerate(txt_files):
            print(f"{i+1}. {file}")
            
        selection = input("\nSelect a file number to convert to audiobook: ")
        try:
            file_index = int(selection) - 1
            if file_index < 0 or file_index >= len(txt_files):
                print("Invalid selection.")
                sys.exit(1)
            filename = txt_files[file_index]
        except ValueError:
            print("Please enter a valid number.")
            sys.exit(1)
    else:
        filename = sys.argv[1]
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)
    
    # Get the title from the filename
    title = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ')
    
    # Let user select voice
    voices = list(AudiobookGenerator.AVAILABLE_VOICES.keys())
    voice_descriptions = AudiobookGenerator.AVAILABLE_VOICES
    
    print("\nAvailable voices:")
    for i, voice in enumerate(voices):
        print(f"{i+1}. {voice} - {voice_descriptions[voice]}")
        
    voice_selection = input(f"\nSelect a voice (1-{len(voices)}) [default: nova]: ")
    
    if voice_selection.strip():
        try:
            voice_index = int(voice_selection) - 1
            if voice_index < 0 or voice_index >= len(voices):
                print("Invalid selection. Using default voice 'nova'.")
                selected_voice = "nova"
            else:
                selected_voice = voices[voice_index]
        except ValueError:
            print("Invalid input. Using default voice 'nova'.")
            selected_voice = "nova"
    else:
        selected_voice = "nova"
    
    print(f"\nConverting '{filename}' to audiobook using voice '{selected_voice}'...")
    print(f"Title: {title}")
    
    # Generate audiobook
    start_time = time.time()
    
    try:
        generator = AudiobookGenerator()
        audio_files, combined = generator.generate_chapter_by_chapter(
            filename, 
            title, 
            voice=selected_voice,
            callback=print_progress
        )
        
        elapsed = time.time() - start_time
        
        print(f"\nGeneration completed in {elapsed:.2f} seconds")
        print(f"Generated {len(audio_files)} audio segments")
        
        if combined:
            print(f"Combined audiobook saved to: {combined}")
            
            # Get filesize
            filesize = os.path.getsize(combined) / (1024 * 1024)  # Convert to MB
            print(f"Audiobook size: {filesize:.2f} MB")
            
            # Suggest how to play
            print("\nYou can play this audiobook with:")
            print(f"  mpv {combined}  # If you have mpv installed")
            print(f"  vlc {combined}  # If you have VLC installed")
        else:
            print("Failed to create combined audiobook.")
            
    except Exception as e:
        print(f"\nError generating audiobook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()