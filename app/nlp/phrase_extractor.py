"""
Phrase Extraction Module for Enhanced Sentiment Analysis
=======================================================

This module provides advanced phrase extraction capabilities to improve
sentiment analysis accuracy by capturing meaningful multi-word expressions
instead of individual words.

Features:
- N-gram extraction (bigrams, trigrams)
- Collocation detection using statistical measures
- Arabic and English phrase processing
- Stopword filtering and phrase validation
- Performance optimization with caching
"""

import re
import math
from typing import List, Dict, Tuple, Set, Optional
from collections import Counter, defaultdict
import functools

# Arabic text processing patterns (reused from main app)
ARABIC_LETTERS = r"\u0621-\u064A\u0660-\u0669"
TOKEN_RE = re.compile(fr"[{ARABIC_LETTERS}A-Za-z0-9]+", re.UNICODE)
ARABIC_DIACRITICS = re.compile("""
        ّ    | # Tashdid
        َ    | # Fatha
        ً    | # Tanwin Fath
        ُ    | # Damma
        ٌ    | # Tanwin Damm
        ِ    | # Kasra
        ٍ    | # Tanwin Kasr
        ْ    | # Sukun
        ـ     # Tatwil/Kashida
    """, re.VERBOSE)

# Comprehensive stopwords for phrase filtering
ENGLISH_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'must', 'can', 'shall', 'this', 'that', 'these', 'those',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
    'am', 'is', 'are', 'was', 'were', 'being', 'been', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'here', 'there', 'where', 'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 'just', 'now', 'then', 'up', 'down', 'out', 'off',
    'over', 'under', 'again', 'further', 'once', 'twice', 'thrice'
}

ARABIC_STOPWORDS = {
    'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي',
    'أن', 'أو', 'لا', 'نعم', 'كان', 'يكون', 'ما', 'هل', 'قد', 'لقد',
    'عن', 'مع', 'بعد', 'قبل', 'عند', 'كل', 'بين', 'حتى', 'لكن', 'ثم',
    'و', 'أو', 'لم', 'لن', 'إن', 'أن', 'كما', 'لماذا', 'كيف', 'أين',
    'متى', 'أين', 'متى', 'كيف', 'لماذا', 'أي', 'أيها', 'أيتها', 'هؤلاء',
    'هذا', 'هذه', 'ذلك', 'تلك', 'هؤلاء', 'أولئك', 'التي', 'الذي', 'اللذان',
    'اللتان', 'الذين', 'اللاتي', 'اللائي', 'اللذين', 'اللتين'
}

# Combined stopwords
ALL_STOPWORDS = ENGLISH_STOPWORDS | ARABIC_STOPWORDS

# Common meaningless phrases to filter out
MEANINGLESS_PHRASES = {
    'في في', 'من من', 'على على', 'هذا هذا', 'هذه هذه',
    'the the', 'and and', 'or or', 'but but', 'in in', 'on on',
    'at at', 'to to', 'for for', 'of of', 'with with', 'by by'
}

# Important sentiment phrases that should be preserved as single units
SENTIMENT_PHRASES = {
    # English sentiment phrases
    'thank you', 'very good', 'very bad', 'not good', 'not bad', 'so good', 'so bad',
    'really good', 'really bad', 'pretty good', 'pretty bad', 'quite good', 'quite bad',
    'absolutely amazing', 'absolutely terrible', 'totally awesome', 'totally awful',
    'love it', 'hate it', 'like it', 'dislike it', 'enjoy it', 'enjoyed it',
    'great job', 'good job', 'bad job', 'nice work', 'excellent work', 'poor work',
    'well done', 'good work', 'bad work', 'amazing work', 'terrible work',
    'highly recommend', 'strongly recommend', 'definitely recommend', 'would recommend',
    'highly rated', 'well rated', 'poorly rated', 'badly rated',
    'top quality', 'high quality', 'low quality', 'poor quality', 'excellent quality',
    'worth it', 'not worth it', 'worthless', 'valuable', 'useless', 'helpful',
    'user friendly', 'easy to use', 'hard to use', 'difficult to use',
    'fast delivery', 'slow delivery', 'quick response', 'slow response',
    'customer service', 'great service', 'poor service', 'excellent service',
    'best ever', 'worst ever', 'never again', 'always good', 'always bad',
    
    # Arabic sentiment phrases
    'شكراً لك', 'شكرا لك', 'شكراً', 'شكرا', 'مشكور', 'مشكورة',
    'جيد جداً', 'جيد جدا', 'ممتاز جداً', 'ممتاز جدا', 'رائع جداً', 'رائع جدا',
    'سيء جداً', 'سيء جدا', 'مروع جداً', 'مروع جدا', 'فظيع جداً', 'فظيع جدا',
    'ليس جيد', 'ليس سيء', 'ليس ممتاز', 'ليس رائع', 'ليس مروع',
    'أحب هذا', 'أكره هذا', 'أعجبني', 'لم يعجبني', 'استمتعت', 'لم أستمتع',
    'عمل رائع', 'عمل جيد', 'عمل سيء', 'عمل ممتاز', 'عمل مروع',
    'خدمة ممتازة', 'خدمة جيدة', 'خدمة سيئة', 'خدمة رائعة', 'خدمة مروعة',
    'جودة عالية', 'جودة منخفضة', 'جودة ممتازة', 'جودة سيئة',
    'يستحق', 'لا يستحق', 'مفيد', 'غير مفيد', 'قيم', 'عديم القيمة',
    'سهل الاستخدام', 'صعب الاستخدام', 'سريع', 'بطيء', 'ممتاز', 'مروع',
    'أفضل شيء', 'أسوأ شيء', 'أبداً مرة أخرى', 'دائماً جيد', 'دائماً سيء'
}

class PhraseExtractor:
    """
    Advanced phrase extractor for sentiment analysis.
    
    Extracts meaningful phrases from text using n-gram analysis and
    statistical collocation detection.
    """
    
    def __init__(self, 
                 min_frequency: int = 2,
                 min_pmi: float = 1.0,
                 max_phrase_length: int = 3,
                 language: str = 'auto'):
        """
        Initialize phrase extractor.
        
        Args:
            min_frequency: Minimum frequency for phrases to be considered
            min_pmi: Minimum Pointwise Mutual Information score
            max_phrase_length: Maximum number of words in a phrase
            language: Language mode ('ar', 'en', 'auto')
        """
        self.min_frequency = min_frequency
        self.min_pmi = min_pmi
        self.max_phrase_length = max_phrase_length
        self.language = language
        
        # Cache for performance
        self._phrase_cache = {}
        self._ngram_cache = {}
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing diacritics, URLs, and extra whitespace."""
        if not text:
            return ""
        
        # Remove diacritics
        text = ARABIC_DIACRITICS.sub('', text)
        
        # Remove URLs and mentions
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[@#]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def preserve_sentiment_phrases(self, text: str) -> tuple:
        """
        Pre-process text to preserve important sentiment phrases as single units.
        
        This method replaces sentiment phrases with placeholders to prevent
        them from being split during tokenization.
        """
        if not text:
            return "", {}
        
        # Create a mapping of phrases to placeholders
        phrase_placeholders = {}
        processed_text = text.lower()
        
        # Sort phrases by length (longest first) to avoid partial replacements
        sorted_phrases = sorted(SENTIMENT_PHRASES, key=len, reverse=True)
        
        for i, phrase in enumerate(sorted_phrases):
            if phrase in processed_text:
                placeholder = f"__SENTIMENT_PHRASE_{i}__"
                phrase_placeholders[placeholder] = phrase
                processed_text = processed_text.replace(phrase, placeholder)
        
        return processed_text, phrase_placeholders
    
    def restore_sentiment_phrases(self, tokens: List[str], phrase_placeholders: Dict[str, str]) -> List[str]:
        """
        Restore sentiment phrases from placeholders after tokenization.
        """
        restored_tokens = []
        
        for token in tokens:
            if token in phrase_placeholders:
                # Replace placeholder with the original phrase
                phrase = phrase_placeholders[token]
                restored_tokens.append(phrase)
            else:
                restored_tokens.append(token)
        
        return restored_tokens
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words, filtering stopwords and preserving sentiment phrases."""
        # First preserve sentiment phrases
        processed_text, phrase_placeholders = self.preserve_sentiment_phrases(text)
        
        # Clean the text
        processed_text = self.clean_text(processed_text)
        
        # Tokenize
        tokens = TOKEN_RE.findall(processed_text)
        
        # Filter stopwords and short tokens
        filtered_tokens = [
            token.lower() for token in tokens 
            if (token.lower() not in ALL_STOPWORDS and 
                len(token) > 2 and 
                not token.isdigit())
        ]
        
        # Restore sentiment phrases
        restored_tokens = self.restore_sentiment_phrases(filtered_tokens, phrase_placeholders)
        
        return restored_tokens
    
    def extract_ngrams(self, tokens: List[str], n: int) -> List[Tuple[str, ...]]:
        """Extract n-grams from tokenized text."""
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    def calculate_pmi(self, phrase: Tuple[str, ...], word_freqs: Dict[str, int], 
                     total_words: int) -> float:
        """
        Calculate Pointwise Mutual Information for a phrase.
        
        PMI measures how much more likely the words appear together
        than if they were independent.
        """
        if len(phrase) < 2:
            return 0.0
        
        # Calculate joint probability
        phrase_text = ' '.join(phrase)
        phrase_freq = word_freqs.get(phrase_text, 0)
        if phrase_freq == 0:
            return 0.0
        
        joint_prob = phrase_freq / total_words
        
        # Calculate individual word probabilities
        word_probs = []
        for word in phrase:
            word_freq = word_freqs.get(word, 0)
            if word_freq == 0:
                return 0.0
            word_probs.append(word_freq / total_words)
        
        # Calculate PMI
        independent_prob = 1.0
        for prob in word_probs:
            independent_prob *= prob
        
        if independent_prob == 0:
            return 0.0
        
        pmi = math.log2(joint_prob / independent_prob)
        return pmi
    
    def is_meaningful_phrase(self, phrase: Tuple[str, ...]) -> bool:
        """Check if a phrase is meaningful and not just noise."""
        phrase_text = ' '.join(phrase)
        
        # Check against meaningless phrases
        if phrase_text in MEANINGLESS_PHRASES:
            return False
        
        # Check for repeated words
        if len(set(phrase)) < len(phrase):
            return False
        
        # Check for very short words (likely noise)
        if any(len(word) < 2 for word in phrase):
            return False
        
        return True
    
    @functools.lru_cache(maxsize=1000)
    def extract_phrases_from_text(self, text: str) -> Dict[str, int]:
        """
        Extract meaningful phrases from a single text.
        
        Returns:
            Dictionary mapping phrases to their frequencies
        """
        tokens = self.tokenize_text(text)
        if len(tokens) < 2:
            return {}
        
        phrase_freqs = {}
        
        # Extract n-grams of different lengths
        for n in range(2, min(self.max_phrase_length + 1, len(tokens) + 1)):
            ngrams = self.extract_ngrams(tokens, n)
            
            for ngram in ngrams:
                if self.is_meaningful_phrase(ngram):
                    phrase = ' '.join(ngram)
                    phrase_freqs[phrase] = phrase_freqs.get(phrase, 0) + 1
        
        return phrase_freqs
    
    def extract_phrases_from_corpus(self, texts: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Extract phrases from a corpus of texts with statistical validation.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            Dictionary with phrase statistics:
            {
                'phrases': {phrase: frequency},
                'word_freqs': {word: frequency},
                'total_words': int,
                'pmi_scores': {phrase: pmi_score}
            }
        """
        # Collect all phrases and word frequencies
        all_phrases = Counter()
        word_freqs = Counter()
        total_words = 0
        
        for text in texts:
            if not text or not text.strip():
                continue
                
            # Extract phrases from this text
            text_phrases = self.extract_phrases_from_text(text)
            for phrase, freq in text_phrases.items():
                all_phrases[phrase] += freq
            
            # Extract individual words for PMI calculation
            tokens = self.tokenize_text(text)
            for token in tokens:
                word_freqs[token] += 1
                total_words += 1
        
        # Calculate PMI scores for phrases
        pmi_scores = {}
        validated_phrases = {}
        
        for phrase, freq in all_phrases.items():
            if freq >= self.min_frequency:
                phrase_tokens = tuple(phrase.split())
                pmi = self.calculate_pmi(phrase_tokens, dict(word_freqs), total_words)
                pmi_scores[phrase] = pmi
                
                if pmi >= self.min_pmi:
                    validated_phrases[phrase] = freq
        
        return {
            'phrases': validated_phrases,
            'word_freqs': dict(word_freqs),
            'total_words': total_words,
            'pmi_scores': pmi_scores
        }
    
    def get_top_phrases(self, texts: List[str], top_n: int = 50) -> Dict[str, int]:
        """
        Get top phrases from a corpus of texts.
        
        Args:
            texts: List of text strings
            top_n: Number of top phrases to return
            
        Returns:
            Dictionary of top phrases with their frequencies
        """
        corpus_stats = self.extract_phrases_from_corpus(texts)
        phrases = corpus_stats['phrases']
        
        # Sort by frequency and return top N
        sorted_phrases = sorted(phrases.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_phrases[:top_n])
    
    def extract_phrases_with_sentiment_context(self, texts: List[str]) -> Dict[str, Dict]:
        """
        Extract phrases with additional context for sentiment analysis.
        
        Returns:
            Dictionary with phrase information including context:
            {
                phrase: {
                    'frequency': int,
                    'pmi_score': float,
                    'contexts': [list of surrounding words],
                    'sentiment_hints': [list of sentiment indicators]
                }
            }
        """
        corpus_stats = self.extract_phrases_from_corpus(texts)
        phrases = corpus_stats['phrases']
        pmi_scores = corpus_stats['pmi_scores']
        
        enhanced_phrases = {}
        
        for phrase, freq in phrases.items():
            enhanced_phrases[phrase] = {
                'frequency': freq,
                'pmi_score': pmi_scores.get(phrase, 0.0),
                'contexts': self._extract_phrase_contexts(phrase, texts),
                'sentiment_hints': self._extract_sentiment_hints(phrase, texts)
            }
        
        return enhanced_phrases
    
    def _extract_phrase_contexts(self, phrase: str, texts: List[str]) -> List[str]:
        """Extract surrounding context for a phrase."""
        contexts = []
        phrase_words = phrase.split()
        
        for text in texts:
            tokens = self.tokenize_text(text)
            for i in range(len(tokens) - len(phrase_words) + 1):
                if tuple(tokens[i:i+len(phrase_words)]) == tuple(phrase_words):
                    # Extract context (2 words before and after)
                    start = max(0, i - 2)
                    end = min(len(tokens), i + len(phrase_words) + 2)
                    context = ' '.join(tokens[start:end])
                    contexts.append(context)
        
        return contexts[:10]  # Limit to 10 contexts
    
    def _extract_sentiment_hints(self, phrase: str, texts: List[str]) -> List[str]:
        """Extract sentiment-related words that appear near the phrase."""
        sentiment_hints = []
        phrase_words = phrase.split()
        
        # Common sentiment indicators
        sentiment_words = {
            'very', 'really', 'quite', 'extremely', 'absolutely', 'totally',
            'not', 'never', 'no', 'nothing', 'nobody', 'nowhere',
            'always', 'all', 'every', 'completely', 'perfectly',
            'جدا', 'حقا', 'تماما', 'مطلقا', 'كليا', 'لا', 'لم', 'لن', 'ليس'
        }
        
        for text in texts:
            tokens = self.tokenize_text(text)
            for i in range(len(tokens) - len(phrase_words) + 1):
                if tuple(tokens[i:i+len(phrase_words)]) == tuple(phrase_words):
                    # Look for sentiment words in nearby context
                    start = max(0, i - 3)
                    end = min(len(tokens), i + len(phrase_words) + 3)
                    context_tokens = tokens[start:end]
                    
                    for token in context_tokens:
                        if token in sentiment_words:
                            sentiment_hints.append(token)
        
        return list(set(sentiment_hints))  # Remove duplicates


# Convenience functions for easy integration
def extract_phrases_simple(texts: List[str], top_n: int = 50) -> Dict[str, int]:
    """
    Simple phrase extraction function for quick integration.
    
    Args:
        texts: List of text strings
        top_n: Number of top phrases to return
        
    Returns:
        Dictionary of top phrases with frequencies
    """
    extractor = PhraseExtractor()
    return extractor.get_top_phrases(texts, top_n)


def extract_phrases_advanced(texts: List[str], top_n: int = 50) -> Dict[str, Dict]:
    """
    Advanced phrase extraction with sentiment context.
    
    Args:
        texts: List of text strings
        top_n: Number of top phrases to return
        
    Returns:
        Dictionary with detailed phrase information
    """
    extractor = PhraseExtractor()
    phrases = extractor.extract_phrases_with_sentiment_context(texts)
    
    # Sort by frequency and return top N
    sorted_phrases = sorted(phrases.items(), key=lambda x: x[1]['frequency'], reverse=True)
    return dict(sorted_phrases[:top_n])
