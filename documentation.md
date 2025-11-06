Apify Actor Documentation for Selected Scrapers (2025‑11‑02)

The Apify platform offers ready‑made “Actors” for scraping social‑media data. Each actor accepts input parameters (JSON schema) and produces a dataset as output. The table below summarises the input fields, output structure, API endpoints and Python client usage for the actors seen in the user’s console screenshot. All API calls require an Apify account and API token.

Facebook Posts Scraper – community version (scraper_one/facebook‑posts‑scraper)

Purpose: Scrapes posts from Facebook pages or groups and returns post text, engagement metrics and author info.

Inputs

pageUrls (array, required) – List of Facebook page or group URLs to scrape
apify.com
.

resultsLimit (integer, optional) – Limit on the number of posts per page
apify.com
.

Output structure

The dataset contains one item per post with fields such as:

url, pageUrl, timestamp, postText (post text),

reactionsCount and a nested reactions object (counts of like/love/sad/angry/haha reactions),

commentsCount, postId,

author object with id, name, profilePictureUrl and profileUrl
apify.com
.

API endpoints

Run actor: POST /v2/acts/scraper_one~facebook-posts-scraper/runs
apify.com
.

Run synchronously: POST /v2/acts/scraper_one~facebook-posts-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/scraper_one~facebook-posts-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"pageUrls": ["https://www.facebook.com/NASA"],
"resultsLimit": 10,
}

# Run the actor

run = client.actor("scraper_one/facebook-posts-scraper").call(run_input=run_input)

# Iterate scraped posts

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
print(item)

The code above initialises the Apify client, runs the actor with a list of page URLs and a posts limit, then iterates through the dataset items
apify.com
.

Facebook Posts Scraper – official version (scraper_one/facebook‑posts‑scraper)

Purpose: Extracts posts and associated metrics from public Facebook pages and profiles.

Inputs

startUrls (array, required) – List of page or profile URLs
apify.com
.

resultsLimit (integer, optional) – Maximum number of posts to scrape per URL
apify.com
.

captionText (boolean, optional) – Include video transcript/caption in results
apify.com
.

onlyPostsNewerThan / onlyPostsOlderThan (string, optional) – ISO date (YYYY‑MM‑DD) or relative time (e.g., 3 days ago) to filter posts by age
apify.com
.

Output structure

Each dataset item includes:

postId, url, pageUrl (profile or page),

text (post message), timestamp, likes, shares, comments, reactions etc
apify.com
.

API endpoints

Run actor: POST /v2/acts/scraper_one~facebook-posts-scraper/runs
apify.com
.

Run synchronously & get dataset: POST /v2/acts/scraper_one~facebook-posts-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/scraper_one~facebook-posts-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"startUrls": ["https://www.facebook.com/nasa"],
"resultsLimit": 10,
"captionText": False,
"onlyPostsNewerThan": "2025-01-01",
}
run = client.actor("scraper_one/facebook-posts-scraper").call(run_input=run_input)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
print(item)

The client sends a JSON input with page URLs and filtering options and retrieves the results dataset
apify.com
.

Facebook Comments Scraper (apify/facebook‑comments‑scraper)

Purpose: Collects comments from Facebook posts/reels/videos.

Inputs

startUrls (array, required) – Facebook URLs (posts, reels or videos)
apify.com
.

resultsLimit (integer, optional) – Max number of comments per URL
apify.com
.

includeNestedComments (boolean, optional) – Include replies up to 3 levels deep
apify.com
.

viewOption (enum, optional) – Sorting of comments: RANKED_THREADED, RECENT_ACTIVITY or RANKED_UNFILTERED
apify.com
.

Output structure

Each comment item contains:

id, postId, commentText, authorName, authorUrl,

likesCount, timestamp, replies (if nested comments are included),

plus metadata about the parent post
apify.com
.

API endpoints

Run actor: POST /v2/acts/apify~facebook-comments-scraper/runs
apify.com
.

Run synchronously & get dataset: POST /v2/acts/apify~facebook-comments-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/apify~facebook-comments-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"startUrls": ["https://www.facebook.com/permalink.php?story_fbid=..."],
"resultsLimit": 50,
"includeNestedComments": True,
"viewOption": "RANKED_THREADED",
}
run = client.actor("apify/facebook-comments-scraper").call(run_input=run_input)
for comment in client.dataset(run["defaultDatasetId"]).iterate_items():
print(comment)

Facebook Reactions Scraper (scraper_one/facebook‑reactions‑scraper)

Purpose: Extracts detailed reaction information from Facebook posts.

Inputs

postUrls (array, required) – List of Facebook post URLs
apify.com
.

resultsLimit (integer, optional) – Maximum number of reactions to fetch per post
apify.com
.

Output structure

Each dataset item represents a user’s reaction and includes:

reactionType (e.g., like, love, haha, wow, sad),

reactionIcon (URL of the reaction emoji),

postUrl, reactorName, reactorId,

reactorProfilePicture, reactorProfileUrl
apify.com
.

API endpoints

Run actor: POST /v2/acts/scraper_one~facebook-reactions-scraper/runs
apify.com
.

Run synchronously: POST /v2/acts/scraper_one~facebook-reactions-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/scraper_one~facebook-reactions-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"postUrls": ["https://www.facebook.com/permalink.php?story_fbid=..."],
"resultsLimit": 100,
}
run = client.actor("scraper_one/facebook-reactions-scraper").call(run_input=run_input)
for reaction in client.dataset(run["defaultDatasetId"]).iterate_items():
print(reaction)

Instagram Scraper (apify/instagram‑scraper)

Purpose: A flexible scraper for Instagram. It can retrieve posts, comments, profile details, mentions, hashtags, places or stories depending on the resultsType value. It replaces functionality removed from the official Instagram API.

Inputs

directUrls (array, optional) – One or more Instagram URLs (profiles, hashtags, posts, places). If provided, the actor will scrape these URLs
apify.com
.

resultsType (enum, optional) – What to scrape: posts, comments, details, mentions or stories (default posts)
apify.com
.

resultsLimit (integer, optional) – Maximum number of posts or comments to scrape per URL (maximum ~50 comments per post)
apify.com
.

onlyPostsNewerThan (string, optional) – Filter posts newer than a date or relative time (e.g., 2025-01-01 or 3 weeks)
apify.com
.

isUserTaggedFeedURL / isUserReelFeedURL (booleans) – Scrape a user’s tagged posts or reel feed
apify.com
.

search (string, optional) – Search term. Use together with searchType (user, hashtag, place)
apify.com
.

searchLimit (integer, optional) – Number of search results to return
apify.com
.

enhanceUserSearchWithFacebookPage (boolean) – For top 10 search results, fetch the connected Facebook page to extract business e‑mail. This may return personal data and should be used with caution
apify.com
.

addParentData (boolean, optional) – For feed items, include information about the parent search (source page or hashtag)
apify.com
.

Output structure

The output varies by resultsType. Key fields include:

Posts output
apify.com
:

inputUrl (original URL), url (post link), type (image/video), shortCode, caption, hashtags, mentions,

commentsCount, firstComment, latestComments (list),

dimensionsHeight, dimensionsWidth, displayUrl, alt, likesCount, timestamp,

childPosts (for carousels), ownerFullName, ownerUsername, ownerId, isSponsored.

Comments output
apify.com
:

id, postId, text, position (order of comment), timestamp,

ownerId, ownerIsVerified, ownerUsername, ownerProfilePicUrl.

Profile output
apify.com
:

id, username, fullName, biography, externalUrl, followersCount, followsCount,

businessCategoryName, profilePicUrl, profilePicUrlHD, isPrivate, isVerified, etc.

API endpoints

Run actor: POST /v2/acts/apify~instagram-scraper/runs
apify.com
.

Run synchronously & get dataset: POST /v2/acts/apify~instagram-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/apify~instagram-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"directUrls": ["https://www.instagram.com/nasa/"],
"resultsType": "posts",
"resultsLimit": 20,
"onlyPostsNewerThan": "1 month",
}
run = client.actor("apify/instagram-scraper").call(run_input=run_input)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
print(item)

This call scrapes the latest posts from the NASA Instagram account with a relative time filter
apify.com
.

Instagram Comments Scraper (apify/instagram‑comment‑scraper)

Purpose: Extracts comments (and optionally replies) from Instagram posts or reels.

Inputs

directUrls (array, required) – One or multiple Instagram post or reel URLs
apify.com
.

resultsLimit (integer, optional) – Number of comments to scrape per URL; note that including replies will increase this number
apify.com
.

isNewestComments (boolean, optional) – When true (pay‑only feature), scrape newest comments first
apify.com
.

includeNestedComments (boolean, optional) – Include replies; each reply counts as a separate result
apify.com
.

Output structure

Each comment item includes:

id, postId, text, position, timestamp,

ownerId, ownerIsVerified, ownerUsername, ownerProfilePicUrl
apify.com
.

API endpoints

Run actor: POST /v2/acts/apify~instagram-comment-scraper/runs
apify.com
.

Run synchronously & get dataset: POST /v2/acts/apify~instagram-comment-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/apify~instagram-comment-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"directUrls": ["https://www.instagram.com/p/POST_ID/"],
"resultsLimit": 50,
"includeNestedComments": True,
}
run = client.actor("apify/instagram-comment-scraper").call(run_input=run_input)
for comment in client.dataset(run["defaultDatasetId"]).iterate_items():
print(comment)

This code scrapes up to 50 comments per URL and includes replies
apify.com
.

YouTube Scraper (streamers/youtube‑scraper)

Purpose: A comprehensive YouTube crawler that extracts videos, channels, playlists, search results, and can download subtitles. It serves as a more flexible alternative to the official YouTube API.

Inputs (selected fields)

searchQueries (array, optional) – List of keywords to search on YouTube
apify.com
.

maxResults (integer, optional) – Maximum number of regular videos to scrape per search term
apify.com
.

maxResultsShorts / maxResultStreams (integers, optional) – Max number of shorts or live streams per query
apify.com
.

startUrls (array, optional) – Direct YouTube URLs (videos, channels, playlists, hashtags or search result pages). When provided, searchQueries are ignored
apify.com
.

downloadSubtitles (boolean) – Download available subtitles and convert them to .srt
apify.com
.

saveSubsToKVS (boolean) – Save subtitles to a key‑value store
apify.com
.

subtitlesLanguage (enum) – Language of subtitles (any, en, de, etc.)
apify.com
.

preferAutoGeneratedSubtitles (boolean) – Prefer auto‑generated subtitles when a language is selected
apify.com
.

subtitlesFormat (enum) – Output format (srt, vtt, xml, plaintext)
apify.com
.

sortingOrder (enum) – Sort search results by relevance, rating, date, or viewCount
apify.com
.

dateFilter (enum) – Upload date filter (hour, today, week, month, year)
apify.com
.

videoType (enum) – Filter by video type (video or movie)
apify.com
.

lengthFilter (enum) – Filter by video length (under4, between420, plus20)
apify.com
.

Additional booleans: isHD, hasSubtitles, hasCC, is3D, isLive, isBought, is4K, is360, hasLocation, isHDR, isVR180 control specific features of the scraped videos
apify.com
.

oldestPostDate (string, optional) – Only scrape videos uploaded after this date or relative time; automatically sets sorting to the newest
apify.com
.

Output structure

Results vary depending on the input and the YouTube URL type:

Channel information: fields include id, title, duration, channelName, channelUrl, date, url, viewCount, fromYTUrl, channelDescription, channelDescriptionLinks, channelJoinedDate, channelLocation, channelTotalVideos, channelTotalViews, numberOfSubscribers, isMonetized, inputChannelUrl
apify.com
.

Single video: title, id, url, thumbnailUrl, viewCount, date, likes, location, channelName, channelUrl, numberOfSubscribers, duration, commentsCount, text, descriptionLinks, subtitles, comments, isMonetized, commentsTurnedOff
apify.com
.

Playlist item: id, title, duration, channelName, channelUrl, date, url, viewCount, fromYTUrl
apify.com
.

Search result item: id, title, duration, channelName, channelUrl, date, url, viewCount, fromYTUrl
apify.com
.

Subtitles: Each subtitle entry contains srtUrl, type (language code), language, and the srt text
apify.com
.

API endpoints

Run actor: POST /v2/acts/streamers~youtube-scraper/runs
apify.com
.

Run synchronously & get dataset: POST /v2/acts/streamers~youtube-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/streamers~youtube-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"searchQueries": ["Halestorm Unapologetic"],
"maxResults": 5,
"maxResultsShorts": 0,
"maxResultStreams": 0,
"downloadSubtitles": True,
"subtitlesLanguage": "en",
"sortingOrder": "date",
"dateFilter": "week",
}
run = client.actor("streamers/youtube-scraper").call(run_input=run_input)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
print(item)

This example searches YouTube for a term, retrieves five videos uploaded in the past week, downloads English subtitles and prints the results
apify.com
.

YouTube Comments Scraper (streamers/youtube‑comments‑scraper)

Purpose: Scrapes comments from specified YouTube videos. It serves as an alternative to the official YouTube Data API and is designed for high‑volume extraction without quotas.

Inputs

startUrls (array, required) – List of direct YouTube video URLs
apify.com
.

maxComments (integer, optional) – Limit on the number of comments to scrape per video
apify.com
.

commentsSortBy (enum, optional) – Sorting method for comments; values "0" (Top comments) or "1" (Newest comments), default "1"
apify.com
.

Output structure

Each output item corresponds to one comment and includes fields such as:

comment (full text of the comment), cid (comment ID), author (username),

videoId, pageUrl, commentsCount (total comments on the video), replyCount (number of replies under this comment), voteCount (likes),

authorIsChannelOwner, hasCreatorHeart, type (comment or reply), replyToCid (if the comment is a reply), and title (video title)
apify.com
.

API endpoints

Run actor: POST /v2/acts/streamers~youtube-comments-scraper/runs
apify.com
.

Run synchronously & get dataset: POST /v2/acts/streamers~youtube-comments-scraper/run-sync-get-dataset-items
apify.com
.

Get actor info: GET /v2/acts/streamers~youtube-comments-scraper
apify.com
.

Python client example
from apify_client import ApifyClient

client = ApifyClient('<API_TOKEN>')
run_input = {
"startUrls": [ { "url": "https://www.youtube.com/watch?v=xObhZ0Ga7EQ" } ],
"maxComments": 10,
}
run = client.actor("streamers/youtube-comments-scraper").call(run_input=run_input)
print("Check your data here: https://console.apify.com/storage/datasets/" + run["defaultDatasetId"])
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
print(item)

This script runs the YouTube Comments Scraper on a specific video, limiting the scrape to 10 comments, and iterates through the dataset items
apify.com
.

HTTP API example

You can call the scraper via REST API using curl:

# Prepare input JSON

cat > input.json <<'EOF'
{
"startUrls": [
{ "url": "https://www.youtube.com/watch?v=xObhZ0Ga7EQ" }
],
"maxComments": 10
}
EOF

# Run the actor

curl "https://api.apify.com/v2/acts/streamers~youtube-comments-scraper/runs?token=<YOUR_API_TOKEN>" \
 -X POST -H 'Content-Type: application/json' -d @input.json

The same endpoints can be used synchronously or to fetch actor details
apify.com
.

How to use this information

Select the appropriate actor depending on the platform (Facebook, Instagram or YouTube) and the type of data required (posts, comments, reactions, profiles, videos etc.).

Prepare the input JSON according to the actor’s schema. Use arrays of URLs for direct scraping or keywords and filters for search‑based actors.

Run the actor via API or Apify UI, specifying your API token. Use synchronous endpoints for immediate results or asynchronous runs when collecting large datasets.

Access the dataset via the returned defaultDatasetId and download it in the desired format (JSON, CSV, Excel, etc.).

For automation or integration, use the Python apify-client library as shown in the examples above.
