# NovellaGPT Streamlit App

A simple web interface for NovellaGPT that allows users to generate novellas using Claude 3.7.

## Features

- User-friendly web interface
- Input for novella title and prompt
- Advanced options for customization
- Real-time progress tracking
- Preview of generated content
- Download options for TXT and PDF formats

## Running the App

1. Make sure you have installed all requirements:
```bash
source venv/bin/activate
pip install streamlit
```

2. Run the app using one of the provided scripts:

### Option 1: Run in the foreground (blocks terminal)
```bash
./run_app.sh
```

### Option 2: Run in the background (detached process)
```bash
./start_app_background.sh
```
To stop the background process:
```bash
./stop_app.sh
```

3. Open your browser and navigate to http://localhost:8501

## Using the App

1. Enter your Anthropic API key in the sidebar
2. Provide a title for your novella
3. Enter a detailed prompt describing the story you want
4. (Optional) Customize the system prompt in advanced options
5. Click "Generate Novella" to start the generation process
6. Track progress in real-time
7. When generation is complete, download the TXT or PDF version

## Notes for the MVP

This MVP version includes:
- A simulation mode that demonstrates the UI without making actual API calls
- Professional PDF conversion
- Clean, responsive interface
- Basic error handling

To connect to the actual Claude API:
1. Uncomment the generate_novella function call in the code
2. Remove the MockStream simulation code

## Future Enhancements

- Social sharing of generated novellas
- AI image generation for covers
- Chapter-by-chapter regeneration
- User accounts and saved drafts
- Gallery of published stories with ratings
- Community features for feedback

## Troubleshooting

If you encounter any issues:
1. Ensure you have a valid Anthropic API key
2. Check that all dependencies are installed
3. Verify that the convert_pdf.py file is in the same directory
4. Look for error messages in the terminal running Streamlit