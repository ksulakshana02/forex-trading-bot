from utils.llm_analyzer import LLMMarketAnalyzer
import os

# Mock article for testing
FOREX_ARTICLE = """
The US Dollar surged today after the Federal Reserve announced a surprise 50 basis point rate hike. 
Jerome Powell stated that inflation remains "too high" and that the committee is "strongly committed" to bringing it down to the 2% target.
Markets immediately reacted, with EURUSD dropping 1.2% and USDJPY rallying.
Analysts believe this hawkish stance effectively takes a pivot off the table for 2024.
"""

def test_analyzer():
    print("--- Testing LLM Market Analyzer ---")
    
    # Check for API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not found.")
        print("Please set it in your terminal: $env:OPENAI_API_KEY='sk-...'")
        return

    analyzer = LLMMarketAnalyzer()
    
    if analyzer.llm is None:
        print("Analyzer failed to initialize.")
        return

    print("\nAnalyzing Article:\n" + FOREX_ARTICLE)
    
    result = analyzer.analyze_article(FOREX_ARTICLE)
    
    if result:
        print("\n--- RESUT ---")
        print(result)
        
        # Simple assertions
        if result['decision'] in ['BUY', 'SELL', 'NEUTRAL']:
            print("\n[PASS] Decision is valid.")
        else:
            print("\n[FAIL] Invalid decision format.")
            
        if 0.0 <= result['confidence'] <= 1.0:
             print("[PASS] Confidence score is valid.")
        else:
             print("[FAIL] Confidence score out of range.")
    else:
        print("\n[FAIL] No result returned.")

if __name__ == "__main__":
    test_analyzer()
