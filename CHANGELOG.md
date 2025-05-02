# NovellaGPT Changelog

## Version 2.0.0 (April 26, 2025)

### Major Improvements
- **Token-Based Progress Tracking**: Added real-time token counting to accurately show generation progress
- **Enhanced Metrics Display**: Now shows tokens, estimated words, and generation rate
- **Threaded Monitoring**: Added background thread to monitor generation without blocking the UI
- **Improved Performance Metrics**: Shows tokens per second and estimated completion time

### Technical Improvements
- Added `token_counter.py` module for proper token counting with Claude's tokenizer
- Created thread-based monitoring system to track file changes in real-time
- Improved error handling for partial file reads
- Enhanced status updates with more detailed information

### User Experience
- Better progress bar accuracy based on token counts rather than time
- More detailed status messages with time elapsed and estimated completion
- Cleaner display of word and token counts with proper formatting

## Version 1.0.0 (April 26, 2025)

Initial release of NovellaGPT with:
- Claude 3.7 novella generation
- PDF export functionality
- Basic Streamlit interface
- Progress tracking based on time estimates
- File downloads