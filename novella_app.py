import streamlit as st
import os
import time
import tempfile
from token_counter import token_counter, estimate_words, estimate_completion
from storygen2 import generate_novella, convert_to_pdf, convert_to_epub
from audio_gen import AudiobookGenerator

# Page config
st.set_page_config(
    page_title="NovellaGPT", 
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1E3A8A;
    text-align: center;
}
.subheader {
    font-size: 1.2rem;
    color: #4B5563;
    text-align: center;
    margin-bottom: 2rem;
}
.stButton>button {
    width: 100%;
    height: 3rem;
    background-color: #1E3A8A;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">NovellaGPT</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Generate professional novellas powered by Claude 3.7</p>', unsafe_allow_html=True)

# Initialize session state for generated content
if 'novella_content' not in st.session_state:
    st.session_state.novella_content = None
if 'novella_title' not in st.session_state:
    st.session_state.novella_title = None
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'word_count' not in st.session_state:
    st.session_state.word_count = 0
if 'audiobook_progress' not in st.session_state:
    st.session_state.audiobook_progress = 0
if 'audiobook_complete' not in st.session_state:
    st.session_state.audiobook_complete = False
if 'audiobook_path' not in st.session_state:
    st.session_state.audiobook_path = None
if 'audio_segments' not in st.session_state:
    st.session_state.audio_segments = []
if 'epub_path' not in st.session_state:
    st.session_state.epub_path = None
    
# Initialize generation progress tracking state
if 'gen_progress' not in st.session_state:
    st.session_state.gen_progress = 0
if 'gen_tokens' not in st.session_state:
    st.session_state.gen_tokens = 0
if 'gen_words' not in st.session_state:
    st.session_state.gen_words = 0
if 'gen_tokens_per_sec' not in st.session_state:
    st.session_state.gen_tokens_per_sec = 0
if 'gen_elapsed_min' not in st.session_state:
    st.session_state.gen_elapsed_min = 0
if 'gen_elapsed_sec' not in st.session_state:
    st.session_state.gen_elapsed_sec = 0
if 'gen_completed' not in st.session_state:
    st.session_state.gen_completed = False
if 'gen_update_time' not in st.session_state:
    st.session_state.gen_update_time = time.time()

# Sidebar for API key
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Anthropic API Key", type="password", help="Your Claude API key from Anthropic")
    st.caption("Your API key is never stored and only used for generation.")
    
    openai_api_key = st.text_input("OpenAI API Key", type="password", help="Your OpenAI API key for audiobook generation (optional)")
    st.caption("Required only if you want to generate audiobooks.")
    
    # Voice selection (only if OpenAI API key is provided)
    if openai_api_key:
        voices = list(AudiobookGenerator.AVAILABLE_VOICES.keys())
        voice_descriptions = AudiobookGenerator.AVAILABLE_VOICES
        
        # Format voice options with descriptions
        voice_options = [f"{voice} - {voice_descriptions[voice]}" for voice in voices]
        
        selected_voice_option = st.selectbox(
            "Audiobook Voice", 
            options=voice_options, 
            index=voices.index(AudiobookGenerator.DEFAULT_VOICE),
            help="Select the voice for your audiobook"
        )
        
        # Extract just the voice name from the selection
        selected_voice = selected_voice_option.split(" - ")[0]
        
        # Option to generate audiobook
        generate_audio = st.checkbox("Generate Audiobook", value=False, help="Generate an audiobook version of your novella")
    else:
        selected_voice = AudiobookGenerator.DEFAULT_VOICE
        generate_audio = False
    
    st.markdown("---")
    st.subheader("About NovellaGPT")
    st.markdown("""
    NovellaGPT uses Claude 3.7 AI to generate high-quality novellas with well-developed characters, 
    engaging plots, and professional formatting.
    
    **Features:**
    - 30,000-40,000 word novellas
    - Rich character development
    - Complex plot structures
    - Professional PDF formatting
    - EPUB export for Amazon KDP
    - MP3 audiobook generation
    
    [View on GitHub](https://github.com/yourusername/novellagpt)
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Create Your Novella")
    
    title = st.text_input("Novella Title", help="Enter a title for your novella")
    
    prompt = st.text_area(
        "Prompt", 
        height=150,
        placeholder="Write a mystery novella set in a small coastal town with an unexpected twist...",
        help="Describe the novella you want to generate. Be specific about genre, setting, characters, etc."
    )
    
    # Custom system prompt option (advanced)
    show_advanced = st.checkbox("Show advanced options")
    
    system_prompt = None
    if show_advanced:
        system_prompt = st.text_area(
            "Custom System Prompt (Optional)", 
            height=100,
            help="Custom instructions for the AI. Leave blank to use the default."
        )
    
    generate_button = st.button("Generate Novella")

with col2:
    st.subheader("Generation Status")
    if not st.session_state.generation_complete:
        status_container = st.empty()
        progress_bar = st.empty()
        word_count_container = st.empty()
        
        # Check if generation is actively running by looking at session state values
        if 'gen_progress' in st.session_state and st.session_state.gen_progress > 0:
            # Format tokens with commas
            tokens_display = f"{st.session_state.gen_tokens:,}" if hasattr(st.session_state, 'gen_tokens') else "0"
            words_display = f"{st.session_state.gen_words:,}" if hasattr(st.session_state, 'gen_words') else "0"
            
            # Update UI with session state values
            progress_bar.progress(st.session_state.gen_progress)
            
            # Update word counter with both tokens and estimated words
            word_count_container.metric(
                "Generation Progress", 
                f"{words_display} words", 
                f"{tokens_display} tokens"
            )
            
            # Display status with time and rate
            elapsed_min = st.session_state.gen_elapsed_min
            elapsed_sec = st.session_state.gen_elapsed_sec
            tokens_per_sec = st.session_state.gen_tokens_per_sec
            completion = st.session_state.gen_progress
            
            status_container.info(
                f"Generating: {elapsed_min}m {elapsed_sec}s elapsed" + 
                f" | ~{tokens_per_sec:.0f} tokens/sec" +
                f" | {completion:.1%} complete"
            )
            
            # Add a note about auto-refreshing
            st.caption("Progress updates automatically every few seconds...")
        else:
            status_container.info("Ready to generate. Fill in the form and click 'Generate Novella'.")
    else:
        st.success(f"Generation complete! Generated '{st.session_state.novella_title}'")
        st.metric("Word Count", st.session_state.word_count)
        
        # Download buttons container
        download_container = st.container()
        
        with download_container:
            # Clean title for filenames
            clean_title = st.session_state.novella_title.replace(" ", "_")
            txt_filename = f"{clean_title}.txt"
            pdf_filename = f"{clean_title}.pdf"
            epub_filename = f"{clean_title}.epub"
            audiobook_filename = f"{clean_title}_audiobook.mp3"
            audiobook_path = os.path.join("audio_files", audiobook_filename)
            
            # Create columns for download buttons
            col_txt, col_pdf, col_epub, col_audio = st.columns(4)
            
            # Text download button
            with col_txt:
                st.download_button(
                    label="📄 Download TXT",
                    data=st.session_state.novella_content,
                    file_name=txt_filename,
                    mime="text/plain",
                    use_container_width=True
                )
            
            # PDF download button
            with col_pdf:
                if os.path.exists(pdf_filename):
                    with open(pdf_filename, "rb") as pdf_file:
                        pdf_data = pdf_file.read()
                    
                    st.download_button(
                        label="📚 Download PDF",
                        data=pdf_data,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("PDF file not found")
            
            # EPUB download button
            with col_epub:
                # Check if EPUB exists or generate it on demand
                if os.path.exists(epub_filename):
                    with open(epub_filename, "rb") as epub_file:
                        epub_data = epub_file.read()
                    
                    st.download_button(
                        label="📱 Download EPUB",
                        data=epub_data,
                        file_name=epub_filename,
                        mime="application/epub+zip",
                        use_container_width=True
                    )
                else:
                    # Button to generate EPUB
                    if st.button("📱 Generate EPUB", use_container_width=True):
                        try:
                            with st.spinner("Generating EPUB..."):
                                epub_file = convert_to_epub(txt_filename, st.session_state.novella_title)
                                st.success(f"EPUB created: {epub_file}")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error generating EPUB: {e}")
            
            # Audiobook download button
            with col_audio:
                if st.session_state.audiobook_complete and st.session_state.audiobook_path:
                    with open(st.session_state.audiobook_path, "rb") as audio_file:
                        audio_data = audio_file.read()
                    
                    st.download_button(
                        label="🎧 Download MP3",
                        data=audio_data,
                        file_name=audiobook_filename,
                        mime="audio/mpeg",
                        use_container_width=True
                    )
                else:
                    if st.session_state.audiobook_progress > 0 and st.session_state.audiobook_progress < 100:
                        # Show progress if audiobook is being generated
                        audio_progress = st.progress(st.session_state.audiobook_progress / 100)
                        st.text(f"Generating audiobook: {st.session_state.audiobook_progress:.0f}%")
                    elif 'openai_api_key' in locals() and openai_api_key:
                        # Button to generate audiobook
                        if st.button("🎧 Generate Audiobook", use_container_width=True):
                            st.session_state.audiobook_progress = 1
                            st.rerun()
                    else:
                        st.info("Add OpenAI API key to generate audiobook")
            
            # Display file paths
            file_info = f"Files saved to:\n- TXT: {os.path.abspath(txt_filename)}\n- PDF: {os.path.abspath(pdf_filename)}"
            if os.path.exists(epub_filename):
                file_info += f"\n- EPUB: {os.path.abspath(epub_filename)}"
            if st.session_state.audiobook_complete and st.session_state.audiobook_path:
                file_info += f"\n- MP3: {os.path.abspath(st.session_state.audiobook_path)}"
            st.info(file_info)
            
            # Display audio segments if available
            if st.session_state.audio_segments:
                with st.expander("Chapter Audio Files"):
                    for i, segment_path in enumerate(st.session_state.audio_segments):
                        if os.path.exists(segment_path):
                            segment_name = os.path.basename(segment_path)
                            st.audio(segment_path, format="audio/mp3")
                            st.caption(f"Chapter {i+1}")
                    
                    st.caption("You can play individual chapters directly in the browser")

# Handle generation process
if generate_button:
    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar")
    elif not prompt:
        st.error("Please enter a prompt for your novella")
    elif not title:
        st.error("Please enter a title for your novella")
    else:
        try:
            # Update UI to show generation is starting
            with col2:
                status_container = st.empty()
                progress_bar = st.empty()
                word_count_container = st.empty()
                
                status_container.info("Initializing generation...")
                progress = progress_bar.progress(0)
                word_count_container.metric("Words Generated", 0)
            
            # Call the actual generation function with real Claude API
            status_container.info("Initializing Claude 3.7 for novella generation...")
            
            try:
                # Set environment variable for API key
                os.environ["ANTHROPIC_API_KEY"] = api_key
                
                # Prepare to capture streaming output
                start_time = time.time()
                
                # Setup monitoring thread for the generation process
                import threading
                import time
                
                # Set up filename
                clean_filename = "".join(c if c.isalnum() else "_" for c in title)
                filename = f"{clean_filename}.txt"
                
                # Initialize session state for generation progress
                if 'gen_progress' not in st.session_state:
                    st.session_state.gen_progress = 0
                if 'gen_tokens' not in st.session_state:
                    st.session_state.gen_tokens = 0
                if 'gen_words' not in st.session_state:
                    st.session_state.gen_words = 0
                if 'gen_tokens_per_sec' not in st.session_state:
                    st.session_state.gen_tokens_per_sec = 0
                if 'gen_elapsed_min' not in st.session_state:
                    st.session_state.gen_elapsed_min = 0
                if 'gen_elapsed_sec' not in st.session_state:
                    st.session_state.gen_elapsed_sec = 0
                if 'gen_completed' not in st.session_state:
                    st.session_state.gen_completed = False
                if 'gen_update_time' not in st.session_state:
                    st.session_state.gen_update_time = time.time()
                
                # Create a monitoring function
                def monitor_generation():
                    """Monitor the generation process and update session state"""
                    last_tokens = 0
                    last_update_time = time.time()
                    update_interval = 1.0  # Update session state every second
                    
                    print("Claude is generating your novella...")
                    
                    while True:
                        # Check if file exists yet
                        if not os.path.exists(filename):
                            time.sleep(1)
                            continue
                            
                        try:
                            with open(filename, "r", encoding="utf-8") as file:
                                current_content = file.read()
                            
                            # Get metrics
                            tokens = token_counter(current_content)
                            word_estimate = estimate_words(tokens)
                            completion = estimate_completion(tokens, target_tokens=100000)
                            
                            # Calculate tokens per second
                            current_time = time.time()
                            time_diff = current_time - last_update_time
                            
                            if time_diff >= update_interval:
                                # Update session state (thread-safe)
                                tokens_per_sec = (tokens - last_tokens) / time_diff if time_diff > 0 else 0
                                
                                # Add time elapsed
                                elapsed = current_time - start_time
                                elapsed_min = int(elapsed // 60)
                                elapsed_sec = int(elapsed % 60)
                                
                                # Update session state with progress data
                                st.session_state.gen_progress = completion
                                st.session_state.gen_tokens = tokens
                                st.session_state.gen_words = word_estimate
                                st.session_state.gen_tokens_per_sec = tokens_per_sec
                                st.session_state.gen_elapsed_min = elapsed_min
                                st.session_state.gen_elapsed_sec = elapsed_sec
                                st.session_state.gen_update_time = time.time()
                                
                                # Print progress to console (useful for debugging)
                                print(f"Generation progress: {word_estimate:,} words | {tokens:,} tokens | {completion:.1%} complete")
                                
                                # Reset for next update
                                last_tokens = tokens
                                last_update_time = current_time
                            
                            # Check for completion
                            if "--- END OF NOVELLA ---" in current_content:
                                # Final update to session state
                                elapsed = time.time() - start_time
                                elapsed_min = int(elapsed // 60)
                                elapsed_sec = int(elapsed % 60)
                                
                                # Update final stats
                                st.session_state.gen_progress = 1.0
                                st.session_state.gen_elapsed_min = elapsed_min
                                st.session_state.gen_elapsed_sec = elapsed_sec
                                st.session_state.gen_completed = True
                                
                                print(f"Novella generated successfully in {elapsed_min}m {elapsed_sec}s")
                                return
                                
                        except Exception as e:
                            # Don't show errors when reading partial files
                            pass
                            
                        time.sleep(0.5)  # Check again in half a second
                
                # Start the monitoring thread
                monitor_thread = threading.Thread(target=monitor_generation)
                monitor_thread.daemon = True  # Thread will exit when main program exits
                monitor_thread.start()
                
                # Add auto-refresh mechanism to update UI based on session state
                def auto_refresh():
                    last_refresh_time = time.time()
                    refresh_interval = 3.0  # Refresh UI every 3 seconds
                    
                    while not st.session_state.gen_completed:
                        current_time = time.time()
                        if current_time - last_refresh_time >= refresh_interval:
                            # Trigger a rerun to update UI
                            last_refresh_time = current_time
                            try:
                                time.sleep(0.1)  # Small delay to prevent race conditions
                                st.rerun()
                            except Exception as e:
                                # If rerun fails, just continue
                                print(f"Rerun failed: {e}")
                        
                        time.sleep(0.5)
                
                # Start auto-refresh thread
                refresh_thread = threading.Thread(target=auto_refresh)
                refresh_thread.daemon = True
                refresh_thread.start()
                
                # Call generate_novella with streaming (this will block until complete)
                content, final_title = generate_novella(prompt, title, system_prompt)
                
                # Wait for the thread to register completion
                time.sleep(2)
                
                # Read the final file
                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as file:
                        full_content = file.read()
                    
                    # Final token count
                    tokens = token_counter(full_content)
                    word_estimate = estimate_words(tokens)
                    
                    # Update session state with the results
                    st.session_state.novella_content = full_content
                    st.session_state.novella_title = title
                    st.session_state.generation_complete = True
                    st.session_state.word_count = word_estimate
                    
                    # Update UI
                    word_count_container.metric("Final Word Count", f"{word_estimate:,}", f"{tokens:,} tokens")
                else:
                    st.error("File not found after generation. Something went wrong.")
            except Exception as e:
                st.error(f"Error in Claude API generation: {str(e)}")
                raise e
            
            # The text file is already created by generate_novella
            # But we'll create the PDF here
            clean_title = title.replace(" ", "_")
            txt_filename = f"{clean_title}.txt"
            pdf_filename = f"{clean_title}.pdf"
            
            # Generate PDF from the text file
            try:
                pdf_file = convert_to_pdf(txt_filename, title)
                st.session_state.pdf_path = pdf_file
                st.success(f"PDF created successfully: {pdf_file}")
            except Exception as e:
                st.warning(f"Could not generate PDF: {e}")
                
            # Generate EPUB from the text file (for Amazon KDP)
            try:
                epub_file = convert_to_epub(txt_filename, title)
                st.session_state.epub_path = epub_file
                st.success(f"EPUB created successfully: {epub_file}")
            except Exception as e:
                st.warning(f"Could not generate EPUB: {e}")
            
            # Check if we should generate audiobook immediately after novella generation
            if 'generate_audio' in locals() and generate_audio and openai_api_key:
                try:
                    st.info("Generating audiobook from novella text...")
                    
                    # Set environment variable for OpenAI API key
                    os.environ["OPENAI_API_KEY"] = openai_api_key
                    
                    # Audio generation
                    def update_audio_progress(progress, current, total, final_path=None):
                        """Callback to update audiobook generation progress"""
                        st.session_state.audiobook_progress = progress
                        if final_path:
                            st.session_state.audiobook_path = final_path
                            st.session_state.audiobook_complete = True
                    
                    # Start audiobook generation in a separate thread
                    import threading
                    
                    def generate_audiobook_thread():
                        try:
                            generator = AudiobookGenerator(api_key=openai_api_key)
                            audio_files, combined = generator.generate_chapter_by_chapter(
                                txt_filename, 
                                title, 
                                voice=selected_voice,
                                callback=update_audio_progress
                            )
                            
                            # Update session state with results
                            if audio_files:
                                st.session_state.audio_segments = audio_files
                            if combined:
                                st.session_state.audiobook_path = combined
                                st.session_state.audiobook_complete = True
                            
                            # Final update
                            st.session_state.audiobook_progress = 100
                        except Exception as e:
                            print(f"Error in audiobook generation: {e}")
                    
                    # Start the audiobook generation in a background thread
                    audio_thread = threading.Thread(target=generate_audiobook_thread)
                    audio_thread.daemon = True
                    audio_thread.start()
                    
                    # Initial progress indicator
                    st.session_state.audiobook_progress = 1
                except Exception as e:
                    st.warning(f"Could not start audiobook generation: {e}")
            
            # Trigger a rerun to update the UI with download buttons
            st.rerun()
            
        except Exception as e:
            st.error(f"Error occurred during generation: {e}")

# Handle standalone audiobook generation if user clicked generate button
if st.session_state.audiobook_progress == 1 and not st.session_state.audiobook_complete:
    try:
        # Set environment variable for OpenAI API key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Status container
        audio_status = st.empty()
        audio_progress_bar = st.progress(0.01)
        audio_status.info("Initializing audiobook generation...")
        
        # Clean title for filenames
        clean_title = st.session_state.novella_title.replace(" ", "_")
        txt_filename = f"{clean_title}.txt"
        
        # Audio generation callback
        def update_audio_progress(progress, current, total, final_path=None):
            """Callback to update audiobook generation progress"""
            audio_progress_bar.progress(progress / 100)
            audio_status.info(f"Generating audiobook: Segment {current}/{total} ({progress:.1f}%)")
            
            # Update session state
            st.session_state.audiobook_progress = progress
            if final_path:
                st.session_state.audiobook_path = final_path
                st.session_state.audiobook_complete = True
                audio_status.success(f"Audiobook generated successfully!")
        
        # Create and start the generator
        generator = AudiobookGenerator(api_key=openai_api_key)
        audio_files, combined = generator.generate_chapter_by_chapter(
            txt_filename, 
            st.session_state.novella_title, 
            voice=selected_voice,
            callback=update_audio_progress
        )
        
        # Update session state with results
        if audio_files:
            st.session_state.audio_segments = audio_files
        if combined:
            st.session_state.audiobook_path = combined
            st.session_state.audiobook_complete = True
        
        # Final update and rerun to show download buttons
        st.session_state.audiobook_progress = 100
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating audiobook: {e}")
        # Reset progress on error
        st.session_state.audiobook_progress = 0

# Display preview if content exists
if st.session_state.novella_content and st.session_state.generation_complete:
    st.subheader("Preview")
    with st.expander("Show novella preview", expanded=False):
        preview_content = st.session_state.novella_content[:5000] + "..." \
            if len(st.session_state.novella_content) > 5000 else st.session_state.novella_content
        st.text_area("Content Preview", value=preview_content, height=400, disabled=True)
        
    # Audio preview if available
    if st.session_state.audiobook_complete and st.session_state.audiobook_path:
        with st.expander("Listen to Audiobook Preview", expanded=False):
            st.audio(st.session_state.audiobook_path, format="audio/mp3")
            st.caption("Preview of the complete audiobook")
