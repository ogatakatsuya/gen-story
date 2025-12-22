from pydantic import BaseModel


class Story(BaseModel):
    title: str
    message: str


class StoryOutput(BaseModel):
    stories: list[Story]
