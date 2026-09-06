from pydantic import BaseModel, Field, field_validator, model_validator

from .segment import SourceLang


class Caption(BaseModel):
    """A translated caption for one segment, in one student language."""

    lesson_id: str
    seq: int = Field(ge=0)  # the Segment.seq this translates
    source_lang: SourceLang
    source_text: str  # carried through so the client can show both (ADR 0008)
    target_lang: str
    text: str
    engine: str  # which backend produced it, for the record
    latency_ms: int = Field(ge=0)
    degraded: bool = False  # true when translation failed; client shows Italian only

    @field_validator("lesson_id", "source_text", "target_lang", "engine", "text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Caption fields must not be blank")
        return v

    @model_validator(mode="after")
    def degraded_carries_source_text(self) -> "Caption":
        if self.degraded and self.text != self.source_text:
            raise ValueError(
                "a degraded Caption must carry the source text verbatim, "
                "never a partial or dropped translation (docs/operations.md)"
            )
        return self
