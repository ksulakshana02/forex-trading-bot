from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
try:
    from langchain_core.pydantic_v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field
import os

class MarketSignal(BaseModel):
    decision: str = Field(description="The trading decision: BUY, SELL, or NEUTRAL")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Brief explanation of the decision based on the news")

class LLMMarketAnalyzer:
    def __init__(self, model_name="gpt-4-turbo-preview"):
        """
        Initialize the LLM Market Analyzer.
        Requires OPENAI_API_KEY environment variable.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[LLM] WARNING: OPENAI_API_KEY not found. LLM analysis will be disabled.")
            self.llm = None
            return

        try:
            self.llm = ChatOpenAI(temperature=0, model=model_name, api_key=api_key)
            self.parser = JsonOutputParser(pydantic_object=MarketSignal)
            
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a senior algorithmic Forex Trader and Global Macro Strategist. "
                           "Analyze the provided news article text and extract a distinct trading signal "
                           "for the relevant currency pair. "
                           "Focus on interest rate differentials, central bank policy, and geotechnical risks. "
                           "Ignore fluff. If the news is irrelevant or old, output NEUTRAL. "
                           "\n{format_instructions}"),
                ("user", "News Article Content:\n{article_text}")
            ])
            
            self.chain = self.prompt | self.llm | self.parser
            print(f"[LLM] Initialized with model {model_name}")
            
        except Exception as e:
            print(f"[LLM] Failed to initialize: {e}")
            self.llm = None

    def analyze_article(self, article_text):
        """
        Analyzes the full text of an article and returns a signal.
        """
        if not self.llm:
            return None

        try:
            print("[LLM] Analyzing article...")
            result = self.chain.invoke({
                "article_text": article_text[:4000], # Trucate to avoid context limits if minimal
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Normalize confidence to 0-1
            # (Result should already be 0-1 based on instructions, but sanity check)
            
            return result
        except Exception as e:
            print(f"[LLM] Analysis failed: {e}")
            return None
