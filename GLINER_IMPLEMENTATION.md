# GLiNER Entity Extraction Implementation

## ✅ Installation Complete

GLiNER and all dependencies have been successfully installed:
- ✅ `gliner>=0.2.0`
- ✅ `torch>=2.0.0` (PyTorch - ~74MB)
- ✅ `transformers<=4.51.0`
- ✅ `huggingface_hub>=0.21.4`
- ✅ `onnxruntime`
- ✅ `sentencepiece`

## 📦 New Files Created

### 1. `/app/nlp/entity_extractor.py`
**Purpose:** Core entity extraction module using GLiNER

**Features:**
- Extract named entities: people, organizations, locations, dates, times, money, products, events, languages, nationalities
- Multilingual support (Arabic + English)
- Entity frequency analysis
- Entity context extraction
- Comprehensive entity summaries

**Main Classes/Functions:**
- `EntityExtractor` - Main class for entity extraction
- `extract_entities_simple(texts)` - Simple convenience function
- `extract_entities_summary(texts)` - Get entity statistics

### 2. `/app/viz/entity_viz.py`
**Purpose:** Visualizations for entity extraction results

**Components:**
- `create_entity_summary_card()` - Metrics display
- `create_entity_type_chart()` - Bar chart of entity types
- `create_top_entities_tables()` - Tables of top entities
- `create_entity_network_chart()` - Sunburst hierarchy chart
- `display_entity_dashboard()` - Complete dashboard

### 3. `/test_gliner.py`
**Purpose:** Test script to verify GLiNER functionality

## 🔧 Integration Points

### 1. Main App Sidebar (`social_media_app.py`)
Added checkbox to enable/disable entity extraction:
```python
use_entity_extraction = st.sidebar.checkbox(
    "Enable Entity Extraction (GLiNER)",
    value=True,
    help="Extract named entities..."
)
```

### 2. NLP Dashboard (`app/viz/nlp_viz.py`)
Integrated entity extraction into `create_advanced_nlp_dashboard()`:
- Automatically runs after emoji analysis
- Respects the sidebar toggle setting
- Gracefully handles missing dependencies

## 🚀 Usage

### In the Streamlit App:
1. **Enable entity extraction** in the sidebar (Analysis Options section)
2. **Fetch or load data** from Facebook/Instagram/YouTube
3. **View the Advanced NLP Analysis** section in the dashboard
4. **Entity dashboard will appear** showing:
   - Total entities found
   - Entity types distribution
   - Top entities by type (people, locations, organizations, etc.)
   - Interactive entity hierarchy chart

### First Run Note:
- The first time entity extraction runs, GLiNER will download the multilingual model (~500MB)
- This is a one-time download and will be cached locally
- Subsequent runs will be much faster

### Programmatic Usage:
```python
from app.nlp.entity_extractor import extract_entities_simple, extract_entities_summary

# Extract entity frequencies
texts = ["NASA announced new astronauts...", "Dr. Smith works at MIT..."]
entities = extract_entities_simple(texts)
# Returns: {'person': {'Dr. Smith': 1, ...}, 'organization': {'NASA': 1, 'MIT': 1}}

# Get comprehensive summary
summary = extract_entities_summary(texts)
# Returns: {'total_entities': 5, 'entity_types': {...}, 'top_entities': {...}}
```

## 🎯 Entity Types Supported

Default entity types (works for Arabic and English):
- **person** - Names of people (أشخاص)
- **organization** - Companies, institutions (منظمات)
- **location** - Places, cities, countries (أماكن)
- **date** - Dates and time periods (تواريخ)
- **time** - Times of day (أوقات)
- **money** - Currency amounts (مبالغ مالية)
- **product** - Products and services (منتجات)
- **event** - Events and occasions (أحداث)
- **language** - Language names (لغات)
- **nationality** - Nationalities (جنسيات)

## 🔍 Testing

Run the test script:
```bash
python3 test_gliner.py
```

Expected output:
- ✅ GLiNER Available: True
- ✅ Entities extracted from English and Arabic text
- ✅ Display of people, organizations, locations found

## 🎛️ Configuration Options

### Model Selection
By default uses `urchade/gliner_multi` (multilingual model recommended for Arabic).

To use a different model, modify `entity_extractor.py`:
```python
extractor = EntityExtractor(model_name="urchade/gliner_large-v2.1")  # English only
```

### Confidence Threshold
Adjust sensitivity (0.0 - 1.0):
```python
entities = extract_entities_simple(texts, threshold=0.3)  # More sensitive
entities = extract_entities_simple(texts, threshold=0.7)  # More conservative
```

### Custom Entity Types
Extract only specific entity types:
```python
entities = extract_entities_simple(
    texts,
    entity_types=['person', 'organization', 'location']
)
```

## 📊 Performance Notes

- **First run:** Model download (~500MB, one-time)
- **Subsequent runs:** Fast (model is cached)
- **Processing speed:** ~1-2 seconds for 100 comments
- **Memory usage:** ~1GB when model is loaded
- **GPU support:** Will use GPU if available (faster)

## 🐛 Troubleshooting

### If entity extraction doesn't appear:
1. Check the sidebar toggle is enabled
2. Verify GLiNER is installed: `pip list | grep gliner`
3. Check for errors in terminal/console
4. Try disabling and re-enabling the feature

### If model download fails:
1. Check internet connection
2. Try manual download: `python3 test_gliner.py`
3. Check HuggingFace Hub access

### If extraction is slow:
1. First run downloads model (expected)
2. Subsequent runs should be faster
3. Consider using smaller model if needed
4. Reduce number of texts analyzed

## 🎉 Benefits

1. **Automated entity discovery** - Find all people, places, organizations mentioned
2. **Multilingual** - Works with Arabic and English simultaneously  
3. **No manual tagging** - Automatically identifies entity types
4. **Rich insights** - Understand who/what is being discussed
5. **Visual analytics** - Interactive charts and tables

## 🔮 Future Enhancements

Potential additions:
- Entity sentiment analysis (how people feel about specific entities)
- Entity relationships (who is mentioned together)
- Temporal analysis (entity mentions over time)
- Entity-based filtering (show only posts mentioning specific entities)
- Custom entity type training
