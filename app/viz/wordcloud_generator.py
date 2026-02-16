"""
Enhanced Word Cloud Generator with Phrase Support
=================================================

This module provides advanced word cloud generation that can display
meaningful phrases instead of just individual words, with proper
formatting and sentiment-based coloring.

Features:
- Phrase-based word clouds
- Sentiment-based coloring
- Arabic text support with proper shaping
- Configurable styling and layout
- Performance optimization
"""

import re
import io
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from wordcloud import WordCloud
from collections import Counter
import numpy as np
import streamlit as st

# Import our phrase and sentiment modules
from ..nlp.phrase_extractor import PhraseExtractor, extract_phrases_simple
from ..nlp.sentiment_analyzer import PhraseSentimentAnalyzer, analyze_sentiment_phrases_detailed
from ..utils.phrase_dictionaries import get_phrase_sentiment_score, get_phrase_sentiment_label
from ..styles.theme import THEME_COLORS, SENTIMENT_COLORS

# Arabic text shaping support
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
    
    def reshape_arabic_text(text: str) -> str:
        """Reshape Arabic text for proper display."""
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
except ImportError:
    ARABIC_SUPPORT = False
    
    def reshape_arabic_text(text: str) -> str:
        """Fallback for Arabic text when shaping libraries are not available."""
        return text

DEFAULT_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "you", "your", "our", "from", "are",
    "was", "were", "have", "has", "had", "will", "can", "just", "about", "they", "them",
    "but", "not", "all", "out", "new", "more", "some", "when", "what", "who", "how",
    "http", "https", "www", "com", "amp", "rt", "u", "im", "dont", "didnt", "ive",
    "post", "posts", "video", "videos", "reel", "reels", "shorts", "content", "channel",
    "page", "profile", "follow", "followers", "following", "like", "likes", "comment",
    "comments", "share", "shares", "subscribe", "subscribers", "instagram", "facebook",
    "youtube", "tiktok", "social", "media", "link", "bio", "today", "tomorrow",
}

# Keep this list small and high-signal: remove platform boilerplate so thematic terms dominate.
DOMAIN_STOPWORDS = {
    "watch", "watched", "watching", "click", "clicked", "check", "checkout", "join",
    "support", "official", "account", "story", "stories", "caption", "captions",
}

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)

URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
NON_WORD_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
DIGIT_RE = re.compile(r"\d+")


@dataclass
class WordCloudConfig:
    max_words: int = 90
    min_frequency: int = 2
    include_bigrams: bool = True
    keep_hashtag_words: bool = True
    remove_emojis: bool = True
    lemmatize: bool = True
    width: int = 1800
    height: int = 900
    scale: float = 2.0
    background_mode: str = "theme"  # theme | transparent
    random_state: int = 42
    max_font_size: int = 170
    min_font_size: int = 12
    prefer_horizontal: float = 0.9
    contour_width: int = 0
    caption: str = "Top Themes in Content"
    section_key: str = "default_wordcloud"
    platform_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


def _apply_optional_filters(
    text_series: List[Any],
    platform_filter: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> List[str]:
    """
    Optionally filter when items are dict-like records with text/platform/date fields.
    Accepts plain string lists unchanged.
    """
    if not text_series:
        return []
    if not isinstance(text_series[0], dict):
        return [str(t) for t in text_series if str(t or "").strip()]

    start = None
    end = None
    try:
        start = np.datetime64(date_from) if date_from else None
        end = np.datetime64(date_to) if date_to else None
    except Exception:
        start = None
        end = None

    filtered: List[str] = []
    for row in text_series:
        text = row.get("text") or row.get("caption") or row.get("comment") or row.get("message")
        if not text:
            continue
        if platform_filter and str(row.get("platform", "")).lower() != platform_filter.lower():
            continue
        if start is not None or end is not None:
            raw_date = row.get("published_at") or row.get("date")
            try:
                dt = np.datetime64(str(raw_date))
                if start is not None and dt < start:
                    continue
                if end is not None and dt > end:
                    continue
            except Exception:
                continue
        filtered.append(str(text))
    return filtered


def _safe_wordnet_lemmatizer():
    """Try to load NLTK lemmatizer; silently fall back if unavailable."""
    try:
        from nltk.stem import WordNetLemmatizer  # type: ignore
        return WordNetLemmatizer()
    except Exception:
        return None


def _lemmatize_token(token: str, lemmatizer: Any) -> str:
    if not token:
        return token
    if lemmatizer is not None:
        try:
            return lemmatizer.lemmatize(token)
        except Exception:
            pass

    # Lightweight fallback for common English endings
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]
    return token


def _prepare_text(text: str, cfg: WordCloudConfig) -> str:
    text = str(text or "").lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    if cfg.keep_hashtag_words:
        text = HASHTAG_RE.sub(r" \1 ", text)
    else:
        text = HASHTAG_RE.sub(" ", text)
    if cfg.remove_emojis:
        text = EMOJI_RE.sub(" ", text)
    text = NON_WORD_RE.sub(" ", text)
    text = DIGIT_RE.sub(" ", text)
    text = re.sub(r"_+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_frequencies(text_series: List[str], cfg: WordCloudConfig) -> Dict[str, int]:
    if not text_series:
        return {}

    stopwords = DEFAULT_STOPWORDS | DOMAIN_STOPWORDS
    lemmatizer = _safe_wordnet_lemmatizer() if cfg.lemmatize else None
    token_counter: Counter = Counter()
    bigram_counter: Counter = Counter()

    for raw in text_series:
        cleaned = _prepare_text(raw, cfg)
        if not cleaned:
            continue
        tokens = []
        for t in cleaned.split():
            if len(t) < 3 or t in stopwords:
                continue
            lemma = _lemmatize_token(t, lemmatizer)
            if lemma and lemma not in stopwords and len(lemma) >= 3:
                tokens.append(lemma)

        token_counter.update(tokens)
        if cfg.include_bigrams and len(tokens) >= 2:
            pairs = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]
            bigram_counter.update(pairs)

    freq: Dict[str, int] = {
        token: count for token, count in token_counter.items() if count >= cfg.min_frequency
    }
    if cfg.include_bigrams:
        for phrase, count in bigram_counter.items():
            # Slightly stricter threshold for bigrams to reduce visual clutter.
            if count >= max(cfg.min_frequency, 2):
                freq[phrase] = count

    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[: cfg.max_words])


def _make_theme_color_func():
    palette = [
        THEME_COLORS["primary"],
        THEME_COLORS["secondary"],
        THEME_COLORS["info"],
        THEME_COLORS["success"],
        "#a78bfa",
    ]

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        idx = abs(hash(word)) % len(palette)
        return palette[idx]

    return color_func


def _generate_wordcloud_image(frequencies: Dict[str, int], cfg: WordCloudConfig) -> Optional[np.ndarray]:
    if not frequencies:
        return None

    wc = WordCloud(
        width=cfg.width,
        height=cfg.height,
        max_words=cfg.max_words,
        min_font_size=cfg.min_font_size,
        max_font_size=cfg.max_font_size,
        prefer_horizontal=cfg.prefer_horizontal,
        random_state=cfg.random_state,
        scale=cfg.scale,
        relative_scaling=0.45,
        background_color=None if cfg.background_mode == "transparent" else THEME_COLORS["background"],
        mode="RGBA" if cfg.background_mode == "transparent" else "RGB",
        collocations=False,
        color_func=_make_theme_color_func(),
        contour_width=cfg.contour_width,
    ).generate_from_frequencies(frequencies)

    return wc.to_array()


def _image_to_png_bytes(image_array: np.ndarray, cfg: WordCloudConfig) -> bytes:
    fig = plt.figure(figsize=(cfg.width / 180, cfg.height / 180), dpi=180)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(image_array, interpolation="bilinear")
    ax.axis("off")
    fig.patch.set_alpha(0 if cfg.background_mode == "transparent" else 1)
    if cfg.background_mode != "transparent":
        fig.patch.set_facecolor(THEME_COLORS["background"])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, transparent=(cfg.background_mode == "transparent"), bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_wordcloud(text_series: List[str], config_options: Optional[Dict[str, Any]] = None) -> None:
    """
    Render a polished, insight-focused word cloud in Streamlit.

    Args:
        text_series: List/series of text values (captions/comments/posts).
        config_options: Optional dictionary for WordCloudConfig overrides.
    """
    cfg = WordCloudConfig(**(config_options or {}))
    raw_items: List[Any] = list(text_series or [])
    texts = _apply_optional_filters(
        raw_items,
        platform_filter=cfg.platform_filter,
        date_from=cfg.date_from,
        date_to=cfg.date_to,
    )

    st.markdown("#### 🧭 Top Themes in Content")
    st.caption(cfg.caption)

    if not texts:
        st.info("No text data available for theme extraction.")
        return

    frequencies = _extract_frequencies(texts, cfg)
    if not frequencies:
        st.info("No meaningful terms found after cleaning and stopword filtering.")
        return

    image = _generate_wordcloud_image(frequencies, cfg)
    if image is None:
        st.info("Word cloud generation returned no output.")
        return

    st.image(image, use_container_width=True)

    top_terms = list(frequencies.items())[:8]
    st.caption("Top terms: " + ", ".join([f"{term} ({count})" for term, count in top_terms]))

    png_bytes = _image_to_png_bytes(image, cfg)
    st.download_button(
        "Download Word Cloud PNG",
        data=png_bytes,
        file_name="top_themes_wordcloud.png",
        mime="image/png",
        key=f"download_wordcloud_{cfg.section_key}",
    )

class PhraseWordCloudGenerator:
    """
    Advanced word cloud generator that supports phrases and sentiment coloring.
    """
    
    def __init__(self,
                 width: int = 800,
                 height: int = 400,
                 max_words: int = 100,
                 background_color: str = 'white',
                 colormap: str = 'viridis',
                 relative_scaling: float = 0.5,
                 min_font_size: int = 10,
                 max_font_size: int = 200,
                 prefer_horizontal: float = 0.9,
                 use_phrases: bool = True,
                 sentiment_coloring: bool = True,
                 language: str = 'auto'):
        """
        Initialize the word cloud generator.
        
        Args:
            width: Width of the word cloud
            height: Height of the word cloud
            max_words: Maximum number of words/phrases to display
            background_color: Background color
            colormap: Colormap for non-sentiment coloring
            relative_scaling: Relative scaling factor
            min_font_size: Minimum font size
            max_font_size: Maximum font size
            prefer_horizontal: Preference for horizontal text
            use_phrases: Whether to use phrase extraction
            sentiment_coloring: Whether to use sentiment-based coloring
            language: Language mode
        """
        self.width = width
        self.height = height
        self.max_words = max_words
        self.background_color = background_color
        self.colormap = colormap
        self.relative_scaling = relative_scaling
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
        self.prefer_horizontal = prefer_horizontal
        self.use_phrases = use_phrases
        self.sentiment_coloring = sentiment_coloring
        self.language = language
        
        # Initialize components
        if self.use_phrases:
            self.phrase_extractor = PhraseExtractor(language=language)
            self.sentiment_analyzer = PhraseSentimentAnalyzer(language=language)
        
        # Sentiment color mapping from theme
        self.sentiment_colors = dict(SENTIMENT_COLORS)
        # Sentiment color gradients using theme colors
        bg = THEME_COLORS['background']
        self.positive_gradient = [bg, SENTIMENT_COLORS['positive'], '#0d9668']
        self.negative_gradient = [bg, SENTIMENT_COLORS['negative'], '#c2352a']
        self.neutral_gradient = [bg, SENTIMENT_COLORS['neutral'], '#475569']
    
    def extract_content_for_wordcloud(self, texts: List[str]) -> Dict[str, Dict]:
        """
        Extract words/phrases and their metadata for word cloud generation.
        
        Returns:
            Dictionary with content information:
            {
                'content': {word/phrase: frequency},
                'sentiment_scores': {word/phrase: sentiment_score},
                'sentiment_labels': {word/phrase: sentiment_label},
                'metadata': {word/phrase: additional_info}
            }
        """
        if not texts:
            return {
                'content': {},
                'sentiment_scores': {},
                'sentiment_labels': {},
                'metadata': {}
            }
        
        if self.use_phrases:
            # Extract phrases
            phrases = self.phrase_extractor.get_top_phrases(texts, self.max_words)
            
            # Analyze sentiment for each phrase
            sentiment_scores = {}
            sentiment_labels = {}
            metadata = {}
            
            for phrase, frequency in phrases.items():
                # Get sentiment information
                sentiment_score = get_phrase_sentiment_score(phrase, self.language)
                sentiment_label = get_phrase_sentiment_label(phrase, self.language)
                
                sentiment_scores[phrase] = sentiment_score
                sentiment_labels[phrase] = sentiment_label
                
                # Additional metadata
                metadata[phrase] = {
                    'frequency': frequency,
                    'is_phrase': True,
                    'word_count': len(phrase.split()),
                    'confidence': abs(sentiment_score)
                }
            
            return {
                'content': phrases,
                'sentiment_scores': sentiment_scores,
                'sentiment_labels': sentiment_labels,
                'metadata': metadata
            }
        else:
            # Fallback to word-based extraction
            from ..nlp.phrase_extractor import tokenize_arabic
            
            all_tokens = []
            for text in texts:
                tokens = tokenize_arabic(text)
                all_tokens.extend(tokens)
            
            word_freqs = Counter(all_tokens)
            top_words = dict(word_freqs.most_common(self.max_words))
            
            # Simple sentiment analysis for words
            sentiment_scores = {}
            sentiment_labels = {}
            metadata = {}
            
            for word, frequency in top_words.items():
                sentiment_score = get_phrase_sentiment_score(word, self.language)
                sentiment_label = get_phrase_sentiment_label(word, self.language)
                
                sentiment_scores[word] = sentiment_score
                sentiment_labels[word] = sentiment_label
                
                metadata[word] = {
                    'frequency': frequency,
                    'is_phrase': False,
                    'word_count': 1,
                    'confidence': abs(sentiment_score)
                }
            
            return {
                'content': top_words,
                'sentiment_scores': sentiment_scores,
                'sentiment_labels': sentiment_labels,
                'metadata': metadata
            }
    
    def create_sentiment_color_func(self, content_data: Dict[str, Dict]) -> callable:
        """
        Create a color function based on sentiment scores.
        
        Returns:
            Function that maps words to colors based on sentiment
        """
        sentiment_scores = content_data['sentiment_scores']
        sentiment_labels = content_data['sentiment_labels']
        
        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            # Get sentiment information
            sentiment_score = sentiment_scores.get(word, 0.0)
            sentiment_label = sentiment_labels.get(word, 'neutral')
            
            # Map sentiment to color
            if sentiment_label == 'positive':
                # Use positive gradient based on score strength
                if sentiment_score >= 0.8:
                    return self.positive_gradient[2]  # Strong positive
                elif sentiment_score >= 0.6:
                    return self.positive_gradient[1]  # Moderate positive
                else:
                    return self.positive_gradient[0]  # Mild positive
            elif sentiment_label == 'negative':
                # Use negative gradient based on score strength
                if sentiment_score <= -0.8:
                    return self.negative_gradient[2]  # Strong negative
                elif sentiment_score <= -0.6:
                    return self.negative_gradient[1]  # Moderate negative
                else:
                    return self.negative_gradient[0]  # Mild negative
            else:
                # Neutral - use neutral gradient
                return self.neutral_gradient[1]
        
        return color_func
    
    def prepare_text_for_display(self, text: str) -> str:
        """
        Prepare text for display in word cloud (handle Arabic shaping).
        """
        if not text:
            return ""
        
        # Handle Arabic text shaping
        if ARABIC_SUPPORT and self._is_arabic_text(text):
            return reshape_arabic_text(text)
        
        return text
    
    def _is_arabic_text(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        return bool(arabic_pattern.search(text))
    
    def generate_wordcloud(self, texts: List[str], title: str = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Generate a word cloud with phrase support and sentiment coloring.
        
        Args:
            texts: List of texts to analyze
            title: Optional title for the plot
            
        Returns:
            Tuple of (figure, axes) for the generated plot
        """
        if not texts:
            # Create empty plot
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No data available for word cloud', 
                   ha='center', va='center', fontsize=16, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig, ax
        
        # Extract content for word cloud
        content_data = self.extract_content_for_wordcloud(texts)
        content = content_data['content']
        
        if not content:
            # Create empty plot with more helpful message
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.7, 'No meaningful content found', 
                   ha='center', va='center', fontsize=16, color='gray', weight='bold')
            ax.text(0.5, 0.5, 'This could be because:', 
                   ha='center', va='center', fontsize=12, color='gray')
            ax.text(0.5, 0.4, '• Comments are too short or contain only common words', 
                   ha='center', va='center', fontsize=10, color='gray')
            ax.text(0.5, 0.35, '• Comments are in a language not well supported', 
                   ha='center', va='center', fontsize=10, color='gray')
            ax.text(0.5, 0.3, '• Comments contain mostly emojis or special characters', 
                   ha='center', va='center', fontsize=10, color='gray')
            ax.text(0.5, 0.2, 'Try using the simple word cloud option in settings', 
                   ha='center', va='center', fontsize=10, color='blue', style='italic')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig, ax
        
        # Prepare text for display (handle Arabic shaping)
        display_content = {}
        for text, frequency in content.items():
            display_text = self.prepare_text_for_display(text)
            display_content[display_text] = frequency
        
        # Create color function
        if self.sentiment_coloring:
            color_func = self.create_sentiment_color_func(content_data)
        else:
            color_func = None
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=self.width,
            height=self.height,
            background_color=THEME_COLORS['background'],
            max_words=self.max_words,
            relative_scaling=self.relative_scaling,
            min_font_size=self.min_font_size,
            max_font_size=self.max_font_size,
            prefer_horizontal=self.prefer_horizontal,
            colormap=self.colormap if not self.sentiment_coloring else None,
            color_func=color_func,
            font_path=None,  # Use default font
            regexp=r"\S+",  # Match any non-whitespace sequence
            collocations=False,  # We handle phrases ourselves
        ).generate_from_frequencies(display_content)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=THEME_COLORS['background'])
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        fig.patch.set_facecolor(THEME_COLORS['background'])
        
        if title:
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color=THEME_COLORS['text'])
        
        # Add legend if using sentiment coloring
        if self.sentiment_coloring:
            self._add_sentiment_legend(ax, content_data)
        
        plt.tight_layout()
        return fig, ax
    
    def _add_sentiment_legend(self, ax: plt.Axes, content_data: Dict[str, Dict]):
        """Add sentiment legend to the plot."""
        sentiment_labels = content_data['sentiment_labels']
        
        # Count sentiment distribution
        sentiment_counts = Counter(sentiment_labels.values())
        
        # Create legend
        legend_elements = []
        for sentiment, count in sentiment_counts.items():
            if count > 0:
                color = self.sentiment_colors.get(sentiment, '#95a5a6')
                legend_elements.append(
                    plt.Rectangle((0, 0), 1, 1, facecolor=color, 
                                label=f'{sentiment.title()} ({count})')
                )
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', 
                     bbox_to_anchor=(1, 1), fontsize=10)
    
    def generate_comparison_wordclouds(self, texts_by_category: Dict[str, List[str]], 
                                     title: str = None) -> Tuple[plt.Figure, List[plt.Axes]]:
        """
        Generate multiple word clouds for comparison.
        
        Args:
            texts_by_category: Dictionary mapping category names to text lists
            title: Optional overall title
            
        Returns:
            Tuple of (figure, list of axes)
        """
        num_categories = len(texts_by_category)
        if num_categories == 0:
            return self.generate_wordcloud([], title)
        
        # Create subplots
        cols = min(3, num_categories)
        rows = (num_categories + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3*rows))
        if num_categories == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes if isinstance(axes, list) else [axes]
        else:
            axes = axes.flatten()
        
        # Generate word cloud for each category
        for i, (category, texts) in enumerate(texts_by_category.items()):
            if i < len(axes):
                # Generate word cloud
                content_data = self.extract_content_for_wordcloud(texts)
                content = content_data['content']
                
                if content:
                    # Prepare text for display
                    display_content = {}
                    for text, frequency in content.items():
                        display_text = self.prepare_text_for_display(text)
                        display_content[display_text] = frequency
                    
                    # Create color function
                    if self.sentiment_coloring:
                        color_func = self.create_sentiment_color_func(content_data)
                    else:
                        color_func = None
                    
                    # Generate word cloud
                    wordcloud = WordCloud(
                        width=400,
                        height=300,
                        background_color=THEME_COLORS['background'],
                        max_words=50,  # Fewer words for subplots
                        relative_scaling=self.relative_scaling,
                        min_font_size=8,
                        max_font_size=100,
                        prefer_horizontal=self.prefer_horizontal,
                        colormap=self.colormap if not self.sentiment_coloring else None,
                        color_func=color_func,
                        collocations=False,
                    ).generate_from_frequencies(display_content)
                    
                    axes[i].imshow(wordcloud, interpolation='bilinear')
                    axes[i].set_title(f'{category}', fontsize=12, fontweight='bold', color=THEME_COLORS['text'])
                else:
                    axes[i].text(0.5, 0.5, 'No content', ha='center', va='center', 
                               fontsize=12, color='gray')
                    axes[i].set_title(f'{category}', fontsize=12, fontweight='bold')
                
                axes[i].axis('off')
        
        # Hide unused subplots
        for i in range(num_categories, len(axes)):
            axes[i].axis('off')
        
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        return fig, axes


# Convenience functions for easy integration
def create_phrase_wordcloud(texts: List[str], 
                          title: str = None,
                          use_sentiment_coloring: bool = True,
                          language: str = 'auto') -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a phrase-based word cloud with sentiment coloring.
    
    Args:
        texts: List of texts to analyze
        title: Optional title
        use_sentiment_coloring: Whether to use sentiment-based colors
        language: Language mode
        
    Returns:
        Tuple of (figure, axes)
    """
    generator = PhraseWordCloudGenerator(
        use_phrases=True,
        sentiment_coloring=use_sentiment_coloring,
        language=language
    )
    return generator.generate_wordcloud(texts, title)


def create_comparison_wordclouds(texts_by_category: Dict[str, List[str]],
                               title: str = None,
                               use_sentiment_coloring: bool = True,
                               language: str = 'auto') -> Tuple[plt.Figure, List[plt.Axes]]:
    """
    Create comparison word clouds for different categories.
    
    Args:
        texts_by_category: Dictionary mapping categories to text lists
        title: Optional title
        use_sentiment_coloring: Whether to use sentiment-based colors
        language: Language mode
        
    Returns:
        Tuple of (figure, list of axes)
    """
    generator = PhraseWordCloudGenerator(
        use_phrases=True,
        sentiment_coloring=use_sentiment_coloring,
        language=language
    )
    return generator.generate_comparison_wordclouds(texts_by_category, title)
