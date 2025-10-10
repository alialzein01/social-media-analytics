"""
Enhanced Sentiment Analysis with Phrase Support
===============================================

This module provides advanced sentiment analysis that works with phrases
instead of individual words, significantly improving accuracy for
multi-word expressions like "thank you", "very good", "not bad", etc.

Features:
- Phrase-based sentiment analysis
- Context-aware sentiment scoring
- Sentiment modifier handling (very, not, etc.)
- Arabic and English support
- Fallback to word-level analysis
- Performance optimization with caching
"""

import re
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter, defaultdict
import functools

# Import our phrase extraction and dictionary modules
from .phrase_extractor import PhraseExtractor, extract_phrases_simple
from ..utils.phrase_dictionaries import (
    get_phrase_sentiment_score, get_sentiment_modifiers,
    get_phrase_sentiment_label, is_positive_phrase, is_negative_phrase
)

# Original word-based sentiment sets (for fallback)
POSITIVE_WORDS = frozenset([
    'جيد', 'ممتاز', 'رائع', 'حلو', 'جميل', 'عظيم', 'مذهل', 'رائع',
    'good', 'great', 'love', 'excellent', 'amazing', 'wonderful', 'fantastic',
    'awesome', 'brilliant', 'perfect', 'outstanding', 'superb', 'marvelous',
    '❤️', '😊', '👍', '😍', '🤩', '🥰', '😘', '💕', '🌟', '✨'
])

NEGATIVE_WORDS = frozenset([
    'سيء', 'سئ', 'رديء', 'مروع', 'فظيع', 'رهيب', 'مخيب', 'محبط',
    'bad', 'hate', 'terrible', 'awful', 'horrible', 'disgusting', 'disappointing',
    'frustrating', 'annoying', 'boring', 'useless', 'worthless', 'pathetic',
    '😢', '😡', '👎', '😠', '😤', '😞', '😔', '😭', '🤬', '💔'
])

class PhraseSentimentAnalyzer:
    """
    Advanced sentiment analyzer that works with phrases.
    
    This analyzer first tries to match phrases, then falls back to
    word-level analysis for unmatched text portions.
    """
    
    def __init__(self, 
                 min_phrase_confidence: float = 0.6,
                 use_context_analysis: bool = True,
                 language: str = 'auto'):
        """
        Initialize the sentiment analyzer.
        
        Args:
            min_phrase_confidence: Minimum confidence for phrase matches
            use_context_analysis: Whether to use context for sentiment
            language: Language mode ('ar', 'en', 'auto')
        """
        self.min_phrase_confidence = min_phrase_confidence
        self.use_context_analysis = use_context_analysis
        self.language = language
        
        # Initialize phrase extractor
        self.phrase_extractor = PhraseExtractor(language=language)
        
        # Cache for performance
        self._sentiment_cache = {}
        self._phrase_cache = {}
    
    def clean_text(self, text: str) -> str:
        """Clean text for analysis."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove excessive punctuation but keep sentence structure
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{2,}', '.', text)
        
        return text.strip()
    
    def extract_phrases_from_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract phrases from text with their positions.
        
        Returns:
            List of (phrase, start_pos, end_pos) tuples
        """
        text = self.clean_text(text)
        tokens = self.phrase_extractor.tokenize_text(text)
        
        phrases = []
        
        # Extract n-grams of different lengths
        for n in range(2, min(self.phrase_extractor.max_phrase_length + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                phrase_tokens = tokens[i:i+n]
                phrase = ' '.join(phrase_tokens)
                
                if self.phrase_extractor.is_meaningful_phrase(tuple(phrase_tokens)):
                    # Find position in original text
                    start_pos = text.lower().find(phrase.lower())
                    if start_pos != -1:
                        end_pos = start_pos + len(phrase)
                        phrases.append((phrase, start_pos, end_pos))
        
        # Sort by position
        phrases.sort(key=lambda x: x[1])
        
        return phrases
    
    def analyze_phrase_sentiment(self, phrase: str) -> Tuple[float, str, float]:
        """
        Analyze sentiment of a single phrase.
        
        Returns:
            Tuple of (score, label, confidence)
        """
        # Check cache first
        if phrase in self._sentiment_cache:
            return self._sentiment_cache[phrase]
        
        # Get base sentiment score
        base_score = get_phrase_sentiment_score(phrase, self.language)
        base_label = get_phrase_sentiment_label(phrase, self.language)
        
        # Calculate confidence based on score magnitude
        confidence = abs(base_score)
        
        # Apply context analysis if enabled
        if self.use_context_analysis:
            context_score, context_confidence = self._analyze_phrase_context(phrase)
            if context_confidence > 0.5:
                # Weight the scores
                final_score = (base_score * 0.7) + (context_score * 0.3)
                final_confidence = (confidence * 0.7) + (context_confidence * 0.3)
            else:
                final_score = base_score
                final_confidence = confidence
        else:
            final_score = base_score
            final_confidence = confidence
        
        # Determine final label
        if final_score > 0.5:
            final_label = 'positive'
        elif final_score < -0.5:
            final_label = 'negative'
        else:
            final_label = 'neutral'
        
        result = (final_score, final_label, final_confidence)
        
        # Cache the result
        self._sentiment_cache[phrase] = result
        
        return result
    
    def _analyze_phrase_context(self, phrase: str) -> Tuple[float, float]:
        """
        Analyze context around a phrase for additional sentiment clues.
        
        Returns:
            Tuple of (context_score, confidence)
        """
        # This is a simplified context analysis
        # In a full implementation, you'd analyze surrounding words
        
        modifiers = get_sentiment_modifiers()
        phrase_words = phrase.lower().split()
        
        context_score = 0.0
        confidence = 0.0
        
        for word in phrase_words:
            if word in modifiers:
                modifier_strength = modifiers[word]
                context_score += modifier_strength * 0.1  # Small impact
                confidence += 0.2
        
        # Normalize
        if confidence > 0:
            context_score = max(-1.0, min(1.0, context_score))
            confidence = min(1.0, confidence)
        
        return context_score, confidence
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, Union[float, str, List]]:
        """
        Analyze sentiment of a text using phrase-based approach.
        
        Returns:
            Dictionary with sentiment analysis results:
            {
                'overall_score': float,
                'overall_label': str,
                'confidence': float,
                'phrases': [{'phrase': str, 'score': float, 'label': str, 'confidence': float}],
                'word_fallback': bool
            }
        """
        if not text or not text.strip():
            return {
                'overall_score': 0.0,
                'overall_label': 'neutral',
                'confidence': 0.0,
                'phrases': [],
                'word_fallback': False
            }
        
        text = self.clean_text(text)
        
        # Extract phrases
        phrases_with_positions = self.extract_phrases_from_text(text)
        
        # Analyze each phrase
        phrase_results = []
        total_score = 0.0
        total_confidence = 0.0
        phrase_count = 0
        
        for phrase, start_pos, end_pos in phrases_with_positions:
            score, label, confidence = self.analyze_phrase_sentiment(phrase)
            
            if confidence >= self.min_phrase_confidence:
                phrase_results.append({
                    'phrase': phrase,
                    'score': score,
                    'label': label,
                    'confidence': confidence,
                    'position': (start_pos, end_pos)
                })
                
                total_score += score * confidence
                total_confidence += confidence
                phrase_count += 1
        
        # Calculate overall sentiment
        if phrase_count > 0:
            overall_score = total_score / total_confidence if total_confidence > 0 else 0.0
            overall_confidence = total_confidence / phrase_count
            word_fallback = False
        else:
            # Fallback to word-level analysis
            overall_score, overall_confidence, word_fallback = self._analyze_word_sentiment(text)
            phrase_results = []
        
        # Determine overall label
        if overall_score > 0.5:
            overall_label = 'positive'
        elif overall_score < -0.5:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
        
        return {
            'overall_score': overall_score,
            'overall_label': overall_label,
            'confidence': overall_confidence,
            'phrases': phrase_results,
            'word_fallback': word_fallback
        }
    
    def _analyze_word_sentiment(self, text: str) -> Tuple[float, float, bool]:
        """
        Fallback word-level sentiment analysis.
        
        Returns:
            Tuple of (score, confidence, is_fallback)
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
        neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
        
        total_sentiment_words = pos_count + neg_count
        
        if total_sentiment_words == 0:
            return 0.0, 0.0, True
        
        # Calculate score
        if pos_count > neg_count:
            score = pos_count / total_sentiment_words
        elif neg_count > pos_count:
            score = -neg_count / total_sentiment_words
        else:
            score = 0.0
        
        # Calculate confidence based on word count
        confidence = min(1.0, total_sentiment_words / 10.0)
        
        return score, confidence, True
    
    def analyze_corpus_sentiment(self, texts: List[str]) -> Dict[str, Union[float, str, List, Dict]]:
        """
        Analyze sentiment for a corpus of texts.
        
        Returns:
            Dictionary with corpus-level sentiment analysis
        """
        if not texts:
            return {
                'overall_score': 0.0,
                'overall_label': 'neutral',
                'confidence': 0.0,
                'text_count': 0,
                'phrase_count': 0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'top_phrases': [],
                'individual_results': []
            }
        
        individual_results = []
        total_score = 0.0
        total_confidence = 0.0
        sentiment_counts = Counter()
        all_phrases = Counter()
        
        for text in texts:
            result = self.analyze_text_sentiment(text)
            individual_results.append(result)
            
            total_score += result['overall_score'] * result['confidence']
            total_confidence += result['confidence']
            sentiment_counts[result['overall_label']] += 1
            
            # Collect phrases
            for phrase_info in result['phrases']:
                all_phrases[phrase_info['phrase']] += 1
        
        # Calculate corpus-level metrics
        text_count = len(texts)
        phrase_count = sum(len(result['phrases']) for result in individual_results)
        
        if total_confidence > 0:
            overall_score = total_score / total_confidence
            overall_confidence = total_confidence / text_count
        else:
            overall_score = 0.0
            overall_confidence = 0.0
        
        # Determine overall label
        if overall_score > 0.5:
            overall_label = 'positive'
        elif overall_score < -0.5:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
        
        # Get top phrases
        top_phrases = [{'phrase': phrase, 'count': count} 
                      for phrase, count in all_phrases.most_common(10)]
        
        return {
            'overall_score': overall_score,
            'overall_label': overall_label,
            'confidence': overall_confidence,
            'text_count': text_count,
            'phrase_count': phrase_count,
            'sentiment_distribution': dict(sentiment_counts),
            'top_phrases': top_phrases,
            'individual_results': individual_results
        }
    
    @functools.lru_cache(maxsize=1000)
    def get_sentiment_label(self, text: str) -> str:
        """Get sentiment label for text (cached)."""
        result = self.analyze_text_sentiment(text)
        return result['overall_label']
    
    @functools.lru_cache(maxsize=1000)
    def get_sentiment_score(self, text: str) -> float:
        """Get sentiment score for text (cached)."""
        result = self.analyze_text_sentiment(text)
        return result['overall_score']


# Convenience functions for easy integration
def analyze_sentiment_phrases(text: str, language: str = 'auto') -> str:
    """
    Simple phrase-based sentiment analysis function.
    
    Args:
        text: Text to analyze
        language: Language code
        
    Returns:
        Sentiment label: 'positive', 'negative', or 'neutral'
    """
    analyzer = PhraseSentimentAnalyzer(language=language)
    return analyzer.get_sentiment_label(text)


def analyze_sentiment_phrases_detailed(text: str, language: str = 'auto') -> Dict:
    """
    Detailed phrase-based sentiment analysis.
    
    Args:
        text: Text to analyze
        language: Language code
        
    Returns:
        Detailed sentiment analysis results
    """
    analyzer = PhraseSentimentAnalyzer(language=language)
    return analyzer.analyze_text_sentiment(text)


def analyze_corpus_sentiment_phrases(texts: List[str], language: str = 'auto') -> Dict:
    """
    Analyze sentiment for a corpus of texts using phrases.
    
    Args:
        texts: List of texts to analyze
        language: Language code
        
    Returns:
        Corpus-level sentiment analysis results
    """
    analyzer = PhraseSentimentAnalyzer(language=language)
    return analyzer.analyze_corpus_sentiment(texts)
