"""
Advanced NLP Visualization Components
======================================

Visualizations for topic modeling, keyword extraction, and enhanced analytics.
"""

from typing import Dict, List, Optional, Any, Tuple
import streamlit as st
import pandas as pd

# Optional Plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
def _next_chart_key(prefix: str) -> str:
    """Generate a unique, deterministic key per render for a given prefix."""
    counter_key = f"_chart_counter_{prefix}"
    st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
    return f"{prefix}-{st.session_state[counter_key]}"



# ============================================================================
# TOPIC MODELING VISUALIZATION
# ============================================================================

def create_topic_modeling_view(topics: List[Dict[str, Any]]) -> None:
    """
    Visualize extracted topics.

    Args:
        topics: List of topic dictionaries from topic modeling
    """
    st.markdown("### 🏷️ Discovered Topics")

    if not topics:
        st.info("Not enough data for topic modeling. Need at least 10 comments.")
        return

    st.markdown(f"**{len(topics)} topics discovered** from the conversation:")

    for topic in topics:
        topic_id = topic['topic_id']
        words = topic['words']
        weights = topic['weights']

        with st.expander(f"📌 Topic {topic_id + 1}: {', '.join(words[:3])}", expanded=topic_id == 0):
            # Create word cloud-style display
            col1, col2 = st.columns([2, 1])

            with col1:
                # Word importance chart
                if PLOTLY_AVAILABLE:
                    df = pd.DataFrame({
                        'Word': words,
                        'Importance': weights
                    })

                    fig = px.bar(
                        df,
                        x='Importance',
                        y='Word',
                        orientation='h',
                        title=f"Topic {topic_id + 1} - Top Words",
                        color='Importance',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(
                        showlegend=False,
                        plot_bgcolor='#F5F7F8',
                        paper_bgcolor='#F5F7F8',
                        font_color='#45474B',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True, key=_next_chart_key(f"topic-words-{topic_id}"))
                else:
                    # Fallback
                    df = pd.DataFrame({
                        'Word': words,
                        'Importance': weights
                    })
                    st.bar_chart(df.set_index('Word'))

            with col2:
                st.markdown("**Top 10 Words:**")
                for i, (word, weight) in enumerate(zip(words, weights), 1):
                    st.markdown(f"{i}. **{word}** ({weight:.3f})")


# ============================================================================
# KEYWORD VISUALIZATION
# ============================================================================

def create_keyword_cloud(keywords: List[Tuple[str, float]], title: str = "Top Keywords") -> None:
    """
    Visualize top keywords with TF-IDF scores.

    Args:
        keywords: List of (keyword, score) tuples
        title: Chart title
    """
    st.markdown(f"### 🔑 {title}")

    if not keywords:
        st.info("No keywords extracted")
        return

    # Take top 20
    keywords = keywords[:20]

    if PLOTLY_AVAILABLE:
        df = pd.DataFrame(keywords, columns=['Keyword', 'Score'])

        fig = px.bar(
            df,
            x='Score',
            y='Keyword',
            orientation='h',
            title=title,
            color='Score',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor='#F5F7F8',
            paper_bgcolor='#F5F7F8',
            font_color='#45474B',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True, key=_next_chart_key("keyword-cloud"))
    else:
        df = pd.DataFrame(keywords, columns=['Keyword', 'Score'])
        st.bar_chart(df.set_index('Keyword'))


# ============================================================================
# ENHANCED EMOJI ANALYSIS
# ============================================================================

def create_emoji_sentiment_chart(emoji_analysis: Dict[str, Any]) -> None:
    """
    Create enhanced emoji analysis with sentiment.

    Args:
        emoji_analysis: Emoji analysis dictionary
    """
    st.markdown("### 😊 Emoji Sentiment Analysis")

    if not emoji_analysis or emoji_analysis.get('emoji_count', 0) == 0:
        st.info("No emojis found in the text")
        return

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Emojis", f"{emoji_analysis['emoji_count']:,}")

    with col2:
        st.metric("Unique Emojis", f"{emoji_analysis['unique_emojis']:,}")

    with col3:
        sentiment_score = emoji_analysis['emoji_sentiment_score']
        st.metric(
            "Emoji Sentiment",
            emoji_analysis['emoji_sentiment_label'].capitalize(),
            delta=f"{sentiment_score:+.2f}"
        )

    with col4:
        contribution = emoji_analysis.get('sentiment_contribution', 0)
        st.metric("Sentiment Impact", f"{contribution:+.1f}")

    # Emoji details
    st.markdown("---")
    st.markdown("#### 📊 Emoji Breakdown")

    emojis = emoji_analysis.get('emojis', [])
    if emojis:
        # Create dataframe
        emoji_df = pd.DataFrame(emojis)
        emoji_df['sentiment_label'] = emoji_df['sentiment'].apply(
            lambda x: 'Positive' if x > 0.3 else 'Negative' if x < -0.3 else 'Neutral'
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if PLOTLY_AVAILABLE:
                fig = go.Figure()

                # Create bars colored by sentiment
                colors = []
                for sentiment in emoji_df['sentiment']:
                    if sentiment > 0.3:
                        colors.append('#43e97b')  # Green
                    elif sentiment < -0.3:
                        colors.append('#f5576c')  # Red
                    else:
                        colors.append('#4facfe')  # Blue

                fig.add_trace(go.Bar(
                    x=emoji_df['count'],
                    y=emoji_df['emoji'],
                    orientation='h',
                    marker_color=colors,
                    text=emoji_df['sentiment'].apply(lambda x: f"{x:+.2f}"),
                    textposition='outside'
                ))

                fig.update_layout(
                    title="Emoji Usage & Sentiment",
                    xaxis_title="Count",
                    yaxis_title="Emoji",
                    plot_bgcolor='#F5F7F8',
                    paper_bgcolor='#F5F7F8',
                    font_color='#45474B',
                    height=400,
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True, key=_next_chart_key("emoji-sentiment"))
            else:
                st.bar_chart(emoji_df.set_index('emoji')['count'])

        with col2:
            st.markdown("**Emoji Sentiment Scores:**")
            for emoji_info in emojis[:10]:
                emoji = emoji_info['emoji']
                count = emoji_info['count']
                sentiment = emoji_info['sentiment']

                if sentiment > 0:
                    color = "🟢"
                elif sentiment < 0:
                    color = "🔴"
                else:
                    color = "⚪"

                st.markdown(f"{color} {emoji} x{count} ({sentiment:+.2f})")


# ============================================================================
# TEXT STATISTICS DASHBOARD
# ============================================================================

def create_text_statistics_dashboard(stats: Dict[str, Any]) -> None:
    """
    Create text statistics dashboard.

    Args:
        stats: Statistics dictionary
    """
    st.markdown("### 📊 Text Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Texts", f"{stats['total_texts']:,}")

    with col2:
        st.metric("Total Words", f"{stats['total_words']:,}")

    with col3:
        st.metric("Avg Words/Text", f"{stats['avg_word_count']:.1f}")

    with col4:
        richness_pct = stats['vocabulary_richness'] * 100
        st.metric("Vocabulary Richness", f"{richness_pct:.1f}%")

    # Additional stats
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Unique Words", f"{stats['unique_words']:,}")

    with col2:
        st.metric("Total Characters", f"{stats['total_chars']:,}")

    with col3:
        st.metric("Avg Text Length", f"{stats['avg_text_length']:.0f} chars")


# ============================================================================
# COMPREHENSIVE NLP DASHBOARD
# ============================================================================

def create_advanced_nlp_dashboard(
    texts: List[str],
    show_topics: bool = True,
    show_keywords: bool = True,
    show_emoji_analysis: bool = True,
    show_statistics: bool = True
) -> None:
    """
    Create comprehensive NLP analysis dashboard.

    Args:
        texts: List of texts to analyze
        show_topics: Whether to show topic modeling
        show_keywords: Whether to show keyword extraction
        show_emoji_analysis: Whether to show emoji analysis
        show_statistics: Whether to show text statistics
    """
    if not texts:
        st.warning("No text data available for analysis")
        return

    st.markdown("## 🧠 Advanced NLP Analysis")
    st.markdown("---")

    # Import advanced NLP functions
    from app.nlp.advanced_nlp import (
        analyze_corpus_advanced,
        SKLEARN_AVAILABLE
    )

    # Run comprehensive analysis
    with st.spinner("Analyzing text corpus..."):
        analysis = analyze_corpus_advanced(texts)

    # Text Statistics
    if show_statistics:
        create_text_statistics_dashboard(analysis['statistics'])
        st.markdown("---")

    # Topic Modeling
    if show_topics and SKLEARN_AVAILABLE:
        if analysis['topics']:
            create_topic_modeling_view(analysis['topics'])
            st.markdown("---")
        else:
            st.info("💡 Topic modeling requires at least 10 texts with sufficient content.")
    elif show_topics and not SKLEARN_AVAILABLE:
        st.warning("📦 Install scikit-learn for topic modeling: `pip install scikit-learn`")

    # Keyword Extraction
    if show_keywords and SKLEARN_AVAILABLE:
        if analysis['keywords']:
            create_keyword_cloud(analysis['keywords'], "Most Important Keywords (TF-IDF)")
            st.markdown("---")
    elif show_keywords and not SKLEARN_AVAILABLE:
        st.warning("📦 Install scikit-learn for keyword extraction: `pip install scikit-learn`")

    # Emoji Analysis
    if show_emoji_analysis and analysis.get('emoji_analysis'):
        emoji_data = analysis['emoji_analysis']
        if emoji_data.get('total_emojis', 0) > 0:
            # Adapt corpus-level emoji data to the schema expected by the chart
            try:
                from app.nlp.advanced_nlp import get_emoji_sentiment
                avg_sent = float(emoji_data.get('avg_sentiment', 0.0))
                if avg_sent > 0.3:
                    label = 'positive'
                elif avg_sent < -0.3:
                    label = 'negative'
                else:
                    label = 'neutral'

                transformed = {
                    'emoji_count': int(emoji_data.get('total_emojis', 0)),
                    'unique_emojis': int(emoji_data.get('unique_emojis', 0)),
                    'emoji_sentiment_score': avg_sent,
                    'emoji_sentiment_label': label,
                    'emojis': [
                        {
                            'emoji': item.get('emoji'),
                            'count': int(item.get('count', 0)),
                            'sentiment': float(get_emoji_sentiment(item.get('emoji')))
                        }
                        for item in emoji_data.get('top_emojis', []) if item.get('emoji')
                    ],
                    'sentiment_contribution': avg_sent * float(emoji_data.get('total_emojis', 0))
                }

                create_emoji_sentiment_chart(transformed)
                st.markdown("---")
            except Exception:
                # Fallback: skip emoji chart if transformation fails
                pass

    # Entity Extraction (if GLiNER is available and enabled)
    import streamlit as st
    use_entity_extraction = st.session_state.get('use_entity_extraction', True)

    if use_entity_extraction:
        try:
            from app.viz.entity_viz import display_entity_dashboard
            display_entity_dashboard(texts)
        except ImportError:
            # GLiNER not installed, skip entity extraction
            pass
        except Exception as e:
            # Silently skip if entity extraction fails
            pass


# ============================================================================
# SENTIMENT COMPARISON VIEW
# ============================================================================

def create_sentiment_comparison_view(
    text_sentiment: Dict[str, Any],
    emoji_sentiment: Dict[str, Any],
    combined_sentiment: Dict[str, Any]
) -> None:
    """
    Create comparison view of text vs emoji vs combined sentiment.

    Args:
        text_sentiment: Text-only sentiment
        emoji_sentiment: Emoji-only sentiment
        combined_sentiment: Combined sentiment
    """
    st.markdown("### 🔄 Sentiment Breakdown")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📝 Text Sentiment")
        text_score = text_sentiment.get('overall_score', 0)
        text_label = text_sentiment.get('overall_label', 'neutral')
        st.metric(
            "Score",
            text_label.capitalize(),
            delta=f"{text_score:+.2f}"
        )

    with col2:
        st.markdown("#### 😊 Emoji Sentiment")
        emoji_score = emoji_sentiment.get('emoji_sentiment_score', 0)
        emoji_label = emoji_sentiment.get('emoji_sentiment_label', 'neutral')
        st.metric(
            "Score",
            emoji_label.capitalize(),
            delta=f"{emoji_score:+.2f}"
        )

    with col3:
        st.markdown("#### ⚖️ Combined Sentiment")
        combined_score = combined_sentiment.get('combined_score', 0)
        combined_label = combined_sentiment.get('combined_label', 'neutral')
        st.metric(
            "Final Score",
            combined_label.capitalize(),
            delta=f"{combined_score:+.2f}"
        )

    # Visualization
    if PLOTLY_AVAILABLE:
        st.markdown("---")

        categories = ['Text Only', 'Emoji Only', 'Combined']
        scores = [text_score, emoji_score, combined_score]
        colors = []

        for score in scores:
            if score > 0.3:
                colors.append('#43e97b')
            elif score < -0.3:
                colors.append('#f5576c')
            else:
                colors.append('#4facfe')

        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=scores,
                marker_color=colors,
                text=[f"{s:+.2f}" for s in scores],
                textposition='outside'
            )
        ])

        fig.update_layout(
            title="Sentiment Score Comparison",
            yaxis_title="Sentiment Score",
            yaxis=dict(range=[-1.2, 1.2]),
            plot_bgcolor='#F5F7F8',
            paper_bgcolor='#F5F7F8',
            font_color='#45474B',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True, key=_next_chart_key("sentiment-comparison"))
