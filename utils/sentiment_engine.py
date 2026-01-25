from transformers import BertTokenizer, BertForSequenceClassification, pipeline
import torch

class SentimentEngine:
    def __init__(self):
        print("Loading FinBERT model... (This may take a moment first time)")
        # We use the 'ProsusAI/finbert' model, specifically pre-trained on financial text
        self.model_name = "ProsusAI/finbert"
        self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
        self.model = BertForSequenceClassification.from_pretrained(self.model_name)
        
        # Create a pipeline for easy usage
        self.nlp = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)
        print("FinBERT model loaded successfully.")

    def analyze(self, text):
        """
        Input: A news headline (string)
        Output: A dictionary containing 'label' (positive/negative/neutral) and 'score' (confidence)
        """
        try:
            results = self.nlp(text)
            return results[0] # Returns dict like {'label': 'positive', 'score': 0.95}
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return None

# --- Unit Test Area ---
if __name__ == "__main__":
    # This block only runs if you execute this file directly, useful for testing.
    engine = SentimentEngine()
    
    # Let's simulate some incoming news headlines to test the brain
    test_headlines = [
        "European Central Bank raises interest rates by 0.5% to fight inflation.",
        "Eurozone economy shrinks, fears of recession grow.",
        "Markets remain quiet ahead of the holiday season."
    ]
    
    print("\n--- Testing Sentiment Engine ---")
    for headline in test_headlines:
        sentiment = engine.analyze(headline)
        print(f"News: {headline}")
        print(f"Sentiment: {sentiment['label'].upper()} (Confidence: {sentiment['score']:.4f})\n")