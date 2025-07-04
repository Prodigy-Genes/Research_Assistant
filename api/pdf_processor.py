import requests
import PyPDF2
import re
import logging
import os

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF processing utilities"""
    
    @staticmethod
    def extract_text_from_url(url: str) -> str:
        """Extract text from PDF URL"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Save temporarily
            temp_path = "temp_pdf.pdf"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Extract text
            text = PDFProcessor.extract_text_from_file(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF URL: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF file: {e}")
            return ""