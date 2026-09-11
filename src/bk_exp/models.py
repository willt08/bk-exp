from enum import StrEnum

from pydantic import BaseModel, Field


class TourCharacter(StrEnum):
    BASQUIAT = "basquiat"
    WHITMAN = "whitman"
    BIGGIE = "biggie"
    RBG = "rbg"


class PointOfInterest(BaseModel):
    id: str
    character: TourCharacter
    name: str
    description: str
    latitude: float
    longitude: float
    source_url: str
    confidence: float = Field(ge=0, le=1)
    estimated_minutes: int = Field(gt=0)


class TourResponse(BaseModel):
    character: TourCharacter
    primary_route: list[PointOfInterest]
    all_points: list[PointOfInterest]


class CrossoverRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    primary_character: TourCharacter
    latitude: float = Field(ge=40.4, le=40.95)
    longitude: float = Field(ge=-74.3, le=-73.65)
    remaining_minutes: int = Field(ge=1, le=720)
    remaining_budget_usd: float = Field(ge=0, le=10000)


class CrossoverOffer(BaseModel):
    point: PointOfInterest
    added_minutes: int
    added_cost_usd: float
    distance_meters: int
    relevance_score: float = Field(ge=0, le=1)
    preserves_original_route: bool = True


class CrossoverResponse(BaseModel):
    offers: list[CrossoverOffer]


class FeedbackType(StrEnum):
    ACCEPTED = "accepted"
    NOT_NOW = "not_now"
    KEEP_ORIGINAL = "keep_original"


class FeedbackRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    character: TourCharacter
    feedback_type: FeedbackType


class FeedbackResponse(BaseModel):
    character_preference_weight: float
