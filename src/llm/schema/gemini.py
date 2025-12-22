from typing import Union

from google.genai import types


class GeminiTextPrompt:
    def __init__(self, message: str):
        self.message = message

    def to_part(self) -> types.Part:
        return types.Part(text=self.message)


class GeminiYoutubePrompt:
    def __init__(self, video_url: str):
        self.video_url = video_url

    def to_part(self) -> types.Part:
        return types.Part(
            file_data=types.FileData(file_uri=self.video_url)
        )


class GeminiPrompt:
    def __init__(
        self,
        messages: list[Union[GeminiYoutubePrompt, GeminiTextPrompt]],
    ):
        self.messages = messages

    def to_parts(self) -> list[types.Part]:
        return [message.to_part() for message in self.messages]
