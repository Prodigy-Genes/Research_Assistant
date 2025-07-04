"""
Research Assistant - CLI and Web Server
Supports both interactive CLI mode and web server mode
"""

import logging
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from graph.workflow import create_research_assistant
from config import Config
from utils import configure_logging

logger = configure_logging()

def create_web_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    research_assistant = create_research_assistant()
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy'})
    
    @app.route('/ask', methods=['POST'])
    def ask_question():
        try:
            data = request.get_json()
            if not data or 'question' not in data:
                return jsonify({'error': 'No question provided'}), 400
            
            question = data['question'].strip()
            if not question:
                return jsonify({'error': 'Question cannot be empty'}), 400
            
            logger.info(f"Processing question: {question}")
            result = research_assistant.invoke({"question": question})
            
            if result.get("error"):
                return jsonify({'error': result['error']}), 500
            
            response = {
                'answer': result.get('answer', 'No answer provided'),
                'citations': result.get('citations', []),
                'timestamp': result.get('timestamp'),
                'question': question
            }
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
    return app

def run_web_server():
    """Run the Flask web server"""
    print("🌐 Starting Research Assistant Web Server...")
    app = create_web_app()
    
    host = getattr(Config, 'HOST', '0.0.0.0')
    port = getattr(Config, 'PORT', 5000)
    debug = getattr(Config, 'DEBUG', False)
    
    print(f"🚀 Server running on: http://{host}:{port}")
    print(f"📡 Endpoints: POST /ask, GET /health")
    print(f"🎯 Ready for React frontend!")
    
    app.run(host=host, port=port, debug=debug, threaded=True)

def run_cli():
    """Run the interactive CLI"""
    print("🤖 Research Assistant CLI Mode")
    print("Ask me anything. Type 'quit' to exit.")
    print("Examples:")
    print("  - What are the latest developments in AI?")
    print("  - Search for recent news about climate change")
    print("  - Summarize this PDF: https://example.com/document.pdf")
    
    app = create_research_assistant()
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Later!")
                break
            
            if not question:
                continue
            
            print(f"\n🔄 Processing your question...")
            result = app.invoke({"question": question})
            
            if result.get("error"):
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n✅ Answer:")
                print(result["answer"])
                
                if result.get("citations"):
                    print(f"\n📚 Citations:")
                    for i, citation in enumerate(result["citations"], 1):
                        print(f"  {i}. {citation}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Unexpected error: {e}")

def main():
    """Main entry point"""
    # Check API keys
    if not Config.OPENAI_API_KEY:
        print("⚠️  Please set your OPENAI_API_KEY in the .env file")
        print("Get it from: https://platform.openai.com/api-keys")
        exit(1)
    
    if not Config.BRAVE_API_KEY:
        print("⚠️  Please set your BRAVE_API_KEY in the .env file")
        print("Get it from: https://brave.com/search/api/")
        exit(1)
    
    print("🚀 Starting Research Assistant...")
    print("📊 API Keys configured successfully")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ['web', 'server', 'api']:
            run_web_server()
            return
        elif mode in ['cli', 'interactive', 'chat']:
            run_cli()
            return
        else:
            print(f"❌ Unknown mode: {mode}")
            print("Usage: python main.py [web|cli]")
            exit(1)
    
    # Default: Ask user for mode
    print("\nSelect mode:")
    print("1. CLI (Interactive command line)")
    print("2. Web Server (For React frontend)")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        if choice == '1':
            run_cli()
            break
        elif choice == '2':
            run_web_server()
            break
        else:
            print("Please enter 1 or 2")

if __name__ == "__main__":
    main()