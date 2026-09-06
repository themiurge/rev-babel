from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

SourceLang = Literal["it", "en", "mixed", "und"]


class Segment(BaseModel):
    """A transcribed segment of teacher speech, committed on a voice-activity
    pause (ADR 0005), never a partial re-decode.
    """

    lesson_id: str
    seq: int = Field(ge=0)
    started_at_ms: int = Field(ge=0)
    ended_at_ms: int
    source_lang: SourceLang
    text: str

    @field_validator("lesson_id")
    @classmethod
    def lesson_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Segment.lesson_id must not be blank")
        return v

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "Segment.text must not be blank: a committed segment always carries text"
            )
        return v

    @model_validator(mode="after")
    def ends_after_it_starts(self) -> "Segment":
        if self.ended_at_ms <= self.started_at_ms:
            raise ValueError(
                f"Segment.ended_at_ms ({self.ended_at_ms}) must be after "
                f"started_at_ms ({self.started_at_ms})"
            )
        return self
