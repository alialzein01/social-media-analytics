# 📊 Social Media Analytics Dashboard

A powerful Streamlit application that analyzes social media content from Facebook, Instagram, and YouTube using Apify web scraping actors. The app provides comprehensive analytics including engagement metrics, sentiment analysis, and interactive visualizations.

## ✨ Features

- **Multi-Platform Support**: Analyze content from Facebook, Instagram, and YouTube
- **Real-time Data**: Fetch live data using Apify web scraping actors
- **Two-Phase Facebook Workflow**: 
  - Phase 1: Extract posts from Facebook pages
  - Phase 2: Extract comments from all posts using batch processing
- **Interactive Analytics**: 
  - Posts per day trends
  - Engagement breakdown (likes, comments, shares)
  - Top performing posts
  - Reaction analysis
- **AI-Powered Insights**:
  - Word cloud generation from comments
  - Sentiment analysis (Arabic and English support)
  - Keyword extraction
  - Phrase-based analysis for better accuracy
- **Modern UI**: Clean, responsive interface built with Streamlit
- **Flexible Date Filtering**: View all posts or filter by current month
- **Batch Comment Processing**: Efficient extraction of comments from multiple posts
- **Optional MongoDB**: Save scraped data to MongoDB and load it later via "Load from Database" (when `MONGODB_URI` is configured)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Apify API token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alialzein01/social-media-analytics.git
   cd social-media-analytics
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Apify API token**
   ```bash
   export APIFY_TOKEN=your_apify_token_here
   ```
   Or add to `.streamlit/secrets.toml`: `APIFY_TOKEN = "your_token"`

5. **(Optional) Set up MongoDB for "Load from Database"**
   To enable saving and loading data from MongoDB:
   - Set `MONGODB_URI` (e.g. `mongodb://localhost:27017/` or your Atlas URI)
   - Set `MONGODB_DATABASE` (default: `social_media_analytics`)
   - In `.streamlit/secrets.toml`: `MONGODB_URI = "..."` and `MONGODB_DATABASE = "social_media_analytics"`
   - Or use environment variables. If not set, the app runs without database (file-only save/load).

6. **Run the application**
   ```bash
   streamlit run social_media_app.py
   ```

## 🔄 Facebook Comments Workflow

The app now features a sophisticated two-phase workflow for Facebook analysis:

### Phase 1: Posts Extraction
- Extracts posts from any Facebook page
- Captures post URLs, text, engagement metrics
- Uses `zanTWNqB3Poz44qdY` (scraper_one/facebook-posts-scraper) actor

### Phase 2: Comments Extraction
- Takes all post URLs from Phase 1
- Extracts comments using batch processing
- Uses `us5srxAYnsrkgUv2v` (apify-facebook-comments-scraper) actor
- Supports both batch and individual processing methods

### How to Use
1. Select "Facebook" as platform
2. Choose "Fetch from API" as data source
3. Select "Batch Processing" for comment extraction method
4. Enable "Fetch Detailed Comments"
5. Enter Facebook page URL and click "Analyze"

For detailed documentation, see [FACEBOOK_COMMENTS_WORKFLOW.md](FACEBOOK_COMMENTS_WORKFLOW.md)

## 📱 Usage

1. **Select Platform**: Choose between Facebook, Instagram, or YouTube
2. **Enter URL**: Paste the URL of the page/profile/channel you want to analyze
3. **Choose Data Range**: Select "Show All Posts" or "Current Month Only"
4. **Analyze**: Click "Analyze" to fetch and process the data
5. **Explore**: View analytics, select individual posts for detailed analysis

### Supported URL Formats

- **Facebook**: `https://www.facebook.com/NASA/`
- **Instagram**: `https://www.instagram.com/nasa/`
- **YouTube**: `https://www.youtube.com/@NASA`

## 🛠️ Configuration

### Apify Actors

The app uses the following Apify actors:

- **Facebook**: `zanTWNqB3Poz44qdY` (scraper_one/facebook-posts-scraper)
- **Instagram**: `apify/instagram-scraper`
- **YouTube**: `streamers/youtube-comments-scraper`

### Customization

You can modify the following in `social_media_app.py`:

- **Results Limit**: Change `resultsLimit` and `maxComments` for different data volumes
- **Date Filtering**: Modify `filter_current_month()` for different time ranges
- **NLP Models**: Replace placeholder sentiment analysis with advanced models

## 📊 Analytics Features

### Overview Metrics
- Total posts count
- Total likes, comments, and shares
- Engagement trends over time

### Individual Post Analysis
- Detailed post information
- Reaction breakdown
- Comment sentiment analysis
- Word cloud from comments

### Visualizations
- Line charts for time-series data
- Bar charts for categorical data
- Interactive data tables

## 🌍 Multi-Language Support

The app includes basic Arabic NLP capabilities:

- Arabic text cleaning and tokenization
- Arabic stopwords filtering
- Extensible for advanced Arabic NLP models (AraBERT, CAMeL Tools)

## 🔧 Technical Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **Web Scraping**: Apify Client
- **Visualization**: Streamlit Native Charts
- **NLP**: Custom Arabic/English text processing
- **Word Clouds**: WordCloud library

## 📁 Project Structure

```
social-media-analytics/
├── social_media_app.py      # Main application
├── requirements.txt         # Python dependencies
├── test_facebook.py        # Facebook scraper test
├── test_instagram.py       # Instagram scraper test
├── test_youtube.py         # YouTube scraper test
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Apify](https://apify.com/) for web scraping infrastructure
- [Streamlit](https://streamlit.io/) for the web framework
- [Pandas](https://pandas.pydata.org/) for data processing

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/alialzein01/social-media-analytics/issues) page
2. Create a new issue with detailed information
3. Contact: [@alialzein01](https://github.com/alialzein01)

---

**Made with ❤️ by [Ali Alzein](https://github.com/alialzein01)**
