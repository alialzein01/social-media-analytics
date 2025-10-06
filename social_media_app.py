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
import json
import glob
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

def calculate_total_reactions(posts: List[Dict]) -> int:
    """Calculate total reactions across all posts."""
    total_reactions = 0
    for post in posts:
        reactions = post.get('reactions', {})
        if isinstance(reactions, dict):
            total_reactions += sum(reactions.values())
        elif isinstance(reactions, int):
            total_reactions += reactions
    return total_reactions

def calculate_average_engagement(posts: List[Dict]) -> float:
    """Calculate average engagement per post (likes + comments + shares + reactions)."""
    if not posts:
        return 0.0
    
    total_engagement = 0
    for post in posts:
        # Ensure numeric values
        likes = post.get('likes', 0)
        if isinstance(likes, list):
            likes = len(likes)  # If likes is a list, count the items
        elif not isinstance(likes, (int, float)):
            likes = 0
        
        comments = post.get('comments_count', 0)
        if isinstance(comments, list):
            comments = len(comments)
        elif not isinstance(comments, (int, float)):
            comments = 0
        
        shares = post.get('shares_count', 0)
        if isinstance(shares, list):
            shares = len(shares)
        elif not isinstance(shares, (int, float)):
            shares = 0
        
        reactions = post.get('reactions', {})
        
        # Calculate reactions total
        reactions_total = 0
        if isinstance(reactions, dict):
            reactions_total = sum(reactions.values())
        elif isinstance(reactions, int):
            reactions_total = reactions
        elif isinstance(reactions, list):
            reactions_total = len(reactions)
        
        # Total engagement = likes + comments + shares + reactions
        total_engagement += likes + comments + shares + reactions_total
    
    return total_engagement / len(posts)

def aggregate_all_comments(posts: List[Dict]) -> List[str]:
    """
    Aggregate all comments from all posts into a single list.
    Returns list of comment text strings.
    """
    all_comments = []
    
    for post in posts:
        comments_list = post.get('comments_list', [])
        
        if isinstance(comments_list, list):
            for comment in comments_list:
                if isinstance(comment, str):
                    all_comments.append(comment)
                elif isinstance(comment, dict):
                    # Extract text from comment object
                    text = comment.get('text') or comment.get('comment') or comment.get('message', '')
                    if text and text.strip():
                        all_comments.append(text)
        elif isinstance(comments_list, int):
            # If comments_list is just a count, we can't extract individual comments
            continue
    
    return all_comments

def analyze_all_sentiments(comments: List[str]) -> Dict[str, int]:
    """
    Analyze sentiment for all comments and return count by sentiment type.
    Returns dict with 'positive', 'negative', 'neutral' counts.
    """
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for comment in comments:
        if comment and comment.strip():
            sentiment = analyze_sentiment_placeholder(comment)
            sentiment_counts[sentiment] += 1
    
    return sentiment_counts

# ============================================================================
# FILE OPERATIONS
# ============================================================================

def save_data_to_files(raw_data: List[Dict], normalized_data: List[Dict], platform: str) -> tuple[str, str]:
    """
    Save raw and processed data to files.
    Returns tuple of (json_file_path, csv_file_path)
    """
    try:
        # Create timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure directories exist
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        # Save raw JSON data
        json_filename = f"data/raw/{platform.lower()}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Prepare CSV data with required columns
        csv_data = []
        for post in normalized_data:
            csv_row = {
                'post_id': post.get('post_id', ''),
                'published_at': post.get('published_at', ''),
                'text': post.get('text', ''),
                'likes': post.get('likes', 0),
                'comments_count': post.get('comments_count', 0),
                'shares_count': post.get('shares_count', 0),
                'reactions': json.dumps(post.get('reactions', {}), ensure_ascii=False),
                'comments_list': json.dumps(post.get('comments_list', []), ensure_ascii=False)
            }
            csv_data.append(csv_row)
        
        # Save processed CSV data
        csv_filename = f"data/processed/{platform.lower()}_{timestamp}.csv"
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        return json_filename, csv_filename
        
    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return None, None

def load_data_from_file(file_path: str) -> Optional[List[Dict]]:
    """
    Load data from a saved file (JSON or CSV).
    Returns normalized data in the same format as from API.
    """
    try:
        if file_path.endswith('.json'):
            # Load raw JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Extract platform from filename
            filename = os.path.basename(file_path)
            platform = filename.split('_')[0].title()
            
            # Normalize the data
            normalized_data = normalize_post_data(raw_data, platform)
            return normalized_data
            
        elif file_path.endswith('.csv'):
            # Load processed CSV data
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Convert back to list of dictionaries
            normalized_data = []
            for _, row in df.iterrows():
                post = {
                    'post_id': row.get('post_id', ''),
                    'published_at': pd.to_datetime(row.get('published_at', '')),
                    'text': row.get('text', ''),
                    'likes': int(row.get('likes', 0)),
                    'comments_count': int(row.get('comments_count', 0)),
                    'shares_count': int(row.get('shares_count', 0)),
                    'reactions': json.loads(row.get('reactions', '{}')),
                    'comments_list': json.loads(row.get('comments_list', '[]'))
                }
                normalized_data.append(post)
            
            return normalized_data
            
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def get_saved_files() -> Dict[str, List[str]]:
    """
    Get list of saved files organized by platform.
    Returns dict with platform as key and list of file paths as value.
    """
    try:
        files = {
            'Facebook': [],
            'Instagram': [],
            'YouTube': []
        }
        
        # Get JSON files from raw directory
        json_files = glob.glob("data/raw/*.json")
        for file_path in json_files:
            filename = os.path.basename(file_path)
            platform = filename.split('_')[0].title()
            if platform in files:
                files[platform].append(file_path)
        
        # Get CSV files from processed directory
        csv_files = glob.glob("data/processed/*.csv")
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            platform = filename.split('_')[0].title()
            if platform in files:
                files[platform].append(file_path)
        
        # Sort files by modification time (newest first)
        for platform in files:
            files[platform].sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return files
        
    except Exception as e:
        st.error(f"Error getting saved files: {str(e)}")
        return {'Facebook': [], 'Instagram': [], 'YouTube': []}

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

def create_wordcloud(comments: List[str], width: int = 800, height: int = 400, figsize: tuple = (10, 5)):
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
        width=width,
        height=height,
        background_color='white',
        colormap='viridis',
        relative_scaling=0.5,
        min_font_size=10
    ).generate_from_frequencies(keywords)
    
    # Display
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

def create_sentiment_pie_chart(sentiment_counts: Dict[str, int]):
    """Create sentiment distribution pie chart with custom colors."""
    if not sentiment_counts or sum(sentiment_counts.values()) == 0:
        st.info("No sentiment data available")
        return
    
    # Define colors
    colors = {
        'positive': '#2ecc71',  # Green
        'negative': '#e74c3c',  # Red
        'neutral': '#95a5a6'    # Gray
    }
    
    # Prepare data
    labels = []
    sizes = []
    color_list = []
    
    for sentiment, count in sentiment_counts.items():
        if count > 0:
            labels.append(sentiment.title())
            sizes.append(count)
            color_list.append(colors.get(sentiment, '#95a5a6'))
    
    if not sizes:
        st.info("No sentiment data to display")
        return
    
    # Calculate percentages
    total = sum(sizes)
    percentages = [f"{size/total*100:.1f}%" for size in sizes]
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        colors=color_list,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12, 'weight': 'bold'}
    )
    
    # Customize the chart
    ax.set_title('Sentiment Distribution', fontsize=16, fontweight='bold', pad=20)
    
    # Add count information to legend
    legend_labels = [f"{label}: {size} ({percent})" for label, size, percent in zip(labels, sizes, percentages)]
    ax.legend(wedges, legend_labels, title="Sentiment Analysis", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
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
    
    # Data Source Selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Data Source")
    data_source = st.sidebar.radio(
        "Choose data source:",
        ["Fetch from API", "Load from File"],
        help="Select whether to fetch new data from API or load previously saved data"
    )
    
    # File selector for loading saved data
    if data_source == "Load from File":
        saved_files = get_saved_files()
        platform_files = saved_files.get(platform, [])
        
        if platform_files:
            st.sidebar.markdown("#### Available Files")
            file_options = []
            for file_path in platform_files:
                filename = os.path.basename(file_path)
                # Extract timestamp from filename for display
                try:
                    timestamp_part = filename.split('_', 1)[1].replace('.json', '').replace('.csv', '')
                    display_name = f"{timestamp_part} ({'JSON' if file_path.endswith('.json') else 'CSV'})"
                except:
                    display_name = filename
                file_options.append((display_name, file_path))
            
            selected_file_display = st.sidebar.selectbox(
                "Select a file:",
                options=[opt[0] for opt in file_options],
                help="Choose a previously saved data file to load"
            )
            
            # Get the actual file path
            selected_file_path = None
            for display_name, file_path in file_options:
                if display_name == selected_file_display:
                    selected_file_path = file_path
                    break
            
            if selected_file_path and st.sidebar.button("📂 Load Selected File", type="primary"):
                with st.spinner(f"Loading data from {os.path.basename(selected_file_path)}..."):
                    loaded_data = load_data_from_file(selected_file_path)
                
                if loaded_data:
                    st.session_state.posts_data = loaded_data
                    st.success(f"✅ Successfully loaded {len(loaded_data)} posts from file")
                    st.info(f"📁 File: {selected_file_path}")
                    st.rerun()
                else:
                    st.error("Failed to load data from file")
        else:
            st.sidebar.info(f"No saved files found for {platform}")
            st.sidebar.markdown("**Tip:** Fetch data from API first to create saved files")
    
    # Initialize session state
    if 'posts_data' not in st.session_state:
        st.session_state.posts_data = None
    if 'selected_post_idx' not in st.session_state:
        st.session_state.selected_post_idx = None
    
    # Main area - URL Input (only for API fetch)
    if data_source == "Fetch from API":
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
    else:
        # For file loading, we don't need URL input
        st.header(f"{platform} Analysis - Loaded from File")
        analyze_button = False
        url = ""
    
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
        
        # Save data to files
        with st.spinner("💾 Saving data to files..."):
            json_path, csv_path = save_data_to_files(raw_data, normalized_data, platform)
        
        if json_path and csv_path:
            st.success("✅ Data saved successfully!")
            st.info(f"📄 Raw JSON: `{json_path}`")
            st.info(f"📊 Processed CSV: `{csv_path}`")
        else:
            st.warning("⚠️ Failed to save data to files")
        
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
        
        # Enhanced KPI Cards for Facebook Data
        st.markdown("### 📈 Monthly Overview")
        
        # Analysis Period Display
        now = datetime.now()
        month_year = now.strftime("%B %Y")
        st.markdown(f"**Analysis Period:** {month_year}")
        st.markdown("---")
        
        # Calculate metrics
        total_reactions = calculate_total_reactions(posts)
        total_comments = df['comments_count'].sum()
        total_shares = df['shares_count'].sum()
        avg_engagement = calculate_average_engagement(posts)
        
        # Create 4-column card layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                color: white;
                margin-bottom: 1rem;
            ">
                <h3 style="margin: 0; font-size: 2rem;">😊</h3>
                <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Reactions</h2>
            </div>
            """, unsafe_allow_html=True)
            st.metric("", f"{total_reactions:,}", help="Sum of all reaction types (like, love, wow, etc.)")
        
        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                color: white;
                margin-bottom: 1rem;
            ">
                <h3 style="margin: 0; font-size: 2rem;">💬</h3>
                <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Comments</h2>
            </div>
            """, unsafe_allow_html=True)
            st.metric("", f"{total_comments:,}", help="Total number of comments across all posts")
        
        with col3:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                color: white;
                margin-bottom: 1rem;
            ">
                <h3 style="margin: 0; font-size: 2rem;">📤</h3>
                <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Shares</h2>
            </div>
            """, unsafe_allow_html=True)
            st.metric("", f"{total_shares:,}", help="Total number of shares across all posts")
        
        with col4:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                color: white;
                margin-bottom: 1rem;
            ">
                <h3 style="margin: 0; font-size: 2rem;">📊</h3>
                <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Avg Engagement</h2>
            </div>
            """, unsafe_allow_html=True)
            st.metric("", f"{avg_engagement:.1f}", help="Average engagement per post (likes + comments + shares + reactions)")
        
        st.markdown("---")
        
        # Monthly Insights Section
        st.markdown("### 💡 Monthly Insights")
        
        # Aggregate all comments for analysis
        all_comments = aggregate_all_comments(posts)
        
        if all_comments:
            # Create two columns for insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💬 Most Discussed Topics This Month")
                # Create larger word cloud for monthly insights
                create_wordcloud(all_comments, width=1200, height=600, figsize=(15, 8))
            
            with col2:
                st.markdown("#### 😊 Sentiment Distribution")
                # Analyze sentiment for all comments
                sentiment_counts = analyze_all_sentiments(all_comments)
                create_sentiment_pie_chart(sentiment_counts)
                
                # Display summary statistics
                total_comments = sum(sentiment_counts.values())
                if total_comments > 0:
                    st.markdown("**Summary:**")
                    st.markdown(f"- **Total Comments Analyzed:** {total_comments:,}")
                    st.markdown(f"- **Positive:** {sentiment_counts['positive']:,} ({sentiment_counts['positive']/total_comments*100:.1f}%)")
                    st.markdown(f"- **Negative:** {sentiment_counts['negative']:,} ({sentiment_counts['negative']/total_comments*100:.1f}%)")
                    st.markdown(f"- **Neutral:** {sentiment_counts['neutral']:,} ({sentiment_counts['neutral']/total_comments*100:.1f}%)")
        else:
            st.info("No comments available for monthly insights analysis")
        
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
