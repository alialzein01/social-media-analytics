# Quick Start - Testing Guide

Run the Facebook platform test to verify everything works!

## 🚀 Quick Test (Recommended)

```bash
# 1. Set your API token
export APIFY_TOKEN=your_token_here

# 2. Run the Facebook test
python scripts/test_facebook.py
```

This will:

- ✅ Test NASA's Facebook page (https://facebook.com/nasa)
- ✅ Fetch 5 posts
- ✅ Validate data structure
- ✅ Test analytics & NLP
- ✅ Generate a report

**Expected time:** ~45-60 seconds

## 📊 What You'll See

```
======================================================================
  FACEBOOK PLATFORM TEST SUITE
  Testing URL: https://facebook.com/nasa
======================================================================

======================================================================
  TEST 1: Environment Validation
======================================================================

✅ PASS: Environment: APIFY_TOKEN
✅ PASS: Environment: Python Version

... (more tests)

======================================================================
TEST SUMMARY
======================================================================
Total Tests: 24
✅ Passed: 24
❌ Failed: 0
⚠️  Warnings: 0
Duration: 45.32s
======================================================================

📝 Test results saved to: scripts/test_results_facebook_20251031_143022.json
```

## 🔧 Test Configuration

To customize the test, edit `scripts/test_facebook.py`:

```python
TEST_CONFIG = {
    'url': 'https://facebook.com/nasa',    # Change URL here
    'max_posts': 5,                        # Increase for more posts
    'fetch_comments': False,               # Set True to test comments
    'max_comments_per_post': 10,           # Comments per post
}
```

## ⚡ Quick Commands

```bash
# Run Facebook test
python scripts/test_facebook.py

# Run all tests
python scripts/run_tests.py

# Get help
python scripts/run_tests.py --help
```

## 📁 Test Results

Results are saved to: `scripts/test_results_facebook_TIMESTAMP.json`

## 🐛 Troubleshooting

**"APIFY_TOKEN not set"**

```bash
export APIFY_TOKEN=your_actual_token
```

**"Module not found"**

```bash
# Make sure you're in project root
cd /Users/ali/Desktop/claudeProject
python scripts/test_facebook.py
```

**"No posts returned"**

- Check your Apify account has credits
- Verify the Facebook URL is accessible
- Try a different Facebook page URL

## ✅ Success Criteria

A successful test should have:

- ✅ All environment checks pass
- ✅ Posts fetched (at least 1)
- ✅ Data structure validated
- ✅ Analytics calculated
- ✅ NLP processing completed
- ✅ No critical failures

## 📖 Full Documentation

See [`scripts/README.md`](./README.md) for complete documentation.
