import os
import re
import json
import time
from openai import OpenAI
from pydub import AudioSegment
import tempfile

class AudiobookGenerator:
    """Generate audiobook from novella text using OpenAI's TTS API"""
    
    # Available voices in OpenAI TTS
    AVAILABLE_VOICES = {
        "alloy": "Versatile, neutral voice",
        "echo": "Baritone, deeper voice",
        "fable": "British-accented, authoritative voice",
        "onyx": "Deep, strong male voice", 
        "nova": "Female voice with a warm tone",
        "shimmer": "Cheerful, young female voice"
    }
    
    # Default voice to use
    DEFAULT_VOICE = "nova"
    
    # Maximum characters per API call
    MAX_CHUNK_SIZE = 4000  # OpenAI TTS limit is 4096 chars
    
    def __init__(self, api_key=None):
        """
        Initialize the AudiobookGenerator with OpenAI API key
        
        Args:
            api_key (str, optional): OpenAI API key
        """
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Create directory for audio files if it doesn't exist
        os.makedirs("audio_files", exist_ok=True)
    
    def _clean_text(self, text):
        """
        Clean text to optimize for TTS
        
        Args:
            text (str): Text content to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove header/footer markers
        text = re.sub(r'--- NOVELLA: .*? ---\n\n', '', text)
        text = re.sub(r'\n\n--- END OF NOVELLA ---\n', '', text)
        text = re.sub(r'--- WORD COUNT: \d+ ---\n', '', text)
        text = re.sub(r'--- GENERATION INTERRUPTED BY USER ---\n', '', text)
        
        # Remove markdown formatting
        text = re.sub(r'#\s+(.+)', r'\1:', text)  # Convert headers to sentences with colon
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Remove italic
        text = re.sub(r'_(.+?)_', r'\1', text)  # Remove underline
        text = re.sub(r'```[\s\S]*?```', ' ', text)  # Remove code blocks
        text = re.sub(r'`[^`]*`', ' ', text)  # Remove inline code
        
        # Improve TTS readability
        text = re.sub(r'\.{3}', ' pause ', text)  # Replace ellipsis with pause cue
        text = re.sub(r'--', ', ', text)  # Replace double dash with comma pause
        text = re.sub(r'\n\n', ' \n ', text)  # Add slight pause between paragraphs
        
        return text
    
    def _split_into_chapters(self, text):
        """
        Split text into chapters based on chapter headings
        
        Args:
            text (str): Complete novella text
            
        Returns:
            list: List of chapter texts
        """
        # First clean the text
        text = self._clean_text(text)
        
        # Look for chapter markers (various formats)
        chapter_pattern = r'(?:^|\n\s*)(?:CHAPTER|Chapter)\s+(?:\d+|[IVXLCDM]+)(?:\s*:\s*|\s+)(.+?)(?=\n)'
        alt_chapter_pattern = r'(?:^|\n\s*)(?:PART|Part|BOOK|Book)\s+(?:\d+|[IVXLCDM]+)(?:\s*:\s*|\s+)(.+?)(?=\n)'
        prologue_pattern = r'(?:^|\n\s*)(?:PROLOGUE|Prologue)(?:\s*:\s*|\s+)?(.+?)?(?=\n)'
        epilogue_pattern = r'(?:^|\n\s*)(?:EPILOGUE|Epilogue)(?:\s*:\s*|\s+)?(.+?)?(?=\n)'
        
        # Combine patterns
        all_patterns = f"({chapter_pattern}|{alt_chapter_pattern}|{prologue_pattern}|{epilogue_pattern})"
        
        # Find all chapter-like divisions
        divisions = re.finditer(all_patterns, text, re.MULTILINE)
        
        # Get positions of all divisions
        positions = [0]  # Start of text
        for match in divisions:
            positions.append(match.start())
        
        # If no chapters found, split by size
        if len(positions) <= 1:
            return self._split_by_size(text)
        
        # Extract chapters
        chapters = []
        for i in range(len(positions)):
            start = positions[i]
            end = positions[i+1] if i < len(positions)-1 else len(text)
            chapter_text = text[start:end].strip()
            if chapter_text:
                chapters.append(chapter_text)
        
        return chapters
    
    def _split_by_size(self, text, target_size=3500):
        """
        Split text into chunks of approximately target_size characters,
        attempting to break at paragraph boundaries
        
        Args:
            text (str): Text to split
            target_size (int): Target size for each chunk
            
        Returns:
            list: List of text chunks
        """
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            # If adding this paragraph would exceed target size and current chunk isn't empty
            if len(current_chunk) + len(para) > target_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _further_split_if_needed(self, chunks):
        """
        Further split chunks if they exceed maximum size
        
        Args:
            chunks (list): List of text chunks
            
        Returns:
            list: List of text chunks, all below maximum size
        """
        result = []
        for chunk in chunks:
            if len(chunk) <= self.MAX_CHUNK_SIZE:
                result.append(chunk)
            else:
                # Split at sentence boundaries if possible
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > self.MAX_CHUNK_SIZE:
                        if current_chunk:
                            result.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            # This means a single sentence is too long, need to split arbitrarily
                            sentence_chunks = [sentence[i:i+self.MAX_CHUNK_SIZE] 
                                              for i in range(0, len(sentence), self.MAX_CHUNK_SIZE)]
                            result.extend(sentence_chunks)
                    else:
                        current_chunk += (" " if current_chunk else "") + sentence
                
                if current_chunk:
                    result.append(current_chunk.strip())
        
        return result
    
    def generate_audio_for_text(self, text, voice=None, output_file=None):
        """
        Generate audio for a single text chunk
        
        Args:
            text (str): Text content to convert to speech
            voice (str, optional): Voice to use for TTS
            output_file (str, optional): Output MP3 file path
            
        Returns:
            str: Path to the generated audio file
        """
        if not voice or voice not in self.AVAILABLE_VOICES:
            voice = self.DEFAULT_VOICE
        
        if not output_file:
            # Create a temporary file if no output file specified
            fd, output_file = tempfile.mkstemp(suffix=".mp3", dir="audio_files")
            os.close(fd)
        
        try:
            response = self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            # Save the audio file
            response.stream_to_file(output_file)
            return output_file
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    def generate_audiobook(self, txt_filename, title, voice=None):
        """
        Generate complete audiobook from a novella text file
        
        Args:
            txt_filename (str): Path to text file
            title (str): Title of the novella
            voice (str, optional): Voice to use for TTS
            
        Returns:
            tuple: (List of chapter audio files, combined audiobook file)
        """
        # Clean the title for filenames
        clean_title = ''.join(c if c.isalnum() else '_' for c in title)
        
        # Create directory for this audiobook if it doesn't exist
        audiobook_dir = os.path.join("audio_files", clean_title)
        os.makedirs(audiobook_dir, exist_ok=True)
        
        # Read the text file
        with open(txt_filename, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Split into chapters
        chapters = self._split_into_chapters(text)
        
        # Further split chapters if needed to stay under API limits
        print(f"Splitting novella into {len(chapters)} chapters or segments...")
        chapters = [self._further_split_if_needed([chapter]) for chapter in chapters]
        # Flatten the list of lists
        chapters = [chunk for sublist in chapters for chunk in sublist]
        
        # Keep track of all generated audio files
        audio_files = []
        combined = None
        
        try:
            print(f"Generating audio for {len(chapters)} segments...")
            
            # Process each chapter
            for i, chapter_text in enumerate(chapters):
                print(f"Generating audio for segment {i+1}/{len(chapters)}...")
                
                # Generate audio file for this chapter
                chapter_filename = os.path.join(audiobook_dir, f"chapter_{i+1:03d}.mp3")
                audio_file = self.generate_audio_for_text(
                    chapter_text, 
                    voice=voice,
                    output_file=chapter_filename
                )
                
                if audio_file:
                    audio_files.append(audio_file)
                    print(f"Generated {audio_file}")
                    
                    # Introduce a small delay between API calls to avoid rate limits
                    time.sleep(0.5)
            
            # Combine all audio files into a single audiobook
            if audio_files:
                combined_file = os.path.join("audio_files", f"{clean_title}_audiobook.mp3")
                combined = self._combine_audio_files(audio_files, combined_file)
                print(f"Combined audiobook saved to {combined}")
            
            return audio_files, combined
            
        except Exception as e:
            print(f"Error generating audiobook: {e}")
            return audio_files, combined
    
    def _combine_audio_files(self, audio_files, output_file):
        """
        Combine multiple audio files into a single file
        
        Args:
            audio_files (list): List of audio file paths
            output_file (str): Output file path
            
        Returns:
            str: Path to the combined audio file
        """
        if not audio_files:
            return None
        
        try:
            # Start with the first file
            combined = AudioSegment.from_mp3(audio_files[0])
            
            # Add a short silence between chapters (500ms)
            silence = AudioSegment.silent(duration=500)
            
            # Add the rest of the files
            for audio_file in audio_files[1:]:
                segment = AudioSegment.from_mp3(audio_file)
                combined += silence + segment
            
            # Export the combined file
            combined.export(output_file, format="mp3")
            return output_file
            
        except Exception as e:
            print(f"Error combining audio files: {e}")
            return None
    
    def generate_chapter_by_chapter(self, txt_filename, title, voice=None, callback=None):
        """
        Generate audiobook chapter by chapter with callback updates
        
        Args:
            txt_filename (str): Path to text file
            title (str): Title of the novella
            voice (str, optional): Voice to use for TTS
            callback (function, optional): Callback function to report progress
            
        Returns:
            tuple: (List of chapter audio files, combined audiobook file)
        """
        # Clean the title for filenames
        clean_title = ''.join(c if c.isalnum() else '_' for c in title)
        
        # Create directory for this audiobook if it doesn't exist
        audiobook_dir = os.path.join("audio_files", clean_title)
        os.makedirs(audiobook_dir, exist_ok=True)
        
        # Read the text file
        with open(txt_filename, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Split into chapters
        chapters = self._split_into_chapters(text)
        total_chapters = len(chapters)
        
        # Further split chapters if needed
        processed_chapters = []
        for chapter in chapters:
            # Split if needed
            chunks = self._further_split_if_needed([chapter])
            processed_chapters.extend(chunks)
        
        total_segments = len(processed_chapters)
        
        # Keep track of all generated audio files
        audio_files = []
        
        # Process all chapters with progress reporting
        for i, segment_text in enumerate(processed_chapters):
            # Update progress through callback
            if callback:
                progress = (i / total_segments) * 100
                callback(progress, i+1, total_segments)
            
            # Generate audio file for this segment
            segment_filename = os.path.join(audiobook_dir, f"segment_{i+1:03d}.mp3")
            audio_file = self.generate_audio_for_text(
                segment_text, 
                voice=voice,
                output_file=segment_filename
            )
            
            if audio_file:
                audio_files.append(audio_file)
                # Small delay between API calls
                time.sleep(0.5)
        
        # Combine all audio files after generation is complete
        combined_file = None
        if audio_files:
            combined_file = os.path.join("audio_files", f"{clean_title}_audiobook.mp3")
            combined_file = self._combine_audio_files(audio_files, combined_file)
            
            # Final callback with 100% progress
            if callback:
                callback(100, total_segments, total_segments, combined_file)
        
        return audio_files, combined_file


# For direct testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python audio_gen.py <input_txt_file> <title> [voice]")
        sys.exit(1)
        
    txt_filename = sys.argv[1]
    title = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        generator = AudiobookGenerator()
        audio_files, combined = generator.generate_audiobook(txt_filename, title, voice)
        
        if combined:
            print(f"Audiobook created: {combined}")
        else:
            print("Failed to create complete audiobook, but some chapter files may have been generated.")
    except Exception as e:
        print(f"Error creating audiobook: {e}")