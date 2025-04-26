import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables and configuration
load_dotenv()

# Get API key and configurations
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
debug_mode = os.getenv("DEBUG", "false").lower() == "true"

# Configure the API
genai.configure(api_key=api_key)

def get_default_generation_config():
    """Get default generation configuration."""
    return {
        "temperature": 0.7,        # Controls randomness (0.0-1.0)
        "top_p": 0.95,             # Nucleus sampling parameter
        "top_k": 40,               # Limits vocabulary to top K tokens
        "max_output_tokens": 8192, # Maximum response length
        "candidate_count": 1       # Number of responses to generate
    }

def chat_with_gemini(prompt, generation_config=None):
    """
    Generate a response from Gemini based on the prompt.
    
    Args:
        prompt (str): User input to send to the model
        generation_config (dict, optional): Override default generation parameters
        
    Returns:
        str: The model's response text
    """
    if debug_mode:
        print(f"DEBUG: Using model {model_name}")
    
    # Use provided config or default
    config = generation_config or get_default_generation_config()
    
    try:
        # Initialize the model
        model = genai.GenerativeModel(model_name)
        
        # Generate content with configuration
        response = model.generate_content(
            prompt,
            generation_config=config
        )
        
        return response.text
    except Exception as e:
        error_msg = f"Error generating content: {str(e)}"
        if debug_mode:
            print(f"DEBUG ERROR: {error_msg}")
        raise Exception(error_msg)
