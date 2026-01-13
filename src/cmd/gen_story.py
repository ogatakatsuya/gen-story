"""Generate meaningful messages for videos using Gemini API."""

import asyncio
import csv
import json
import time
from pathlib import Path

from src.llm.schema.output import StoryOutput
from src.llm.base import Prompt
from src.llm.gemini import GeminiTsumGenerator
from src.util.env import env

# YouTubeのベースURL
YOUTUBE_BASE_URL = "https://www.youtube.com/watch?v="

# メッセージ生成用のプロンプト
MESSAGE_PROMPT = """
この動画の内容を視聴した上で、この動画を編集してストーリーとして伝えることができる、意味のあるメッセージや教訓を考えてください。
音声は考慮せずに、動画の映像情報のみを基にしてください。

例えば:
- 視聴者に伝えたい重要なポイント
- 動画から学べる教訓やインサイト
- 動画の本質的なメッセージ

3-5つ程度、それぞれタイトル（短く簡潔に）と詳細なメッセージ（1-2文程度）のペアで、日本語で答えてください。
"""

# レートリミット対策: リクエスト間の待機時間（秒）
SLEEP_SECONDS = 2


def load_video_ids_from_csv(csv_path: Path) -> list[dict[str, str]]:
    """
    Load video IDs and metadata from CSV file.
    Only video_id is required, other fields are optional.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of dictionaries containing video metadata
    """
    video_data = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("video_id"):
                continue  # Skip rows without video_id

            video_data.append(
                {
                    "video_id": row["video_id"],
                    "title": row.get("title", ""),
                    "channel": row.get("channel", ""),
                    "parent_category": row.get("parent_category", ""),
                    "fine_category": row.get("fine_category", ""),
                }
            )
    return video_data


def save_results_to_json(results: list[dict], output_json: Path) -> None:
    """
    Save results to JSON file.

    Args:
        results: List of result dictionaries
        output_json: Path to output JSON file
    """
    print(f"\nSaving results to {output_json}...")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Done! Results saved to {output_json}")


async def generate_messages_sequentially(
    summarizer: GeminiTsumGenerator,
    video_data: list[dict[str, str]],
    sleep_seconds: float = 2.0,
) -> list[StoryOutput]:
    """
    Generate messages for videos one by one with delays to avoid rate limits.

    Args:
        summarizer: GeminiTsumGenerator instance
        video_data: List of video metadata dictionaries
        sleep_seconds: Seconds to wait between requests

    Returns:
        List of generated messages
    """
    messages = []
    total = len(video_data)

    for i, video in enumerate(video_data, 1):
        video_id = video["video_id"]
        video_url = f"{YOUTUBE_BASE_URL}{video_id}"

        print(f"\n[{i}/{total}] Processing video: {video_id}")
        print(f"  Title: {video['title']}")

        try:
            # Create prompt for this video
            prompts = [
                Prompt(
                    video_url=video_url,
                    text=MESSAGE_PROMPT,
                )
            ]

            # Generate message
            message = await summarizer.generate(prompts)
            messages.append(message)

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            messages.append(error_msg)
            print(f"  Error: {e}")

        # Wait before next request (except for the last one)
        if i < total:
            print(f"  Waiting {sleep_seconds} seconds before next request...")
            time.sleep(sleep_seconds)

    return messages


def main():
    # Setup paths
    csv_path = Path(
        "/home/ogata-katsuya/Study/VideoSum/Code/gen_story/data/lv-travel-short.csv"
    )
    # Use CSV filename (without extension) for JSON output
    csv_filename = csv_path.stem
    output_json = Path(f"results/{csv_filename}.json")

    # Create output directory
    output_json.parent.mkdir(parents=True, exist_ok=True)

    # Load video data
    print(f"Loading video data from {csv_path}...")
    video_data = load_video_ids_from_csv(csv_path)
    print(f"Loaded {len(video_data)} videos")

    # Initialize Gemini generator
    summarizer = GeminiTsumGenerator(api_key=env.GEMINI_API_KEY)

    # Generate messages sequentially with rate limiting
    print(
        f"\nGenerating messages for {len(video_data)} videos (one by one with {SLEEP_SECONDS}s delay)..."
    )
    messages = asyncio.run(
        generate_messages_sequentially(summarizer, video_data, SLEEP_SECONDS)
    )

    # Combine results
    results = []
    for video, message in zip(video_data, messages):
        if isinstance(message, StoryOutput):
            stories_data = [
                {"title": story.title, "message": story.message}
                for story in message.stories
            ]
        else:
            stories_data = [{"title": "Error", "message": str(message)}]

        result = {"video_id": video["video_id"], "stories": stories_data}

        # Add optional fields only if they exist and are not empty
        if video.get("title"):
            result["title"] = video["title"]
        if video.get("channel"):
            result["channel"] = video["channel"]
        if video.get("parent_category"):
            result["parent_category"] = video["parent_category"]
        if video.get("fine_category"):
            result["fine_category"] = video["fine_category"]

        results.append(result)

    # Save to JSON
    save_results_to_json(results, output_json)


if __name__ == "__main__":
    main()
