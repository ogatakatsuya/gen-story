"""Streamlit app for visualizing video messages."""

import json
from pathlib import Path

import streamlit as st

# YouTubeのベースURL
YOUTUBE_BASE_URL = "https://www.youtube.com/watch?v="


def load_json_data(json_path: Path) -> list[dict]:
    """Load JSON data from file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    st.set_page_config(page_title="Video Message Viewer", layout="wide")
    st.title("📹 Video Message Viewer")

    # JSONファイルの選択
    results_dir = Path("results")
    if not results_dir.exists():
        st.error("resultsディレクトリが見つかりません")
        return

    json_files = sorted(results_dir.glob("*.json"), reverse=True)
    if not json_files:
        st.error("JSONファイルが見つかりません")
        return

    # ファイル選択
    selected_file = st.selectbox(
        "JSONファイルを選択",
        json_files,
        format_func=lambda x: x.name,
    )

    # データ読み込み
    data = load_json_data(selected_file)
    st.success(f"{len(data)} 件の動画データを読み込みました")

    # 動画選択
    video_options = [
        f"{i+1}. {item.get('title', item['video_id'])} ({item['video_id']})"
        for i, item in enumerate(data)
    ]
    selected_index = st.selectbox(
        "動画を選択",
        range(len(data)),
        format_func=lambda i: video_options[i],
    )

    if selected_index is not None:
        video_data = data[selected_index]

        # 2カラムレイアウト
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📺 動画")
            video_url = f"{YOUTUBE_BASE_URL}{video_data['video_id']}"
            st.video(video_url)

            # メタデータ
            st.subheader("📋 メタデータ")
            st.write(f"**Video ID:** {video_data['video_id']}")
            if video_data.get('title'):
                st.write(f"**Title:** {video_data['title']}")
            if video_data.get('channel'):
                st.write(f"**Channel:** {video_data['channel']}")
            if video_data.get('parent_category'):
                st.write(f"**Parent Category:** {video_data['parent_category']}")
            if video_data.get('fine_category'):
                st.write(f"**Fine Category:** {video_data['fine_category']}")

        with col2:
            st.subheader("💡 生成されたストーリー")

            # ストーリーの表示
            stories = video_data.get("stories", [])
            if stories:
                for i, story in enumerate(stories, 1):
                    with st.expander(f"ストーリー {i}: {story['title']}", expanded=True):
                        st.write(f"**タイトル:** {story['title']}")
                        st.write(f"**メッセージ:** {story['message']}")
            else:
                st.warning("ストーリーが見つかりません")

            # JSON表示
            st.subheader("📄 JSON (Raw)")
            st.json(video_data)


if __name__ == "__main__":
    main()
