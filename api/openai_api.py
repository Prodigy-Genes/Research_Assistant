import openai
import logging
from config import Config

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = Config.OPENAI_API_KEY

class OpenAIAPI:
    """OpenAI API integration"""
    
    @staticmethod
    def generate_response(prompt: str, max_tokens: int = 1000) -> str:
        """Generate response using OpenAI API"""
        if not Config.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            return "Error: OpenAI API key not configured"
        
        try:
            response = openai.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant. Provide accurate, well-cited responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return f"Error generating response: {str(e)}"