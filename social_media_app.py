"""
Social Media Analytics Dashboard
=================================

How to run:
1. Set your Apify API token:
   export APIFY_TOKEN=your_token_here

2. Install dependencies:
   pip install -r requirements.txt

3. Run the app:
   streamlit run app.py

This app connects to Apify actors to analyze social media posts from Facebook, 
Instagram, and YouTube for the current month.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
from apify_client import ApifyClient
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter

# ============================================================================
# CONFIGURATION
# ============================================================================

# Apify Actor Names - Replace with actual actor IDs/names
ACTOR_CONFIG = {
    "Facebook": "apify/facebook-posts-scraper",  # Updated with correct actor name
    "Instagram": "apify/instagram-scraper",  # Updated with correct actor name
    "YouTube": "streamers/youtube-comments-scraper"  # Updated with correct actor name
}

# Actor IDs for direct calls (when needed)
ACTOR_IDS = {
    "Facebook": "KoJrdxJCTtpon81KY",  # Placeholder
    "Instagram": "shu8hvrXbJbY3Eb9W",  # Instagram scraper actor ID
    "YouTube": "p7UMdpQnjKmmpR21D"  # Placeholder
}

# Arabic stopwords (basic set - expand as needed)
ARABIC_STOPWORDS = {
    'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي',
    'أن', 'أو', 'لا', 'نعم', 'كان', 'يكون', 'ما', 'هل', 'قد', 'لقد',
    'عن', 'مع', 'بعد', 'قبل', 'عند', 'كل', 'بين', 'حتى', 'لكن', 'ثم',
    'و', 'أو', 'لم', 'لن', 'إن', 'أن', 'كما', 'لماذا', 'كيف', 'أين',
    'متى', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
}

# ============================================================================
# NLP UTILITIES (Arabic-capable, pluggable design)
# ============================================================================

def clean_arabic_text(text: str) -> str:
    """Clean Arabic text by removing diacritics, extra spaces, and noise."""
    if not text:
        return ""
    
    # Remove Arabic diacritics
    arabic_diacritics = re.compile("""
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
    
    text = re.sub(arabic_diacritics, '', text)
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove mentions and hashtags symbols (keep text)
    text = re.sub(r'[@#]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def tokenize_arabic(text: str) -> List[str]:
    """Tokenize text and filter stopwords."""
    text = clean_arabic_text(text)
    # Split on whitespace and punctuation
    tokens = re.findall(r'\b\w+\b', text)
    # Filter stopwords and short tokens
    tokens = [t for t in tokens if t.lower() not in ARABIC_STOPWORDS and len(t) > 2]
    return tokens

def extract_keywords_nlp(comments: List[str], top_n: int = 50) -> Dict[str, int]:
    """
    Extract keywords from comments using frequency analysis.
    This is a pluggable function - replace with GLiNER or other Arabic NLP as needed.
    
    For production: Replace this with:
    - GLiNER for named entity recognition
    - CAMeL Tools for Arabic morphological analysis
    - AraBERT for sentiment analysis
    """
    all_tokens = []
    for comment in comments:
        all_tokens.extend(tokenize_arabic(comment))
    
    # Count frequencies
    word_freq = Counter(all_tokens)
    return dict(word_freq.most_common(top_n))

def analyze_sentiment_placeholder(text: str) -> str:
    """
    Placeholder sentiment analysis. Replace with Arabic-capable model.
    
    For production, use:
    - AraBERT for Arabic sentiment
    - Multilingual BERT fine-tuned on Arabic
    - CAMeL Tools + rule-based sentiment
    """
    # Simple placeholder - counts positive/negative indicators
    positive_words = ['جيد', 'ممتاز', 'رائع', 'حلو', 'good', 'great', 'love', '❤️', '😊', '👍']
    negative_words = ['سيء', 'سئ', 'bad', 'hate', 'terrible', '😢', '😡', '👎']
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"

# ============================================================================
# DATA NORMALIZATION
# ============================================================================

def normalize_post_data(raw_data: List[Dict], platform: str) -> List[Dict]:
    """
    Normalize actor response into consistent schema.
    Adjust field mappings based on actual actor responses.
    """
    normalized = []
    
    for item in raw_data:
        try:
            # Platform-specific field mapping
            if platform == "Instagram":
                post = {
                    'post_id': item.get('id') or item.get('shortcode', ''),
                    'published_at': item.get('timestamp') or item.get('takenAt') or item.get('date', ''),
                    'text': item.get('caption') or item.get('text') or item.get('description', ''),
                    'likes': item.get('likesCount') or item.get('likes', 0),
                    'comments_count': item.get('commentsCount') or item.get('comments', 0),
                    'shares_count': item.get('sharesCount') or item.get('shares', 0),
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('comments') or item.get('commentsList', [])
                }
            elif platform == "Facebook":
                post = {
                    'post_id': item.get('id') or item.get('postId', ''),
                    'published_at': item.get('time') or item.get('timestamp') or item.get('createdTime', ''),
                    'text': item.get('text') or item.get('message') or item.get('caption', ''),
                    'likes': item.get('likesCount') or item.get('likes', 0),
                    'comments_count': item.get('commentsCount') or item.get('comments', 0),
                    'shares_count': item.get('sharesCount') or item.get('shares', 0),
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('comments') or item.get('commentsList', [])
                }
            elif platform == "YouTube":
                post = {
                    'post_id': item.get('id') or item.get('videoId', ''),
                    'published_at': item.get('publishedAt') or item.get('timestamp') or item.get('date', ''),
                    'text': item.get('text') or item.get('title') or item.get('description', ''),
                    'likes': item.get('likesCount') or item.get('likes', 0),
                    'comments_count': item.get('commentsCount') or item.get('comments', 0),
                    'shares_count': item.get('sharesCount') or item.get('shares', 0),
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('comments') or item.get('commentsList', [])
                }
            else:
                # Generic fallback
                post = {
                    'post_id': item.get('id') or item.get('postId') or item.get('videoId', ''),
                    'published_at': item.get('time') or item.get('timestamp') or item.get('publishedAt', ''),
                    'text': item.get('text') or item.get('caption') or item.get('title', ''),
                    'likes': item.get('likes', 0) or item.get('likesCount', 0),
                    'comments_count': item.get('comments', 0) or item.get('commentsCount', 0),
                    'shares_count': item.get('shares', 0) or item.get('sharesCount', 0),
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('commentsList', []) or item.get('comments_data', [])
                }
            
            # Parse timestamp if string
            if isinstance(post['published_at'], str):
                try:
                    post['published_at'] = pd.to_datetime(post['published_at'])
                except:
                    post['published_at'] = datetime.now()
            
            normalized.append(post)
        except Exception as e:
            st.warning(f"Failed to normalize post: {str(e)}")
            continue
    
    return normalized

def filter_current_month(posts: List[Dict]) -> List[Dict]:
    """Filter posts to current month only."""
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    filtered = []
    for post in posts:
        pub_date = post['published_at']
        if isinstance(pub_date, str):
            pub_date = pd.to_datetime(pub_date)
        
        # Convert to timezone-naive for comparison
        if hasattr(pub_date, 'tz') and pub_date.tz is not None:
            pub_date = pub_date.tz_localize(None)
        
        if month_start <= pub_date <= month_end:
            filtered.append(post)
    
    return filtered

# ============================================================================
# APIFY INTEGRATION
# ============================================================================

@st.cache_data(ttl=3600)
def fetch_apify_data(platform: str, url: str, _apify_token: str) -> Optional[List[Dict]]:
    """
    Fetch data from Apify actor for the given platform and URL.
    Cached for 1 hour per platform+URL combination.
    
    NOTE: Adjust the 'run_input' based on actual actor requirements.
    """
    try:
        client = ApifyClient(_apify_token)
        actor_name = ACTOR_CONFIG.get(platform)
        
        if not actor_name:
            st.error(f"No actor configured for {platform}")
            return None
        
        # Configure input based on platform
        # These are example inputs - adjust based on actual actor documentation
        if platform == "Instagram":
            # Instagram-specific input based on the actor documentation
            run_input = {
                "directUrls": [url],  # The Instagram profile URL
                "resultsType": "posts",  # What to scrape
                "resultsLimit": 10,  # Number of posts to fetch (reduced for testing)
                "searchType": "hashtag",  # Search type
                "searchLimit": 1,  # Search limit
                "addParentData": False  # Whether to add parent data
            }
        elif platform == "Facebook":
            # Facebook-specific input based on the actor documentation
            run_input = {
                "startUrls": [{"url": url}],  # Facebook page URL
                "resultsLimit": 10,  # Number of posts to fetch (reduced for testing)
                "captionText": False  # Whether to include caption text
            }
        elif platform == "YouTube":
            # YouTube-specific input based on the actor documentation
            run_input = {
                "startUrls": [{"url": url}],  # YouTube video URL
                "maxComments": 10,  # Maximum number of comments to fetch (reduced for testing)
                "commentsSortBy": "1"  # Sort comments (1 = most relevant)
            }
        else:
            # Default input for unknown platforms
            run_input = {
                "startUrls": [{"url": url}],
                "maxPosts": 100,  # Adjust as needed
            }
        
        # Run the actor
        st.info(f"Calling Apify actor: {actor_name}")
        run = client.actor(actor_name).call(run_input=run_input)
        
        # Fetch results
        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append(item)
        
        return items
    
    except Exception as e:
        st.error(f"Apify API Error: {str(e)}")
        return None

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_monthly_overview_charts(df: pd.DataFrame):
    """Create overview charts for monthly data using Streamlit native charts."""
    
    # Posts per day - handle timezone-aware datetime objects
    df_copy = df.copy()
    if 'published_at' in df_copy.columns:
        # Convert to timezone-naive if needed
        df_copy['published_at'] = df_copy['published_at'].apply(
            lambda x: x.tz_localize(None) if hasattr(x, 'tz') and x.tz is not None else x
        )
        df_copy['date'] = pd.to_datetime(df_copy['published_at']).dt.date
    else:
        df_copy['date'] = pd.to_datetime(df_copy['published_at']).dt.date
    
    posts_per_day = df_copy.groupby('date').size().reset_index(name='count')
    
    # Posts per day line chart
    st.subheader("📈 Posts Per Day")
    st.line_chart(posts_per_day.set_index('date'))
    
    # Engagement comparison
    st.subheader("📊 Total Engagement Breakdown")
    engagement_data = pd.DataFrame({
        'Metric': ['Likes', 'Comments', 'Shares'],
        'Count': [
            df['likes'].sum(),
            df['comments_count'].sum(),
            df['shares_count'].sum()
        ]
    })
    st.bar_chart(engagement_data.set_index('Metric'))
    
    # Top posts by engagement
    st.subheader("🏆 Top 5 Posts by Engagement")
    df['total_engagement'] = df['likes'] + df['comments_count'] + df['shares_count']
    top_posts = df.nlargest(5, 'total_engagement')[['text', 'total_engagement']].copy()
    top_posts['text'] = top_posts['text'].str[:50] + '...'
    top_posts = top_posts.set_index('text')
    
    st.bar_chart(top_posts)

def create_reaction_pie_chart(reactions: Dict[str, int]):
    """Create reaction breakdown chart using Streamlit native charts."""
    # Filter out zero values
    reactions_filtered = {k: v for k, v in reactions.items() if v > 0}
    
    if not reactions_filtered:
        st.info("No reaction data available for this post")
        return
    
    # Create a simple bar chart for reactions
    st.subheader("😊 Reaction Breakdown")
    reactions_df = pd.DataFrame(list(reactions_filtered.items()), columns=['Reaction', 'Count'])
    reactions_df = reactions_df.set_index('Reaction')
    st.bar_chart(reactions_df)

def create_wordcloud(comments: List[str]):
    """Generate and display word cloud from comments."""
    if not comments:
        st.info("No comments available for word cloud")
        return
    
    # Extract keywords
    keywords = extract_keywords_nlp(comments)
    
    if not keywords:
        st.info("No keywords extracted from comments")
        return
    
    # Generate word cloud
    # Use a font that supports Arabic (you may need to specify font_path)
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        relative_scaling=0.5,
        min_font_size=10
    ).generate_from_frequencies(keywords)
    
    # Display
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

# ============================================================================
# URL VALIDATION
# ============================================================================

def validate_url(url: str, platform: str) -> bool:
    """Basic URL validation by platform."""
    patterns = {
        "Facebook": r'(facebook\.com|fb\.com)',
        "Instagram": r'instagram\.com',
        "YouTube": r'(youtube\.com|youtu\.be)'
    }
    
    pattern = patterns.get(platform, '')
    return bool(re.search(pattern, url, re.IGNORECASE))

# ============================================================================
# MAIN STREAMLIT APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Social Media Analytics",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Social Media Analytics Dashboard")
    st.markdown("Analyze Facebook, Instagram, and YouTube content with AI-powered insights")
    
    # Check for API token
    apify_token = os.environ.get('APIFY_TOKEN', 'apify_api_re9vmjOyu3JAE1OWdBVcglApVHBrYq3IDeIG')
    if not apify_token:
        st.error("⚠️ APIFY_TOKEN environment variable not set!")
        st.stop()
    
    # Sidebar - Platform Selection
    st.sidebar.title("Platform Selection")
    platform = st.sidebar.radio(
        "Choose a platform:",
        ["Facebook", "Instagram", "YouTube"],
        help="Select the social media platform to analyze"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### Current Selection\n**{platform}**")
    
    # Initialize session state
    if 'posts_data' not in st.session_state:
        st.session_state.posts_data = None
    if 'selected_post_idx' not in st.session_state:
        st.session_state.selected_post_idx = None
    
    # Main area - URL Input
    st.header(f"{platform} Analysis")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input(
            f"Enter {platform} URL:",
            placeholder=f"https://www.{platform.lower()}.com/...",
            help=f"Paste the URL of the {platform} page/profile/channel"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze", type="primary", width='stretch')
    
    # Refresh button
    if st.session_state.posts_data is not None:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.session_state.posts_data = None
            st.session_state.selected_post_idx = None
            st.rerun()
    
    # Process analysis
    if analyze_button:
        if not url:
            st.warning("Please enter a URL")
            st.stop()
        
        if not validate_url(url, platform):
            st.error(f"Invalid {platform} URL. Please check and try again.")
            st.stop()
        
        # Fetch data
        with st.spinner(f"Fetching data from {platform}..."):
            raw_data = fetch_apify_data(platform, url, apify_token)
        
        if not raw_data:
            st.error("No data returned from Apify. Check your actor configuration and URL.")
            st.stop()
        
        # Normalize and filter
        normalized_data = normalize_post_data(raw_data, platform)
        st.info(f"✅ Successfully processed {len(normalized_data)} posts")
        
        # Option to show all posts or filter by current month
        filter_option = st.radio(
            "Choose data range:",
            ["Show All Posts", "Current Month Only"],
            help="Select whether to show all posts or filter to current month only"
        )
        
        if filter_option == "Current Month Only":
            current_month_posts = filter_current_month(normalized_data)
            st.info(f"Current month posts: {len(current_month_posts)} items")
            
            if not current_month_posts:
                st.warning("No posts found for the current month.")
                st.info("This could be because:")
                st.info("1. The posts are from a different month")
                st.info("2. The date field mapping is incorrect")
                st.info("3. The date format is not being parsed correctly")
                
                # Debug option: Show all posts regardless of month
                if st.button("🔍 Show All Posts Instead"):
                    st.session_state.posts_data = normalized_data
                    st.success(f"✅ Showing all {len(normalized_data)} posts")
                    st.rerun()
                st.stop()
            
            st.session_state.posts_data = current_month_posts
            st.success(f"✅ Fetched {len(current_month_posts)} posts from current month")
        else:
            st.session_state.posts_data = normalized_data
            st.success(f"✅ Showing all {len(normalized_data)} posts")
    
    # Display results
    if st.session_state.posts_data:
        posts = st.session_state.posts_data
        df = pd.DataFrame(posts)
        
        # KPI Metrics
        st.markdown("### 📈 Monthly Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Posts This Month", len(posts))
        with col2:
            st.metric("Total Likes", f"{df['likes'].sum():,}")
        with col3:
            st.metric("Total Comments", f"{df['comments_count'].sum():,}")
        with col4:
            st.metric("Total Shares", f"{df['shares_count'].sum():,}")
        
        st.markdown("---")
        
        # Visualizations
        st.markdown("### 📊 Analytics")
        create_monthly_overview_charts(df)
        
        st.markdown("---")
        
        # Posts table
        st.markdown("### 📝 Posts Details")
        display_df = df[['published_at', 'text', 'likes', 'comments_count', 'shares_count']].copy()
        display_df['text'] = display_df['text'].str[:100] + '...'
        
        # Handle timezone-aware datetime objects for display
        display_df['published_at'] = display_df['published_at'].apply(
            lambda x: x.tz_localize(None) if hasattr(x, 'tz') and x.tz is not None else x
        )
        display_df['published_at'] = pd.to_datetime(display_df['published_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df.columns = ['Date', 'Caption', 'Likes', 'Comments', 'Shares']
        
        st.dataframe(display_df, width='stretch', height=300)
        
        # Post selection
        st.markdown("### 🎯 Select a Post for Detailed Analysis")
        post_options = [f"Post {i+1}: {p['text'][:60]}..." for i, p in enumerate(posts)]
        selected_idx = st.selectbox("Choose a post:", range(len(posts)), format_func=lambda x: post_options[x])
        
        if selected_idx is not None:
            st.session_state.selected_post_idx = selected_idx
            selected_post = posts[selected_idx]
            
            st.markdown("---")
            st.markdown("### 🔍 Post Details")
            
            # Post info
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Caption:** {selected_post['text']}")
                # Handle timezone-aware datetime objects for display
                pub_date = selected_post['published_at']
                if hasattr(pub_date, 'tz') and pub_date.tz is not None:
                    pub_date = pub_date.tz_localize(None)
                st.markdown(f"**Published:** {pub_date}")
            
            with col2:
                st.metric("Shares", selected_post['shares_count'])
                st.metric("Comments", selected_post['comments_count'])
            
            # Reactions pie chart
            reactions = selected_post.get('reactions', {})
            if isinstance(reactions, dict) and reactions:
                st.markdown("#### Reaction Breakdown")
                create_reaction_pie_chart(reactions)
            else:
                # If no reaction breakdown, show simple metrics
                st.info("Detailed reaction data not available for this post")
            
            # Word cloud from comments
            st.markdown("#### 💬 Comments Word Cloud")
            comments_list = selected_post.get('comments_list', [])
            
            # Extract text from comments (handle various formats)
            comment_texts = []
            
            # Check if comments_list is actually a list, not just a count
            if isinstance(comments_list, list):
                for comment in comments_list:
                    if isinstance(comment, str):
                        comment_texts.append(comment)
                    elif isinstance(comment, dict):
                        text = comment.get('text') or comment.get('comment') or comment.get('message', '')
                        if text:
                            comment_texts.append(text)
            elif isinstance(comments_list, int):
                st.info(f"Comments count: {comments_list}. Individual comment data not available for word cloud.")
            else:
                st.info("No comment data available for word cloud.")
            
            if comment_texts:
                create_wordcloud(comment_texts)
                
                # Optional: Show sentiment distribution
                with st.expander("📊 Sentiment Analysis (Beta)"):
                    sentiments = [analyze_sentiment_placeholder(c) for c in comment_texts]
                    sentiment_counts = pd.Series(sentiments).value_counts()
                    
                    st.subheader("💭 Comment Sentiment Distribution")
                    sentiment_df = pd.DataFrame({
                        'Sentiment': sentiment_counts.index,
                        'Count': sentiment_counts.values
                    }).set_index('Sentiment')
                    st.bar_chart(sentiment_df)
            else:
                st.info("No comments available for this post")

if __name__ == "__main__":
    main()
