import asyncio
from google.genai import Client, types

from .base import Prompt
from src.llm.schema.gemini import (
    GeminiTextPrompt,
    GeminiYoutubePrompt,
    GeminiPrompt,
)
from src.llm.schema.output import StoryOutput


class GeminiTsumGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.api_key = api_key

        if self.api_key is None:
            raise ValueError(
                "API key for Gemini is not set. Please set the 'GEMINI_API_KEY' environment variable."
            )

        self.client = Client(api_key=self.api_key)

    async def generate(self, prompts: list[Prompt]) -> StoryOutput:
        messages = []
        for prompt in prompts:
            messages.append(GeminiYoutubePrompt(video_url=prompt.video_url))
            messages.append(GeminiTextPrompt(message=prompt.text))

        contents = GeminiPrompt(messages=messages)

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=types.Content(parts=contents.to_parts()),
            config={
                "response_mime_type": "application/json",
                "response_json_schema": StoryOutput.model_json_schema(),
            },
        )

        if response is None or response.text is None:
            raise ValueError("No response from Gemini API.")

        return StoryOutput.model_validate_json(response.text)

    def batch_generate(self, prompt_list: list[list[Prompt]]) -> list[StoryOutput]:
        """
        Generate summaries for multiple videos in parallel.

        Args:
            prompt_list: List of prompt lists, each for one video

        Returns:
            List of generated summaries in the same order
        """

        async def _batch_execute():
            tasks = [self.generate(prompts) for prompts in prompt_list]
            return await asyncio.gather(*tasks)

        return asyncio.run(_batch_execute())
