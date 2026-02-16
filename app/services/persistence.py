"""
Data Persistence Service
========================

Handles saving and loading data to/from files (JSON, CSV).
"""

import os
import json
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import glob


class DataPersistenceService:
    """
    Service for persisting social media data to files.

    Handles both raw JSON storage and processed CSV exports.
    """

    def __init__(self, base_dir: str = "data"):
        """
        Initialize persistence service.

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.processed_dir = os.path.join(base_dir, "processed")

        # Ensure directories exist
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    def save_dataset(
        self, raw_data: List[Dict], normalized_data: List[Dict], platform: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Save raw and normalized data to files.

        Args:
            raw_data: Raw data from Apify
            normalized_data: Normalized/processed data
            platform: Platform name (Facebook, Instagram, YouTube)

        Returns:
            Tuple of (json_path, csv_path, comments_csv_path)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform_lower = platform.lower()

        # Save raw JSON
        json_path = self._save_raw_json(raw_data, platform_lower, timestamp)

        # Save processed CSV
        csv_path = self._save_processed_csv(normalized_data, platform_lower, timestamp)

        # Save comments CSV
        comments_path = self._save_comments_csv(normalized_data, platform_lower, timestamp)

        return json_path, csv_path, comments_path

    def _save_raw_json(self, raw_data: List[Dict], platform: str, timestamp: str) -> str:
        """Save raw JSON data."""
        filename = os.path.join(self.raw_dir, f"{platform}_{timestamp}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)

        return filename

    def _save_processed_csv(
        self, normalized_data: List[Dict], platform: str, timestamp: str
    ) -> str:
        """Save processed data as CSV."""
        filename = os.path.join(self.processed_dir, f"{platform}_{timestamp}.csv")

        # Prepare data for CSV
        csv_data = []
        for post in normalized_data:
            # Copy all fields
            csv_row = dict(post)

            # Convert complex fields to JSON strings
            if "reactions" in csv_row and isinstance(csv_row["reactions"], dict):
                csv_row["reactions"] = json.dumps(csv_row["reactions"], ensure_ascii=False)

            if "comments_list" in csv_row and isinstance(csv_row["comments_list"], list):
                csv_row["comments_list"] = json.dumps(csv_row["comments_list"], ensure_ascii=False)

            if "hashtags" in csv_row and isinstance(csv_row["hashtags"], list):
                csv_row["hashtags"] = json.dumps(csv_row["hashtags"], ensure_ascii=False)

            if "mentions" in csv_row and isinstance(csv_row["mentions"], list):
                csv_row["mentions"] = json.dumps(csv_row["mentions"], ensure_ascii=False)

            if "attachments" in csv_row and isinstance(csv_row["attachments"], list):
                csv_row["attachments"] = json.dumps(csv_row["attachments"], ensure_ascii=False)

            if "author" in csv_row and isinstance(csv_row["author"], dict):
                csv_row["author"] = json.dumps(csv_row["author"], ensure_ascii=False)

            csv_data.append(csv_row)

        # Save to CSV
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False, encoding="utf-8")

        return filename

    def _save_comments_csv(
        self, normalized_data: List[Dict], platform: str, timestamp: str
    ) -> Optional[str]:
        """Extract and save comments as separate CSV."""
        comments_data = []

        for post in normalized_data:
            post_id = post.get("post_id", "")
            comments_list = post.get("comments_list", [])

            if isinstance(comments_list, list):
                for comment in comments_list:
                    if isinstance(comment, dict):
                        comment_row = {
                            "post_id": post_id,
                            "comment_id": comment.get("comment_id", ""),
                            "text": comment.get("text", ""),
                            "author_name": comment.get("author_name", ""),
                            "created_time": comment.get("created_time", ""),
                            "likes_count": comment.get("likes_count", 0),
                        }
                        comments_data.append(comment_row)
                    elif isinstance(comment, str):
                        # Simple string comment
                        comments_data.append(
                            {
                                "post_id": post_id,
                                "comment_id": "",
                                "text": comment,
                                "author_name": "",
                                "created_time": "",
                                "likes_count": 0,
                            }
                        )

        # Only save if we have comments
        if not comments_data:
            return None

        filename = os.path.join(self.processed_dir, f"{platform}_comments_{timestamp}.csv")
        df = pd.DataFrame(comments_data)
        df.to_csv(filename, index=False, encoding="utf-8")

        return filename

    def load_dataset(self, file_path: str) -> Optional[List[Dict]]:
        """
        Load data from a saved file (JSON or CSV).

        Args:
            file_path: Path to the file

        Returns:
            List of normalized data
        """
        if not os.path.exists(file_path):
            return None

        try:
            if file_path.endswith(".json"):
                return self._load_json(file_path)
            elif file_path.endswith(".csv"):
                return self._load_csv(file_path)
            else:
                return None
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

    def _load_json(self, file_path: str) -> List[Dict]:
        """Load JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_csv(self, file_path: str) -> List[Dict]:
        """Load CSV file and parse JSON fields."""
        df = pd.read_csv(file_path)
        posts = df.to_dict("records")

        # Parse JSON fields
        for post in posts:
            # Parse reactions
            if "reactions" in post and isinstance(post["reactions"], str):
                try:
                    post["reactions"] = json.loads(post["reactions"])
                except:
                    post["reactions"] = {}

            # Parse comments_list
            if "comments_list" in post and isinstance(post["comments_list"], str):
                try:
                    post["comments_list"] = json.loads(post["comments_list"])
                except:
                    post["comments_list"] = []

            # Parse hashtags
            if "hashtags" in post and isinstance(post["hashtags"], str):
                try:
                    post["hashtags"] = json.loads(post["hashtags"])
                except:
                    post["hashtags"] = []

            # Parse mentions
            if "mentions" in post and isinstance(post["mentions"], str):
                try:
                    post["mentions"] = json.loads(post["mentions"])
                except:
                    post["mentions"] = []

            # Parse attachments
            if "attachments" in post and isinstance(post["attachments"], str):
                try:
                    post["attachments"] = json.loads(post["attachments"])
                except:
                    post["attachments"] = []

            # Parse author
            if "author" in post and isinstance(post["author"], str):
                try:
                    post["author"] = json.loads(post["author"])
                except:
                    post["author"] = {}

            # Convert published_at to datetime
            if "published_at" in post:
                try:
                    post["published_at"] = pd.to_datetime(post["published_at"])
                except:
                    pass

        return posts

    def get_saved_files(self) -> Dict[str, List[str]]:
        """
        Get lists of saved files by platform.

        Returns:
            Dict mapping platform to list of file paths
        """
        platforms = {
            "Facebook": glob.glob(os.path.join(self.processed_dir, "facebook_*.csv")),
            "Instagram": glob.glob(os.path.join(self.processed_dir, "instagram_*.csv")),
            "YouTube": glob.glob(os.path.join(self.processed_dir, "youtube_*.csv")),
        }

        # Filter out comment files
        for platform in platforms:
            platforms[platform] = [
                f for f in platforms[platform] if "comments" not in os.path.basename(f)
            ]
            # Sort by modification time (newest first)
            platforms[platform].sort(key=os.path.getmtime, reverse=True)

        return platforms

    def get_latest_file(self, platform: str) -> Optional[str]:
        """
        Get the most recent file for a platform.

        Args:
            platform: Platform name

        Returns:
            Path to latest file, or None
        """
        files = self.get_saved_files()
        platform_files = files.get(platform, [])

        return platform_files[0] if platform_files else None
