# Testing Scripts

Professional test scripts for validating the Social Media Analytics application.

## 📋 Available Tests

### `test_facebook.py` - Facebook Platform Test Suite

Comprehensive testing script that validates the complete Facebook data pipeline.

**What it tests:**

1. ✅ Environment validation (API token, Python version)
2. ✅ Adapter initialization
3. ✅ URL validation (multiple test cases)
4. ✅ Actor input configuration
5. ✅ Data fetching from Facebook
6. ✅ Post data structure validation
7. ✅ Analytics calculations (engagement, hashtags, emojis)
8. ✅ NLP processing (phrase extraction, sentiment analysis)
9. ✅ Comment fetching (optional)

## 🚀 Usage

### Quick Test (No Comments)

```bash
# Set your API token
export APIFY_TOKEN=your_token_here

# Run the test
python scripts/test_facebook.py
```

### Full Test (With Comments)

Edit `scripts/test_facebook.py` and set:

```python
TEST_CONFIG = {
    'fetch_comments': True,  # Enable comment fetching
    'max_comments_per_post': 10
}
```

Then run:

```bash
python scripts/test_facebook.py
```

## 📊 Test Output

The script provides:

1. **Real-time progress** - See each test as it runs with ✅/❌/⚠️ indicators
2. **Detailed results** - View data structure, API responses, and analysis results
3. **Summary report** - Final statistics of passed/failed/warning tests
4. **JSON report** - Saved to `scripts/test_results_facebook_TIMESTAMP.json`

### Example Output:

```
======================================================================
  FACEBOOK PLATFORM TEST SUITE
  Testing URL: https://facebook.com/nasa
======================================================================

======================================================================
  TEST 1: Environment Validation
======================================================================

✅ PASS: Environment: APIFY_TOKEN
   Token found (length: 48)
✅ PASS: Environment: Python Version
   Python 3.11.5

======================================================================
  TEST 2: Adapter Initialization
======================================================================

✅ PASS: Adapter: Initialization
   FacebookAdapter created successfully
✅ PASS: Adapter: Method validate_url
   Method exists
...

======================================================================
TEST SUMMARY
======================================================================
Total Tests: 25
✅ Passed: 24
❌ Failed: 0
⚠️  Warnings: 1
Duration: 45.32s
======================================================================
```

## 🎯 Test Configuration

Edit the `TEST_CONFIG` dictionary at the top of each test script:

```python
TEST_CONFIG = {
    'url': 'https://facebook.com/nasa',      # URL to test
    'max_posts': 5,                          # Number of posts to fetch
    'fetch_comments': False,                 # Enable comment testing
    'max_comments_per_post': 10,             # Comments per post
    'from_date': '2024-10-01',               # Date range filtering
    'to_date': None
}
```

## 📝 Test Reports

Test results are automatically saved to:

```
scripts/test_results_facebook_YYYYMMDD_HHMMSS.json
```

The JSON report includes:

- Test configuration used
- All passed tests with timestamps
- All failed tests with error details
- Warnings and messages
- Total test duration

## 🔍 What Each Test Validates

### Test 1: Environment Validation

- Checks `APIFY_TOKEN` is set
- Validates Python version
- Ensures dependencies are importable

### Test 2: Adapter Initialization

- Creates FacebookAdapter instance
- Verifies all required methods exist
- Tests adapter configuration

### Test 3: URL Validation

- Tests valid Facebook URLs
- Tests invalid URLs (Instagram, empty, malformed)
- Verifies correct validation logic

### Test 4: Actor Input Building

- Constructs Apify actor input
- Validates required fields
- Checks date parameter handling

### Test 5: Data Fetching

- Calls Apify actor
- Fetches real Facebook posts
- Validates API response

### Test 6: Post Structure

- Validates normalized post structure
- Checks required fields exist
- Verifies data types

### Test 7: Analytics Calculations

- Tests engagement calculations
- Validates hashtag extraction
- Tests emoji analysis
- Checks comment aggregation

### Test 8: NLP Processing

- Tests phrase extraction
- Validates sentiment analysis
- Checks text processing

### Test 9: Comment Fetching (Optional)

- Fetches comments for posts
- Validates comment structure
- Tests comment normalization

## 🛠️ Troubleshooting

### "APIFY_TOKEN not set"

```bash
export APIFY_TOKEN=your_token_here
```

### "Module not found"

Make sure you're in the project root:

```bash
cd /path/to/claudeProject
python scripts/test_facebook.py
```

### "No posts returned"

- Check the URL is valid
- Verify the Facebook page exists
- Ensure your Apify account has credits

### Test takes too long

Reduce `max_posts` in `TEST_CONFIG`:

```python
'max_posts': 3  # Smaller number for faster tests
```

## 📦 Future Tests

Coming soon:

- `test_instagram.py` - Instagram platform tests
- `test_youtube.py` - YouTube platform tests
- `test_integration.py` - End-to-end integration tests
- `test_performance.py` - Performance benchmarking

## 🤝 Contributing

To add new tests:

1. Create a new test function following the naming pattern: `test_<feature_name>`
2. Use the `TestResult` class to track pass/fail/warning
3. Add comprehensive error handling with try/except
4. Print detailed progress information
5. Update this README with test documentation

## 📄 License

Same as the main project.
