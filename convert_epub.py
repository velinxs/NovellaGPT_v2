import re
import time
import os
from ebooklib import epub

def convert_to_epub(txt_filename, title, author="Generated with Claude 3.7"):
    """
    Convert a text file containing a novella to EPUB format
    
    Args:
        txt_filename (str): Path to the text file
        title (str): Title of the novella
        author (str, optional): Author name
        
    Returns:
        str: Path to the generated EPUB file
    """
    # Create epub file path
    epub_filename = txt_filename.replace('.txt', '.epub')
    
    # Read the text content
    with open(txt_filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove header and footer markers
    content = re.sub(r'--- NOVELLA: .*? ---\n\n', '', content)
    content = re.sub(r'\n\n--- END OF NOVELLA ---\n', '', content)
    content = re.sub(r'--- WORD COUNT: \d+ ---\n', '', content)
    content = re.sub(r'--- GENERATION INTERRUPTED BY USER ---\n', '', content)
    
    # Initialize EPUB book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier(f'novellagpt-{int(time.time())}')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)
    
    # Add default CSS
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Georgia, serif;
        line-height: 1.5;
        text-align: justify;
        margin: 2%;
    }
    h1, h2, h3, h4 {
        font-family: "Helvetica", "Arial", sans-serif;
        text-align: center;
        margin-top: 2em;
        margin-bottom: 1em;
    }
    h1 {
        font-size: 1.5em;
        margin-top: 3em;
    }
    h2 {
        font-size: 1.3em;
    }
    h3 {
        font-size: 1.1em;
    }
    p {
        text-indent: 1.5em;
        margin: 0;
        margin-bottom: 0.3em;
    }
    .chapter-first-p:first-letter {
        font-size: 2.5em;
        font-weight: bold;
        float: left;
        margin-right: 0.15em;
        line-height: 0.8;
    }
    .chapter {
        margin-top: 2em;
        page-break-before: always;
    }
    .title-page {
        text-align: center;
        page-break-after: always;
    }
    .title-page h1 {
        font-size: 2em;
        margin-top: 30%;
        margin-bottom: 1em;
    }
    .title-page p {
        text-indent: 0;
        margin: 1em 0;
    }
    '''
    css = epub.EpubItem(uid="style_default", file_name="style/default.css", 
                        media_type="text/css", content=style)
    book.add_item(css)
    
    # Create title page
    title_page_content = f'''
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>{title}</title>
        <link rel="stylesheet" href="style/default.css" type="text/css" />
    </head>
    <body>
        <div class="title-page">
            <h1>{title}</h1>
            <p>{author}</p>
            <p>{time.strftime("%B %d, %Y")}</p>
        </div>
    </body>
    </html>
    '''
    title_page = epub.EpubHtml(title='Title Page', file_name='title_page.xhtml', lang='en')
    title_page.content = title_page_content
    book.add_item(title_page)
    
    # Split content into chapters
    chapters = []
    toc = []
    
    # Check for # headers for chapter detection
    chapter_splits = re.split(r'(?m)^(#+\s+.*?)$', content)
    
    # If no chapters found or only one part
    if len(chapter_splits) <= 1:
        # Create a single chapter with all content
        c = epub.EpubHtml(title="Chapter 1", file_name="chapter_1.xhtml", lang='en')
        c.content = f'''
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title>Chapter 1</title>
            <link rel="stylesheet" href="style/default.css" type="text/css" />
        </head>
        <body class="chapter">
            <h1>Chapter 1</h1>
            {_format_paragraphs(content)}
        </body>
        </html>
        '''
        book.add_item(c)
        chapters.append(c)
        toc.append(epub.Link("chapter_1.xhtml", "Chapter 1", "chapter1"))
    else:
        # Process each header as a chapter
        current_file_index = 0
        
        for i in range(0, len(chapter_splits)-1, 2):
            header = chapter_splits[i+1] if i+1 < len(chapter_splits) else ""
            content_text = chapter_splits[i+2] if i+2 < len(chapter_splits) else ""
            
            # Skip empty chapters
            if not header.strip() or not content_text.strip():
                continue
                
            # Clean up header and use as chapter title
            header_text = header.strip('#').strip()
            chapter_id = f"chapter_{current_file_index+1}"
            file_name = f"{chapter_id}.xhtml"
            
            # Create chapter
            c = epub.EpubHtml(title=header_text, file_name=file_name, lang='en')
            c.content = f'''
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <title>{header_text}</title>
                <link rel="stylesheet" href="style/default.css" type="text/css" />
            </head>
            <body class="chapter">
                <h1>{header_text}</h1>
                {_format_paragraphs(content_text)}
            </body>
            </html>
            '''
            book.add_item(c)
            chapters.append(c)
            toc.append(epub.Link(file_name, header_text, chapter_id))
            current_file_index += 1
    
    # Add chapters to the book
    book.toc = toc
    
    # Add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style
    book.add_item(css)
    
    # Create spine
    book.spine = ['nav', title_page] + chapters
    
    # Write the epub file
    epub.write_epub(epub_filename, book, {})
    
    return epub_filename

def _format_paragraphs(text):
    """Format text into HTML paragraphs"""
    # Split into paragraphs
    paragraphs = text.strip().split('\n\n')
    formatted_html = ""
    
    # First paragraph special formatting
    if paragraphs:
        formatted_html = f'<p class="chapter-first-p">{paragraphs[0]}</p>\n'
        # Rest of paragraphs
        for p in paragraphs[1:]:
            if p.strip():
                formatted_html += f'<p>{p}</p>\n'
    
    return formatted_html

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python convert_epub.py <input_txt_file> <title> [author]")
        sys.exit(1)
    
    txt_filename = sys.argv[1]
    title = sys.argv[2]
    author = sys.argv[3] if len(sys.argv) > 3 else "Generated with Claude 3.7"
    
    try:
        epub_filename = convert_to_epub(txt_filename, title, author)
        print(f"EPUB created: {epub_filename}")
    except Exception as e:
        print(f"Error creating EPUB: {e}")