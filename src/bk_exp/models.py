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
    source_title: str
    confidence: float = Field(ge=0, le=1)
    estimated_minutes: int = Field(gt=0)


class TourResponse(BaseModel):
    character: TourCharacter
    primary_route: list[PointOfInterest]
    all_points: list[PointOfInterest]


class CrewRunRequest(BaseModel):
    character: TourCharacter
    remaining_minutes: int = Field(ge=15, le=720)
    remaining_budget_usd: float = Field(ge=0, le=10000)


class ResearchCitation(BaseModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    snippet: str = Field(min_length=1)


class ResearchResponse(BaseModel):
    character: TourCharacter
    query: str
    citations: list[ResearchCitation]
    review_required: bool = True


class CrewRunResponse(BaseModel):
    kickoff_id: str = Field(min_length=1)
    research: ResearchResponse


class CrewInputsResponse(BaseModel):
    inputs: dict[str, object]


class CrewStatusResponse(BaseModel):
    kickoff_id: str
    status: str
    result: object | None = None


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
