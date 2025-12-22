from abc import ABCMeta, abstractmethod


class Prompt:
    def __init__(self, video_url: str, text: str):
        self.video_url = video_url
        self.text = text


class BaseTsumGenerator(metaclass=ABCMeta):
    @abstractmethod
    async def generate(self, prompts: list[Prompt]) -> str:
        raise NotImplementedError("Subclasses must implement the generate method.")
