# 📊 Social Media Analytics Dashboard

A powerful Streamlit application that analyzes social media content from Facebook, Instagram, and YouTube using Apify web scraping actors. The app provides comprehensive analytics including engagement metrics, sentiment analysis, and interactive visualizations.

## ✨ Features

- **Multi-Platform Support**: Analyze content from Facebook, Instagram, and YouTube
- **Real-time Data**: Fetch live data using Apify web scraping actors
- **Interactive Analytics**: 
  - Posts per day trends
  - Engagement breakdown (likes, comments, shares)
  - Top performing posts
  - Reaction analysis
- **AI-Powered Insights**:
  - Word cloud generation from comments
  - Sentiment analysis (Arabic and English support)
  - Keyword extraction
- **Modern UI**: Clean, responsive interface built with Streamlit
- **Flexible Date Filtering**: View all posts or filter by current month

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

5. **Run the application**
   ```bash
   streamlit run social_media_app.py
   ```

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

- **Facebook**: `apify/facebook-posts-scraper`
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
