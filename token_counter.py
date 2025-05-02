import tiktoken
import re

def get_token_counter():
    """
    Creates a token counter function that uses tiktoken to count tokens
    in the Claude tokenizer format (cl100k_base)
    
    Returns:
        A function that counts tokens in text
    """
    # Initialize the encoder with Claude's tokenizer model
    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except KeyError:
        # Fall back to GPT-4 tokenizer if Claude's isn't available
        enc = tiktoken.get_encoding("p50k_base")
    
    def count_tokens(text):
        """
        Count the number of tokens in the given text
        
        Args:
            text (str): The text to count tokens in
            
        Returns:
            int: The token count
        """
        if not text:
            return 0
        
        # Clean the text a bit (remove headers/footers that may be present)
        clean_text = re.sub(r'--- NOVELLA: .*? ---\n\n', '', text)
        clean_text = re.sub(r'\n\n--- END OF NOVELLA ---\n', '', clean_text)
        clean_text = re.sub(r'--- WORD COUNT: \d+ ---\n', '', clean_text)
        
        # Count tokens
        return len(enc.encode(clean_text))
    
    def estimate_words_from_tokens(tokens):
        """
        Estimate the number of words based on token count
        Using average ratio for English text (tokens:words)
        
        Args:
            tokens (int): Token count
            
        Returns:
            int: Estimated word count
        """
        # Common ratio of tokens to words is about 4:3 (or 1.33:1)
        # But Claude tokenizer is more efficient, closer to 1.2:1
        return int(tokens / 1.2)
    
    def estimate_completion_percentage(tokens, target_tokens=120000):
        """
        Estimate completion percentage based on token count
        
        Args:
            tokens (int): Current token count
            target_tokens (int): Target token count for completion
            
        Returns:
            float: Completion percentage (0-1)
        """
        return min(1.0, tokens / target_tokens)
    
    # Return functions as a tuple
    return count_tokens, estimate_words_from_tokens, estimate_completion_percentage

# Module-level exports for easy importing
token_counter, estimate_words, estimate_completion = get_token_counter()

# For testing
if __name__ == "__main__":
    sample_text = "This is a sample text to test the token counter functionality."
    tokens = token_counter(sample_text)
    words = estimate_words(tokens)
    completion = estimate_completion(tokens)
    
    print(f"Text: '{sample_text}'")
    print(f"Token count: {tokens}")
    print(f"Estimated words: {words}")
    print(f"Completion percentage: {completion:.2%}")