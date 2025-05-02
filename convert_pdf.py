import re
import time
import textwrap
from fpdf import FPDF

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

def create_ebook_pdf(txt_filename, title):
    """Create a professional ebook-style PDF from a text file"""
    pdf_filename = txt_filename.replace('.txt', '.pdf')
    
    # Read the text content
    with open(txt_filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove header and footer markers for PDF
    content = re.sub(r'--- NOVELLA: .*? ---\n\n', '', content)
    content = re.sub(r'\n\n--- END OF NOVELLA ---\n', '', content)
    content = re.sub(r'--- WORD COUNT: \d+ ---\n', '', content)
    
    # Replace special characters that might cause encoding issues
    content = content.replace('—', '-')  # Em dash
    content = content.replace('–', '-')  # En dash
    content = content.replace('"', '"')  # Fancy quotes
    content = content.replace('"', '"')  # Fancy quotes
    content = content.replace(''', "'")  # Fancy apostrophe
    content = content.replace(''', "'")  # Fancy apostrophe
    content = content.replace('…', '...')  # Ellipsis
    
    # Create custom PDF class to handle headers and footers
    class EbookPDF(FPDF):
        def __init__(self, title):
            super().__init__()
            self.title = title
            self.chapter_pages = []
            # Set document information
            self.set_title(title)
            self.set_author('Generated with Claude 3.7')
            
        def header(self):
            # Skip header on first page (title page) and chapter start pages
            if self.page_no() == 1 or self.page_no() in self.chapter_pages:
                return
            # Regular header with more spacing
            self.set_y(10)  # Set position from top
            self.set_font('Times', 'I', 9)
            self.cell(0, 10, self.title, 0, 0, 'R')  # Right-aligned
            self.ln(10)  # Extra space after header
            
        def footer(self):
            # Skip footer on title page
            if self.page_no() == 1:
                return
            # Position at 2 cm from bottom (increased from 1.5)
            self.set_y(-20)
            self.set_font('Times', 'I', 9)
            # Page number
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    # Initialize PDF with UTF-8 support and better margins
    pdf = EbookPDF(title)
    pdf.set_font('Arial', '', 12)
    # Set larger margins (left, top, right) in mm - default was too narrow
    pdf.set_margins(25, 20, 25)  
    pdf.set_auto_page_break(auto=True, margin=25)
    
    # Add title page
    pdf.add_page()
    
    # Title
    pdf.set_font('Times', 'B', 24)
    pdf.ln(60)
    pdf.cell(0, 20, title, 0, 1, 'C')
    
    # Author line (using Claude as ghostwriter)
    pdf.set_font('Times', 'I', 14)
    pdf.ln(10)
    pdf.cell(0, 10, 'Generated with Claude 3.7', 0, 1, 'C')
    
    # Date
    pdf.set_font('Times', '', 12)
    pdf.ln(10)
    current_date = time.strftime("%B %d, %Y")
    pdf.cell(0, 10, current_date, 0, 1, 'C')
    
    # Process content by cleaning non-ASCII characters
    # Convert all non-ASCII characters to their closest ASCII equivalents or remove them
    cleaned_content = ""
    for char in content:
        if ord(char) < 128:
            cleaned_content += char
        else:
            # Replace with space or similar ASCII character
            cleaned_content += ' '
    
    # Split into paragraphs
    paragraphs = cleaned_content.split('\n\n')
    in_chapter = False
    
    # Start content on new page
    pdf.add_page()
    
    for paragraph in paragraphs:
        # Skip empty paragraphs
        if not paragraph.strip():
            continue
            
        # Check if it's a chapter header
        chapter_match = re.match(r'^#+\s+(CHAPTER\s+\d+|CHAPTER\s+[IVXLCDM]+|PROLOGUE|EPILOGUE|INTRODUCTION|PART\s+\d+|PART\s+[IVXLCDM]+).*', paragraph, re.IGNORECASE)
        
        if chapter_match or paragraph.strip().startswith('# '):
            # Start a new chapter
            pdf.add_page()
            pdf.chapter_pages.append(pdf.page_no())
            
            # Get chapter title
            chapter_title = paragraph.strip('#').strip()
            
            # Add chapter title
            pdf.set_font('Times', 'B', 18)
            pdf.ln(40)
            pdf.cell(0, 20, chapter_title, 0, 1, 'C')
            pdf.ln(20)
            
            # Reset to normal font
            pdf.set_font('Times', '', 12)
            in_chapter = True
            continue
        
        # Handle section headers (## or ###)
        if paragraph.strip().startswith('## ') or paragraph.strip().startswith('### '):
            header_level = paragraph.count('#', 0, paragraph.find(' '))
            header_text = paragraph.strip('#').strip()
            
            pdf.ln(5)
            if header_level == 2:
                pdf.set_font('Times', 'B', 14)
            else:
                pdf.set_font('Times', 'B', 12)
                
            pdf.multi_cell(0, 10, header_text)
            pdf.ln(5)
            pdf.set_font('Times', '', 12)
            continue
        
        # Regular paragraph
        pdf.set_font('Times', '', 12)
        
        # First paragraph in chapter gets a drop cap if it's longer than 100 chars
        if in_chapter and len(paragraph) > 100:
            # Extract first character for drop cap
            first_char = paragraph[0]
            rest_of_paragraph = paragraph[1:]
            
            # Add drop cap
            pdf.set_font('Times', 'B', 24)
            pdf.cell(10, 10, first_char)
            
            # Continue with rest of paragraph
            pdf.set_font('Times', '', 12)
            
            # Calculate width of first character to position rest of text
            first_char_width = pdf.get_string_width(first_char) + 2
            
            # Wrap text to fit page width minus drop cap width (reduced width for better margins)
            lines = textwrap.wrap(rest_of_paragraph, width=60)
            
            # First line positioned next to drop cap
            if lines:
                pdf.set_x(pdf.get_x() + 2)
                pdf.cell(0, 10, lines[0])
                pdf.ln(7)  # Increased line spacing
                
                # Rest of lines with normal indentation
                for line in lines[1:]:
                    pdf.multi_cell(0, 10, line)
            
            in_chapter = False  # Only apply drop cap to first paragraph
        else:
            # Normal paragraph formatting
            # Add consistent paragraph indentation
            pdf.set_x(pdf.get_x() + 10)
            
            # Wrap text to fit page width (reduced width for better margins)
            lines = textwrap.wrap(paragraph, width=60)
            for i, line in enumerate(lines):
                pdf.multi_cell(0, 10, line)
        
        pdf.ln(7)  # Increased space between paragraphs for better readability
    
    # Save the pdf
    pdf.output(pdf_filename)
    return pdf_filename

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python convert_pdf.py <input_txt_file> <title>")
        sys.exit(1)
        
    txt_filename = sys.argv[1]
    title = sys.argv[2]
    
    try:
        pdf_filename = create_ebook_pdf(txt_filename, title)
        print(f"PDF created: {pdf_filename}")
    except Exception as e:
        print(f"Error creating PDF: {e}")