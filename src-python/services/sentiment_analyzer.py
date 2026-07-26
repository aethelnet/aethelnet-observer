"""
Sentiment Analyzer Service
Analyzes sentiment of news items using keyword-based and optional ML approaches
"""

import logging
import re
from typing import Dict, Any, Optional, Tuple
import os

logger = logging.getLogger("SentimentAnalyzer")

class SentimentAnalyzer:
    """
    Analyzes sentiment of news items using multiple methods:
    - Keyword-based sentiment analysis
    - Optional ML libraries (TextBlob, VADER)
    - CryptoPanic votes (if available)
    - AlphaVantage sentiment (if API key available)
    """
    
    def __init__(self):
        # Positive keywords (bullish, positive sentiment)
        self.positive_keywords = [
            'bullish', 'surge', 'rally', 'gain', 'profit', 'growth', 'rise', 'up', 'increase',
            'breakthrough', 'success', 'win', 'positive', 'optimistic', 'strong', 'boom',
            'soar', 'jump', 'climb', 'advance', 'boost', 'improve', 'recover', 'rebound',
            'approval', 'adoption', 'partnership', 'launch', 'upgrade', 'expansion',
            'record', 'high', 'peak', 'milestone', 'achievement', 'breakout'
        ]
        
        # Negative keywords (bearish, negative sentiment)
        self.negative_keywords = [
            'bearish', 'crash', 'drop', 'fall', 'loss', 'decline', 'down', 'decrease',
            'failure', 'negative', 'pessimistic', 'weak', 'bust', 'plunge', 'sink',
            'dip', 'slump', 'retreat', 'worry', 'concern', 'risk', 'threat', 'problem',
            'rejection', 'ban', 'hack', 'attack', 'scam', 'fraud', 'lawsuit', 'regulation',
            'low', 'bottom', 'crash', 'panic', 'fear', 'uncertainty', 'volatility'
        ]
        
        # Neutral/uncertain keywords
        self.neutral_keywords = [
            'stable', 'unchanged', 'flat', 'neutral', 'mixed', 'uncertain', 'wait',
            'monitor', 'observe', 'analysis', 'report', 'update', 'announcement'
        ]
        
        # Try to import optional ML libraries
        self.textblob_available = False
        self.vader_available = False
        
        try:
            from textblob import TextBlob
            self.textblob_available = True
            self.TextBlob = TextBlob
        except ImportError:
            logger.debug("TextBlob not available - using keyword-based analysis only")
        
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader_available = True
            self.vader_analyzer = SentimentIntensityAnalyzer()
        except ImportError:
            logger.debug("VADER not available - using keyword-based analysis only")
    
    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Tuple of (sentiment_score, sentiment_label)
            sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
            sentiment_label: 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'
        """
        if not text or not text.strip():
            return 0.0, 'NEUTRAL'
        
        text_lower = text.lower()
        scores = []
        
        # 1. Keyword-based analysis
        keyword_score = self._keyword_analysis(text_lower)
        if keyword_score is not None:
            scores.append(keyword_score)
        
        # 2. ML-based analysis (if available)
        if self.vader_available:
            try:
                vader_score = self._vader_analysis(text)
                if vader_score is not None:
                    scores.append(vader_score)
            except Exception as e:
                logger.debug(f"VADER analysis error: {e}")
        
        if self.textblob_available:
            try:
                textblob_score = self._textblob_analysis(text)
                if textblob_score is not None:
                    scores.append(textblob_score)
            except Exception as e:
                logger.debug(f"TextBlob analysis error: {e}")
        
        # Average the scores
        if scores:
            final_score = sum(scores) / len(scores)
        else:
            final_score = 0.0
        
        # Determine label
        if final_score > 0.2:
            label = 'POSITIVE'
        elif final_score < -0.2:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        
        return final_score, label
    
    def _keyword_analysis(self, text: str) -> Optional[float]:
        """Keyword-based sentiment analysis."""
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)
        neutral_count = sum(1 for keyword in self.neutral_keywords if keyword in text)
        
        total = positive_count + negative_count + neutral_count
        if total == 0:
            return None
        
        # Calculate weighted score
        score = (positive_count - negative_count) / max(total, 1)
        
        # Normalize to -1.0 to 1.0 range
        score = max(-1.0, min(1.0, score))
        
        return score
    
    def _vader_analysis(self, text: str) -> Optional[float]:
        """VADER sentiment analysis."""
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            # VADER returns compound score from -1 to 1
            return scores.get('compound', 0.0)
        except Exception as e:
            logger.debug(f"VADER analysis error: {e}")
            return None
    
    def _textblob_analysis(self, text: str) -> Optional[float]:
        """TextBlob sentiment analysis."""
        try:
            blob = self.TextBlob(text)
            # TextBlob returns polarity from -1 to 1
            return blob.sentiment.polarity
        except Exception as e:
            logger.debug(f"TextBlob analysis error: {e}")
            return None
    
    def analyze_news_item(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment of a news item.
        
        Args:
            news_item: Dictionary containing news data with keys:
                - title: str (required)
                - content: str or summary (optional)
                - votes: dict (optional, for CryptoPanic)
                - ticker_sentiment: list (optional, for AlphaVantage)
        
        Returns:
            Dictionary with added sentiment fields:
                - sentiment: float (-1.0 to 1.0)
                - sentiment_label: str (POSITIVE/NEGATIVE/NEUTRAL)
        """
        try:
            # Combine title and content for analysis
            title = news_item.get('title', '')
            content = news_item.get('content', '') or news_item.get('summary', '') or ''
            text = f"{title} {content}".strip()
            
            # Check for external sentiment data first
            # CryptoPanic votes
            votes = news_item.get('votes', {})
            if votes and isinstance(votes, dict):
                positive = votes.get('positive', 0)
                negative = votes.get('negative', 0)
                total = positive + negative
                if total > 0:
                    # Convert votes to sentiment score (-1 to 1)
                    vote_score = (positive - negative) / total
                    sentiment_score = vote_score
                    sentiment_label = 'POSITIVE' if vote_score > 0.2 else 'NEGATIVE' if vote_score < -0.2 else 'NEUTRAL'
                    return {
                        'sentiment': sentiment_score,
                        'sentiment_label': sentiment_label
                    }
            
            # AlphaVantage ticker sentiment
            ticker_sentiment = news_item.get('ticker_sentiment', [])
            if ticker_sentiment and isinstance(ticker_sentiment, list):
                # Average sentiment scores from tickers
                scores = []
                for ticker in ticker_sentiment:
                    if isinstance(ticker, dict):
                        relevance = ticker.get('relevance_score', 0)
                        sentiment = ticker.get('ticker_sentiment_score', 0)
                        if relevance > 0.5:  # Only consider relevant tickers
                            scores.append(sentiment)
                if scores:
                    avg_sentiment = sum(scores) / len(scores)
                    sentiment_label = 'POSITIVE' if avg_sentiment > 0.2 else 'NEGATIVE' if avg_sentiment < -0.2 else 'NEUTRAL'
                    return {
                        'sentiment': avg_sentiment,
                        'sentiment_label': sentiment_label
                    }
            
            # Fall back to text analysis
            if text:
                sentiment_score, sentiment_label = self.analyze_sentiment(text)
                return {
                    'sentiment': sentiment_score,
                    'sentiment_label': sentiment_label
                }
            
            # Default to neutral if no data
            return {
                'sentiment': 0.0,
                'sentiment_label': 'NEUTRAL'
            }
            
        except Exception as e:
            logger.exception(f"Error analyzing news item sentiment: {e}")
            return {
                'sentiment': 0.0,
                'sentiment_label': 'NEUTRAL'
            }

# Singleton
_sentiment_analyzer_instance = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get the global sentiment analyzer instance (singleton)."""
    global _sentiment_analyzer_instance
    if _sentiment_analyzer_instance is None:
        _sentiment_analyzer_instance = SentimentAnalyzer()
    return _sentiment_analyzer_instance
