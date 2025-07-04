import logging
from graph.workflow import create_research_assistant
from config import Config
from utils import configure_logging

logger = configure_logging()

if __name__ == "__main__":
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
    
    # Create the research assistant
    app = create_research_assistant()
    
    # Interactive mode
    print("\n🤖 Research Assistant is ready!")
    print("Ask me anything. Type 'quit' to exit.")
    print("Examples:")
    print("  - What are the latest developments in AI?")
    print("  - Search for recent news about climate change")
    print("  - Summarize this PDF: https://example.com/document.pdf")
    print("  - What did we discuss about Python earlier?")
    
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