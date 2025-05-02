# NovellaGPT

NovellaGPT is a powerful CLI tool for generating high-quality novellas using Claude 3.7 AI. It helps users create professional, well-structured stories with rich characters, engaging plots, and proper formatting.

## Features

- **AI-Powered Novella Generation**: Leverages Claude 3.7's advanced capabilities to create compelling stories
- **Extended Output**: Generates 30,000-40,000 word novellas with complete narrative arcs
- **Extended Thinking**: Uses Claude's thinking tokens to plan coherent storylines
- **Live Streaming**: Shows content as it's generated
- **Progress Tracking**: Monitors word count and generation progress
- **Autosave**: Periodically saves content to prevent loss in case of interruption
- **PDF Export**: Converts text to professionally formatted ebook-style PDF

## Installation

1. Clone this repository
2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install requirements:

```bash
pip install -r requirements.txt
```

4. Set up your Anthropic API key:
   - Create a `.env` file in the project root
   - Add your API key: `ANTHROPIC_API_KEY=your_api_key_here`

## Usage

### Command-Line Interface

```bash
python storygen2.py --prompt "Your novella prompt" --title "Your Title"
```

Command-line arguments:
- `--prompt`: Your creative prompt for the novella
- `--title`: Title for your novella (optional)
- `--api-key`: Anthropic API key (optional if set in .env file)
- `--no-pdf`: Skip PDF generation (optional)

If you don't provide a prompt or title, you'll be prompted to enter them interactively.

### Generating a Novella from Python

```python
from storygen2 import generate_novella

content, title = generate_novella(
    prompt="Write a mystery novella set in a small coastal town with an unexpected twist.",
    title="Secrets of Seacliff",
    api_key="your_api_key_here"  # Optional if set in environment
)
```

### Converting Existing Text to PDF

If you already have a text file, you can convert it to a PDF:

```python
from storygen2 import convert_to_pdf

pdf_file = convert_to_pdf("your_file.txt", "Your Title")
print(f"PDF created: {pdf_file}")
```

## Output

The tool generates two files:
1. A text file with the novella content (`.txt`)
2. A professionally formatted PDF ebook (`.pdf`)

## Requirements

- Python 3.8+
- [Anthropic API key](https://www.anthropic.com/)
- Required packages (see requirements.txt):
  - anthropic
  - python-dotenv
  - fpdf

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.