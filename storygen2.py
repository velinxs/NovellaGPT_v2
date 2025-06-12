import anthropic
import os
import argparse
import sys
import time
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def generate_novella(prompt, title=None, system_prompt=None, api_key=None):
    """
    Generate a novella using Claude 3.7 with extended thinking and output capabilities.
    
    Args:
        prompt (str): The user's prompt for the novella
        title (str, optional): Title for the novella
        system_prompt (str, optional): Custom system prompt
        api_key (str, optional): Anthropic API key
    
    Returns:
        str: The generated novella
    """
    # Use provided API key or try to get from environment
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API key not provided and ANTHROPIC_API_KEY environment variable not set")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Default system prompt if none provided
    if not system_prompt:
        system_prompt = """You are NovellaGPT, master novelist and storyteller. Your task is to ghostwrite a compelling, well-structured novella based on the user's prompt that is ready to be published. Feel free to improve the user's prompt at your own discretion.

The novella should:
- Be between 20,000-30,000,000 words. (Use All Tokens)
- Have well-developed characters with clear motivations and backstories
- Include a well-developed, interesting, , well written plot.. think it thru, avoid tropes.
- Generate a Human Ghostwriter Persona who utilizes varied sentence structures and has a dinstinct style, think of your ghostwriter's human author bio/style/backstory/personality matrix, what famous writers inspired this author? dive deep into this new writer's persona you are embodying for the novella.
- Incorporate themes that resonate with the central premise
- Balance dialogue, action, and description, etc...
- Have chapters with natural breaks and a coherent structure
- You are not confined to these instructions, they're merely suggestions. It's important that you do your best written work so plan it out entirely! It will be sold and read by many people, so we want to make sure its' the best quality.

First, create a detailed plan in your thinking tokens (30k tokens budget) only that includes (but not limited too):
1. Character profiles and relationships
2. Plot outline with major events and development notes
3. Setting details and worldbuilding elements
4. Thematic elements you want to explore
5. Timeline of events
6. Story arch
7. Ensure Engagement
8. Anything else you feel you need to think through out that would improve quality. remember you're ghostwriter.

Then use the remaining ~100k output tokens to generate the complete novella. The actual output (as opposed to thinking tokens) should entirely be a novella, as it will be directly saved to a txt file and later converted into a pdf ebook"""
    
    print("Generating novella with Claude 3.7... (this may take several minutes)")
    print("Content will stream as it's generated. Press Ctrl+C to stop at any time.")
    start_time = time.time()
    
    try:
        # Create the parameters dictionary
        params = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 128000,
            "temperature": 1,  # Must be 1 when thinking is enabled
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "thinking": {
                "type": "enabled",
                "budget_tokens": 30000
            },
            "betas": ["output-128k-2025-02-19"]
        }
        
        # Initialize an empty string to collect the streamed content
        full_content = ""
        filename = save_novella_partial("", title, initial=True)
        
        with client.beta.messages.stream(**params) as stream:
            try:
                print("\nStreaming novella content (saving chunks to file as they arrive):")
                print("-" * 50)
                # Use a buffer to collect chunks before writing to file
                buffer = ""
                chunk_size = 5000  # Characters to collect before writing
                word_count = 0
                last_update_time = time.time()
                update_interval = 5  # Update word count every 5 seconds
                
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    full_content += text
                    buffer += text
                    
                    # Update word count at intervals
                    current_time = time.time()
                    if current_time - last_update_time >= update_interval:
                        # Count words in current buffer
                        current_words = count_words(full_content)
                        # Update progress in terminal title bar
                        sys.stdout.write(f"\033]0;Generating: {title} - {current_words} words\007")
                        sys.stdout.flush()
                        last_update_time = current_time
                    
                    # When buffer reaches threshold, write to file
                    if len(buffer) >= chunk_size:
                        save_novella_partial(buffer, title)
                        buffer = ""  # Reset buffer after writing
                
                # Save any remaining text in buffer
                if buffer:
                    save_novella_partial(buffer, title)
                
                # Add final marker
                save_novella_partial("", title, final=True)
                
                # Final word count
                final_word_count = count_words(full_content)
                sys.stdout.write(f"\033]0;Completed: {title} - {final_word_count} words\007")
                sys.stdout.flush()
                
                message = stream.get_final_message()
                
                elapsed_time = time.time() - start_time
                print(f"\n\nNovella generated in {elapsed_time:.2f} seconds")
                print(f"Final word count: {final_word_count}")
                
                return message.content, title
            
            except KeyboardInterrupt:
                print("\n\nGeneration stopped by user.")
                # Save any remaining text in buffer
                if buffer:
                    save_novella_partial(buffer, title)
                
                # Add final interrupted marker
                save_novella_partial("", title, final=True, interrupted=True)
                print(f"Partial novella saved to file: {filename}")
                sys.exit(0)
    
    except Exception as e:
        print(f"Error generating novella: {e}")
        sys.exit(1)

def count_words(text):
    """Count the number of words in the text"""
    # Remove header/footer markers
    text = re.sub(r'--- NOVELLA: .*? ---\n\n', '', text)
    text = re.sub(r'\n\n--- END OF NOVELLA ---\n', '', text)
    text = re.sub(r'--- WORD COUNT: \d+ ---\n', '', text)
    text = re.sub(r'--- GENERATION INTERRUPTED BY USER ---\n', '', text)
    
    # Remove markdown formatting and other non-word characters
    text = re.sub(r'#', ' ', text)  # Replace headers with spaces
    text = re.sub(r'\*+', ' ', text)  # Remove asterisks (bold/italic)
    text = re.sub(r'_+', ' ', text)  # Remove underscores (italic)
    text = re.sub(r'```[\s\S]*?```', ' ', text)  # Remove code blocks
    text = re.sub(r'`[^`]*`', ' ', text)  # Remove inline code
    
    # Split by whitespace and count non-empty words
    # Treat hyphenated words as a single word
    words = []
    for word in re.split(r'\s+', text):
        if word:
            # Count hyphenated terms as one word
            if '-' in word and not word.startswith('-') and not word.endswith('-'):
                hyphen_parts = word.split('-')
                if all(part.isalpha() for part in hyphen_parts if part):
                    words.append(word)
                    continue
            
            # Remove punctuation from the start and end of words
            clean_word = re.sub(r'^[^\w]+|[^\w]+$', '', word)
            if clean_word:
                words.append(clean_word)
    
    return len(words)

def save_novella_partial(content, title=None, initial=False, final=False, interrupted=False):
    """Save partial novella content to a file"""
    if not title:
        title = "generated_novella"
    
    # Clean filename - replace spaces with underscores and remove special characters
    filename = "".join(c if c.isalnum() else "_" for c in title)
    filename = f"{filename}.txt"
    
    mode = "w" if initial else "a"
    
    with open(filename, mode, encoding='utf-8') as file:
        if initial:
            file.write(f"--- NOVELLA: {title} ---\n\n")
        elif final:
            # Count words in the file before adding the final marker
            with open(filename, 'r', encoding='utf-8') as read_file:
                text = read_file.read()
                word_count = count_words(text)
            
            if interrupted:
                file.write(f"\n\n--- GENERATION INTERRUPTED BY USER ---\n")
                file.write(f"--- WORD COUNT: {word_count} ---\n")
            else:
                file.write(f"\n\n--- END OF NOVELLA ---\n")
                file.write(f"--- WORD COUNT: {word_count} ---\n")
        else:
            file.write(content)
    
    return filename

def convert_to_pdf(txt_filename, title):
    """Convert a text file to PDF format"""
    # Import from separate module to avoid encoding issues
    try:
        from convert_pdf import create_ebook_pdf
        return create_ebook_pdf(txt_filename, title)
    except ImportError:
        print("Error: convert_pdf.py module not found.")
        print("Please make sure convert_pdf.py is in the same directory.")
        return None

def convert_to_epub(txt_filename, title, author="Generated with Claude 3.7"):
    """Convert a text file to EPUB format for e-readers including Amazon KDP"""
    try:
        from convert_epub import convert_to_epub
        return convert_to_epub(txt_filename, title, author)
    except ImportError:
        print("Error: convert_epub.py module not found.")
        print("Please make sure convert_epub.py is in the same directory.")
        return None

def save_novella(content, title=None, generate_epub=False, author=None):
    """Save the complete generated novella to a file"""
    if not title:
        title = "generated_novella"
    
    # Clean filename - replace spaces with underscores and remove special characters
    filename = "".join(c if c.isalnum() else "_" for c in title)
    filename = f"{filename}.txt"
    
    with open(filename, "w", encoding='utf-8') as file:
        file.write(f"--- NOVELLA: {title} ---\n\n")
        
        if isinstance(content, list):
            for item in content:
                if hasattr(item, 'text'):
                    file.write(item.text)
                elif isinstance(item, dict) and 'text' in item:
                    file.write(item['text'])
                else:
                    file.write(str(item))
        else:
            file.write(str(content))
        
        # Count words
        word_count = count_words(str(content))
        file.write("\n\n--- END OF NOVELLA ---\n")
        file.write(f"--- WORD COUNT: {word_count} ---\n")
    
    # Convert to PDF
    pdf_filename = convert_to_pdf(filename, title)
    
    # Convert to EPUB if requested
    epub_filename = None
    if generate_epub:
        if not author:
            author = "Generated with Claude 3.7"
        epub_filename = convert_to_epub(filename, title, author)
    
    return filename, pdf_filename, epub_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a novella using Claude 3.7")
    parser.add_argument("--prompt", type=str, help="Prompt for the novella")
    parser.add_argument("--title", type=str, help="Title for the novella", default=None)
    parser.add_argument("--api-key", type=str, help="Anthropic API key", default=None)
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")
    parser.add_argument("--epub", action="store_true", help="Generate EPUB format (for Amazon KDP)")
    parser.add_argument("--author", type=str, help="Author name for EPUB metadata", default="Generated with Claude 3.7")
    
    args = parser.parse_args()
    
    prompt = args.prompt
    if not prompt:
        try:
            prompt = input("Enter a prompt for your novella: ")
        except EOFError:
            print("\nNo input detected. Using default prompt.")
            prompt = "Write a captivating story with interesting characters and an unexpected twist. Generate characters etc as needed"
    
    title = args.title
    if not title:
        try:
            title = input("Enter a title for your novella (or press Enter for default): ")
            if not title:
                title = "Generated_Novella"
        except EOFError:
            print("\nNo input detected. Using default title.")
            title = "Generated_Novella"
    
    content, _ = generate_novella(prompt, title, api_key=args.api_key)
    
    # Process the generated content
    txt_filename = "".join(c if c.isalnum() else "_" for c in title) + ".txt"
    
    # Count words in the generated content
    with open(txt_filename, 'r') as file:
        text = file.read()
        word_count = count_words(text)
    
    print(f"\nNovella has been saved to '{txt_filename}'")
    print(f"Total word count: {word_count}")
    
    # Generate PDF if not disabled
    if not args.no_pdf:
        try:
            pdf_filename = convert_to_pdf(txt_filename, title)
            print(f"PDF version saved to '{pdf_filename}'")
        except Exception as e:
            print(f"Error generating PDF: {e}")
            print("The text version is still available.")
    
    # Generate EPUB if requested
    if args.epub:
        try:
            epub_filename = convert_to_epub(txt_filename, title, args.author)
            print(f"EPUB version saved to '{epub_filename}' (KDP-compatible)")
        except Exception as e:
            print(f"Error generating EPUB: {e}")
            print("The text version is still available.")
