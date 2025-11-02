# Facebook Actors Documentation (samples + input shapes)

This file contains concrete example outputs and example input schemas for the two Apify actors you requested:

- `scraper_one/facebook-posts-scraper` (posts with reactions)
- `apify/facebook-comments-scraper` (comments for posts)

Use these samples for adapter development, unit tests (mocking Apify dataset items), and migration scripts.

---

## scraper_one/facebook-posts-scraper — Sample output (array of items)

```json
[
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid02RQFkBznr3x9MwKvPeBh2VHhboC7JEzbzEW3QG5aWXJnLuiXjfGhT21hhKA1zLXuXl",
    "postId": "1220007700156055",
    "postText": "إعلان عن صدور نتائج المعادلات للطلاب القادمين من داخل الجامعة اللبنانية",
    "reactions": {
      "like": 31
    },
    "reactionsCount": 31,
    "timestamp": 1761638896000,
    "commentsCount": 1,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    },
    "attachments": [
      {
        "type": "photo",
        "url": "https://www.facebook.com/photo/?fbid=1220007673489391&set=a.465364825620350",
        "id": "1220007673489391",
        "accessibilityCaption": "May be an image of ticket stub and text"
      }
    ]
  },
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid02rmKG1AiB2cRdtVwaKvLXXvdf8VUyXSxaMG6ugc2SYj2roqFeK2i36wgN7QeokLtzl",
    "postId": "1206928638130628",
    "postText": "صدور نتائج طلبات المعادلة للطلاب القادمين من خارج الجامعة اللبنانية، وذلك للعام الجامعي 2025-2026",
    "reactions": {
      "like": 59
    },
    "reactionsCount": 59,
    "timestamp": 1760346931000,
    "commentsCount": 5,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    },
    "attachments": [
      {
        "type": "photo",
        "url": "https://www.facebook.com/photo/?fbid=1206928614797297&set=a.465364825620350",
        "id": "1206928614797297",
        "accessibilityCaption": "May be an image of text"
      }
    ]
  },
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid0V48BAs9zCVjt5ZcZrToiydjnrV9BYNF6XnHDk5mtp2bPBovtKpLnEhWXvNPywK9vl",
    "postId": "1204120265078132",
    "postText": "دعوة حول انتخاب  مجالس الفروع وممثلي الأساتذة في كلية العلوم",
    "reactions": {
      "like": 28
    },
    "reactionsCount": 28,
    "timestamp": 1760081991000,
    "commentsCount": 0,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    },
    "attachments": [
      {
        "type": "photo",
        "url": "https://www.facebook.com/photo/?fbid=1204120251744800&set=a.465364825620350",
        "id": "1204120251744800",
        "accessibilityCaption": "May be an image of ticket stub, blueprint and text"
      }
    ]
  },
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid02P8DjpCxRVZH4JYMja4A44At7j5ZRxRDxaMzCnEYUFhRpEZBkcY4qczPwTJ1X1FxJl",
    "postId": "1197812525708906",
    "postText": "إعلان طلبات ترشح للماستر ٢ بحثي\nMolecular Immunology and Cancer Biology \nللعام الجامعي ٢٠٢٥ - ٢٠٢٦\n\n",
    "reactions": {
      "like": 14
    },
    "reactionsCount": 14,
    "timestamp": 1759505525000,
    "commentsCount": 0,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    }
  },
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid0aLEsji3AaXVUqeb5uuUuGvK39zBwtJG7CHBiE222mNNntitr2GaVFSk7iVcpmFeWl",
    "postId": "1176284361195056",
    "postText": "للتذكير",
    "reactions": {
      "like": 26
    },
    "reactionsCount": 26,
    "timestamp": 1751269958000,
    "commentsCount": 3,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    }
  },
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid09MTZT7ixpyXbhff2DiZfXCy7H88kZkZ7i3BwirFvB5NQVS3vUB5EycDyPgTEZGAul",
    "postId": "1173218691501623",
    "postText": "إعلان عن بدء استقبال طلبات المعادلات  والإعفاءات للطلاب القادمين من داخل الجامعة اللبنانية",
    "reactions": {
      "like": 111,
      "love": 2
    },
    "reactionsCount": 113,
    "timestamp": 1756975653000,
    "commentsCount": 6,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    },
    "attachments": [
      {
        "type": "photo",
        "url": "https://www.facebook.com/photo/?fbid=1173218671501625&set=a.465364825620350",
        "id": "1173218671501625",
        "accessibilityCaption": "May be an image of ‎ticket stub and ‎text..."
      }
    ]
  },
  {
    "url": "https://www.facebook.com/ul.fsciences/posts/pfbid02tzHw6X41SDwWZDspq8WXfGNNpNdhoieYLSdeCHecJMc38c8B1ezxCUBDD54mmhf4l",
    "postId": "1168006615356164",
    "postText": "أسماء الطلاب المقبولين في الماستر البحثي\nMicrowave\nللعام الجامعي 2025 – 2026",
    "reactions": {
      "like": 166,
      "love": 6,
      "haha": 2,
      "wow": 1
    },
    "reactionsCount": 175,
    "timestamp": 1756392037000,
    "commentsCount": 61,
    "author": {
      "id": "100064405103773",
      "name": "Lebanese University - Faculty of Science",
      "profilePicture": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "profileUrl": "https://www.facebook.com/ul.fsciences"
    },
    "attachments": [
      {
        "type": "photo",
        "url": "https://www.facebook.com/photo/?fbid=1168006592022833&set=a.465364825620350",
        "id": "1168006592022833",
        "accessibilityCaption": "May be a doodle of ‎blueprint, floor plan and ‎text..."
      }
    ]
  }
]
```

---

## apify/facebook-comments-scraper — Sample output (array items)

```json
[
  {
    "postTitle": "NASA - National Aeronautics and Space Administration’s 10 new astronaut candidates were introduced Monday ...",
    "text": "Still providing passport \"stamps\"?  If so, how do we \"collect\"?",
    "likesCount": "12",
    "facebookUrl": "https://www.facebook.com/NASA/posts/pfbid0HFGX3ArQESah..."
  },
  {
    "postTitle": "NASA - National Aeronautics and Space Administration’s 10 new astronaut candidates were introduced Monday ...",
    "text": "MaryBeth Kruckow and Keri McGreal Gray you know the Amplify lesson with the video...",
    "likesCount": "8",
    "facebookUrl": "https://www.facebook.com/NASA/posts/pfbid0HFGX3ArQESah..."
  },
  {
    "postTitle": "NASA - National Aeronautics and Space Administration’s 10 new astronaut candidates were introduced Monday ...",
    "text": "Almost all of the selected people are from a branch of armed forces...",
    "likesCount": "4",
    "facebookUrl": "https://www.facebook.com/NASA/posts/pfbid0HFGX3ArQESah..."
  },
  {
    "postTitle": "NASA - National Aeronautics and Space Administration’s 10 new astronaut candidates were introduced Monday ...",
    "text": "Koyi Or prajati hai jo hamare signal ko age jane nahinde raha ho sakta hai...",
    "likesCount": "0",
    "facebookUrl": "https://www.facebook.com/NASA/posts/pfbid0HFGX3ArQESah..."
  }
]
```

---

## Input examples / schema

### scraper_one/facebook-posts-scraper (posts actor)

Required fields:

- `pageUrls` (string[]) — list of Facebook pages/groups

Optional fields:

- `resultsLimit` (number) — max number of posts per URL

Example input:

```json
{
  "resultsLimit": 3,
  "pageUrls": [
    "https://www.facebook.com/groups/1054903574928547",
    "https://www.facebook.com/tweakedmotorsports",
    "https://www.facebook.com/groups/289835267786139"
  ]
}
```

### apify/facebook-comments-scraper (comments actor)

Required fields:

- `startUrls` (array) — array of valid Facebook post URLs (objects with `url` or plain strings, see actor docs)

Optional fields:

- `resultsLimit` (integer) — max comments per URL (if omitted the actor attempts to return as many as possible)
- `includeNestedComments` (boolean) — include replies up to 3 levels
- `viewOption` (enum) — one of: `RANKED_THREADED`, `RECENT_ACTIVITY`, `RANKED_UNFILTERED` (default `RANKED_UNFILTERED`)

Example input:

```json
{
  "startUrls": [
    { "url": "https://www.facebook.com/permalink.php?story_fbid=..." }
  ],
  "resultsLimit": 50,
  "includeNestedComments": true,
  "viewOption": "RANKED_THREADED"
}
```

---

## Notes for developers

- Use the `scraper_one/facebook-posts-scraper` items to implement/verify your posts adapter (map `postId`->`post_id`, `postText`->`text`, `timestamp`->`published_at` (convert ms epoch to UTC datetime), and `reactions`/`reactionsCount` to `reactions`/`likes`).
- Use the `apify/facebook-comments-scraper` items to implement comment normalization (map `text`/`commentText` to `text`, `likesCount` to `likes_count`, and `facebookUrl` to `post_url` or `postId`).
- Prefer mocking `ApifyClient.dataset(...).iterate_items()` to return these sample JSON objects when writing unit tests.
