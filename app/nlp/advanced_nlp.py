"""
Advanced NLP Analytics Module
==============================

Enhanced NLP capabilities including:
- Topic modeling (LDA)
- Emoji sentiment mapping
- Named entity recognition
- Keyword extraction
- Text statistics
"""

from typing import Dict, List, Tuple, Optional, Any
import re
from collections import Counter, defaultdict
import functools

# Optional advanced NLP libraries
try:
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ============================================================================
# EMOJI SENTIMENT MAPPING
# ============================================================================

EMOJI_SENTIMENT_MAP = {
    # Very Positive
    '❤️': 1.0, '😍': 1.0, '🥰': 1.0, '😘': 1.0, '💕': 1.0, '💖': 1.0, '💗': 1.0,
    '🤩': 1.0, '🌟': 1.0, '✨': 1.0, '🎉': 1.0, '🎊': 1.0, '🏆': 1.0, '🥇': 1.0,

    # Positive
    '😊': 0.8, '😀': 0.8, '😃': 0.8, '😄': 0.8, '😁': 0.8, '😆': 0.8, '🙂': 0.8,
    '👍': 0.8, '👏': 0.8, '🙌': 0.8, '💪': 0.8, '🔥': 0.8, '💯': 0.8, '✅': 0.8,
    '😎': 0.7, '🤗': 0.7, '😇': 0.7, '🌈': 0.7, '🌻': 0.7, '🌺': 0.7, '🌸': 0.7,

    # Slightly Positive
    '🙏': 0.5, '🤝': 0.5, '👌': 0.5, '✌️': 0.5, '🎵': 0.5, '🎶': 0.5, '📈': 0.5,

    # Neutral/Ambiguous
    '😐': 0.0, '😑': 0.0, '🤔': 0.0, '🧐': 0.0, '😶': 0.0, '🙃': 0.0,

    # Slightly Negative
    '😕': -0.4, '🤨': -0.4, '😬': -0.4, '😓': -0.5, '😥': -0.5, '😰': -0.5,

    # Negative
    '😞': -0.7, '😔': -0.7, '😟': -0.7, '🙁': -0.7, '☹️': -0.7, '😣': -0.7,
    '😖': -0.7, '😫': -0.7, '😩': -0.7, '😢': -0.8, '😭': -0.8, '😪': -0.6,
    '👎': -0.8, '😤': -0.7, '😠': -0.8, '😡': -0.9, '🤬': -1.0, '💔': -0.9,

    # Very Negative
    '😱': -1.0, '😨': -1.0, '🤮': -1.0, '🤢': -1.0, '😷': -0.7,

    # Surprise (context-dependent, default neutral)
    '😲': 0.0, '😯': 0.0, '😮': 0.0, '😧': -0.3,

    # Laughing (positive)
    '😂': 0.9, '🤣': 0.9, '😹': 0.9,
}


def get_emoji_sentiment(emoji: str) -> float:
    """
    Get sentiment score for an emoji.

    Args:
        emoji: Single emoji character

    Returns:
        Sentiment score (-1.0 to 1.0)
    """
    return EMOJI_SENTIMENT_MAP.get(emoji, 0.0)


def analyze_text_emojis(text: str) -> Dict[str, Any]:
    """
    Analyze emojis in text and their sentiment contribution.

    Args:
        text: Text containing emojis

    Returns:
        Dictionary with emoji analysis
    """
    # Find all emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "]+", flags=re.UNICODE)

    emojis = emoji_pattern.findall(text)

    if not emojis:
        return {
            'emoji_count': 0,
            'unique_emojis': 0,
            'emoji_sentiment_score': 0.0,
            'emoji_sentiment_label': 'neutral',
            'emojis': [],
            'sentiment_contribution': 0.0
        }

    emoji_counts = Counter(emojis)
    total_sentiment = 0.0
    emoji_details = []

    for emoji, count in emoji_counts.items():
        sentiment = get_emoji_sentiment(emoji)
        total_sentiment += sentiment * count
        emoji_details.append({
            'emoji': emoji,
            'count': count,
            'sentiment': sentiment
        })

    # Calculate average sentiment
    total_emojis = len(emojis)
    avg_sentiment = total_sentiment / total_emojis if total_emojis > 0 else 0.0

    # Determine label
    if avg_sentiment > 0.3:
        label = 'positive'
    elif avg_sentiment < -0.3:
        label = 'negative'
    else:
        label = 'neutral'

    # Sort by count
    emoji_details.sort(key=lambda x: x['count'], reverse=True)

    return {
        'emoji_count': total_emojis,
        'unique_emojis': len(emoji_counts),
        'emoji_sentiment_score': avg_sentiment,
        'emoji_sentiment_label': label,
        'emojis': emoji_details,
        'sentiment_contribution': total_sentiment
    }


# ============================================================================
# TOPIC MODELING
# ============================================================================

class TopicModeler:
    """
    Topic modeling using LDA (Latent Dirichlet Allocation).
    """

    def __init__(self,
                 n_topics: int = 5,
                 max_features: int = 1000,
                 min_df: int = 2,
                 max_df: float = 0.8):
        """
        Initialize topic modeler.

        Args:
            n_topics: Number of topics to extract
            max_features: Maximum number of features (words)
            min_df: Minimum document frequency
            max_df: Maximum document frequency
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("sklearn is required for topic modeling. Install with: pip install scikit-learn")

        self.n_topics = n_topics
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df

        self.vectorizer = None
        self.lda_model = None
        self.feature_names = None

    def fit(self, texts: List[str]) -> 'TopicModeler':
        """
        Fit topic model on texts.

        Args:
            texts: List of text documents

        Returns:
            Self for chaining
        """
        # Create document-term matrix
        self.vectorizer = CountVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words=None,  # We handle stopwords separately
            token_pattern=r'\b\w+\b'
        )

        doc_term_matrix = self.vectorizer.fit_transform(texts)
        self.feature_names = self.vectorizer.get_feature_names_out()

        # Fit LDA model
        self.lda_model = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=42,
            max_iter=20,
            learning_method='online',
            n_jobs=-1
        )

        self.lda_model.fit(doc_term_matrix)

        return self

    def get_topics(self, top_n_words: int = 10) -> List[Dict[str, Any]]:
        """
        Get extracted topics with top words.

        Args:
            top_n_words: Number of top words per topic

        Returns:
            List of topics with their top words
        """
        if self.lda_model is None:
            return []

        topics = []

        for topic_idx, topic in enumerate(self.lda_model.components_):
            # Get top word indices
            top_indices = topic.argsort()[-top_n_words:][::-1]
            top_words = [self.feature_names[i] for i in top_indices]
            top_weights = [topic[i] for i in top_indices]

            topics.append({
                'topic_id': topic_idx,
                'words': top_words,
                'weights': top_weights.tolist(),
                'word_weight_pairs': list(zip(top_words, top_weights.tolist()))
            })

        return topics

    def get_document_topics(self, texts: List[str]) -> List[List[Tuple[int, float]]]:
        """
        Get topic distribution for documents.

        Args:
            texts: List of text documents

        Returns:
            List of topic distributions (topic_id, probability) for each document
        """
        if self.lda_model is None or self.vectorizer is None:
            return []

        doc_term_matrix = self.vectorizer.transform(texts)
        doc_topics = self.lda_model.transform(doc_term_matrix)

        result = []
        for doc_topic_dist in doc_topics:
            doc_topics_sorted = sorted(enumerate(doc_topic_dist), key=lambda x: x[1], reverse=True)
            result.append(doc_topics_sorted)

        return result


def extract_topics_from_texts(
    texts: List[str],
    n_topics: int = 5,
    top_n_words: int = 10
) -> List[Dict[str, Any]]:
    """
    Extract topics from a corpus of texts.

    Args:
        texts: List of text documents
        n_topics: Number of topics to extract
        top_n_words: Number of top words per topic

    Returns:
        List of topics with their top words
    """
    if not SKLEARN_AVAILABLE:
        return []

    if not texts or len(texts) < 2:
        return []

    try:
        modeler = TopicModeler(n_topics=min(n_topics, len(texts)))
        modeler.fit(texts)
        return modeler.get_topics(top_n_words=top_n_words)
    except Exception as e:
        print(f"Topic modeling error: {e}")
        return []


# ============================================================================
# KEYWORD EXTRACTION
# ============================================================================

def extract_keywords_tfidf(
    texts: List[str],
    top_n: int = 20,
    min_df: int = 2,
    max_df: float = 0.8
) -> List[Tuple[str, float]]:
    """
    Extract keywords using TF-IDF.

    Args:
        texts: List of text documents
        top_n: Number of top keywords to return
        min_df: Minimum document frequency
        max_df: Maximum document frequency

    Returns:
        List of (keyword, score) tuples
    """
    if not SKLEARN_AVAILABLE:
        return []

    if not texts:
        return []

    try:
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=min_df,
            max_df=max_df,
            stop_words=None,
            token_pattern=r'\b\w+\b'
        )

        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        # Sum TF-IDF scores across all documents
        tfidf_scores = tfidf_matrix.sum(axis=0).A1

        # Get top keywords
        top_indices = tfidf_scores.argsort()[-top_n:][::-1]
        keywords = [(feature_names[i], tfidf_scores[i]) for i in top_indices]

        return keywords
    except Exception as e:
        print(f"Keyword extraction error: {e}")
        return []


# ============================================================================
# TEXT STATISTICS
# ============================================================================

def calculate_text_statistics(texts: List[str]) -> Dict[str, Any]:
    """
    Calculate comprehensive text statistics.

    Args:
        texts: List of text documents

    Returns:
        Dictionary with text statistics
    """
    if not texts:
        return {
            'total_texts': 0,
            'total_words': 0,
            'total_chars': 0,
            'avg_text_length': 0.0,
            'avg_word_count': 0.0,
            'unique_words': 0,
            'vocabulary_richness': 0.0
        }

    total_words = 0
    total_chars = 0
    all_words = []

    for text in texts:
        words = text.split()
        total_words += len(words)
        total_chars += len(text)
        all_words.extend(words)

    unique_words = len(set(all_words))
    vocabulary_richness = unique_words / total_words if total_words > 0 else 0.0

    return {
        'total_texts': len(texts),
        'total_words': total_words,
        'total_chars': total_chars,
        'avg_text_length': total_chars / len(texts),
        'avg_word_count': total_words / len(texts),
        'unique_words': unique_words,
        'vocabulary_richness': vocabulary_richness
    }


# ============================================================================
# ENHANCED SENTIMENT WITH EMOJI INTEGRATION
# ============================================================================

def analyze_text_with_emoji_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze text sentiment including emoji contribution.

    Args:
        text: Text to analyze

    Returns:
        Combined sentiment analysis
    """
    from app.nlp.sentiment_analyzer import analyze_sentiment_phrases_detailed

    # Get text sentiment
    text_sentiment = analyze_sentiment_phrases_detailed(text)

    # Get emoji sentiment
    emoji_analysis = analyze_text_emojis(text)

    # Combine scores (weight: 70% text, 30% emoji)
    text_weight = 0.7
    emoji_weight = 0.3

    combined_score = (
        text_sentiment['overall_score'] * text_weight +
        emoji_analysis['emoji_sentiment_score'] * emoji_weight
    )

    # Determine combined label
    if combined_score > 0.3:
        combined_label = 'positive'
    elif combined_score < -0.3:
        combined_label = 'negative'
    else:
        combined_label = 'neutral'

    return {
        'text_sentiment': text_sentiment,
        'emoji_sentiment': emoji_analysis,
        'combined_score': combined_score,
        'combined_label': combined_label,
        'emoji_contribution': emoji_analysis['sentiment_contribution']
    }


# ============================================================================
# BATCH ANALYSIS
# ============================================================================

def analyze_corpus_advanced(texts: List[str]) -> Dict[str, Any]:
    """
    Comprehensive analysis of a text corpus.

    Args:
        texts: List of text documents

    Returns:
        Complete analysis results
    """
    results = {
        'statistics': calculate_text_statistics(texts),
        'topics': extract_topics_from_texts(texts, n_topics=5, top_n_words=10),
        'keywords': extract_keywords_tfidf(texts, top_n=20),
        'emoji_analysis': {},
        'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
    }

    # Analyze emojis across corpus
    all_emojis = []
    emoji_sentiment_total = 0.0

    for text in texts:
        emoji_data = analyze_text_emojis(text)
        all_emojis.extend(emoji_data['emojis'])
        emoji_sentiment_total += emoji_data['emoji_sentiment_score']

    if all_emojis:
        emoji_counter = Counter()
        for emoji_info in all_emojis:
            emoji_counter[emoji_info['emoji']] += emoji_info['count']

        results['emoji_analysis'] = {
            'total_emojis': sum(emoji_counter.values()),
            'unique_emojis': len(emoji_counter),
            'avg_sentiment': emoji_sentiment_total / len(texts),
            'top_emojis': [{'emoji': e, 'count': c} for e, c in emoji_counter.most_common(15)]
        }

    return results
