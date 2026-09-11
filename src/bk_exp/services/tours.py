from math import asin, cos, radians, sin, sqrt

from bk_exp.models import (
    CrossoverOffer,
    CrossoverRequest,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackType,
    PointOfInterest,
    TourCharacter,
)

POINTS_OF_INTEREST = [
    PointOfInterest(
        id="murrow-high-school",
        character=TourCharacter.BASQUIAT,
        name="Edward R. Murrow High School",
        description="Basquiat attended this Midwood public high school before his art career.",
        latitude=40.6275,
        longitude=-73.9654,
        source_url="https://www.bklynlibrary.org/blog/2020/12/22/jean-michel-basquiat",
        confidence=0.9,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="brooklyn-museum",
        character=TourCharacter.BASQUIAT,
        name="Brooklyn Museum",
        description="A major Brooklyn art institution for grounding a Basquiat-focused cultural tour.",
        latitude=40.6712,
        longitude=-73.9636,
        source_url="https://www.brooklynmuseum.org/",
        confidence=0.75,
        estimated_minutes=30,
    ),
    PointOfInterest(
        id="walt-whitman-park",
        character=TourCharacter.WHITMAN,
        name="Walt Whitman Park",
        description="Downtown Brooklyn park named for the poet and Brooklyn journalist.",
        latitude=40.6978,
        longitude=-73.9890,
        source_url="https://www.nycgovparks.org/parks/walt-whitman-park",
        confidence=0.95,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="brooklyn-heights-prom",
        character=TourCharacter.WHITMAN,
        name="Brooklyn Heights Promenade",
        description="A waterfront literary walking context near Whitman's nineteenth-century Brooklyn.",
        latitude=40.6965,
        longitude=-73.9966,
        source_url="https://www.brooklynbridgepark.org/places-to-see/pier-1/",
        confidence=0.7,
        estimated_minutes=25,
    ),
    PointOfInterest(
        id="biggie-wallace-way",
        character=TourCharacter.BIGGIE,
        name="Christopher 'Notorious B.I.G.' Wallace Way",
        description="Clinton Hill street co-named to honor Christopher Wallace.",
        latitude=40.6894,
        longitude=-73.9650,
        source_url="https://www.nyc.gov/site/dot/about/street-naming.page",
        confidence=0.9,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="barclays-center",
        character=TourCharacter.BIGGIE,
        name="Barclays Center",
        description="Brooklyn venue with a lasting relationship to the borough's hip-hop culture.",
        latitude=40.6826,
        longitude=-73.9754,
        source_url="https://www.barclayscenter.com/",
        confidence=0.7,
        estimated_minutes=30,
    ),
    PointOfInterest(
        id="james-madison-high-school",
        character=TourCharacter.RBG,
        name="James Madison High School",
        description="Brooklyn school attended by Ruth Bader Ginsburg.",
        latitude=40.6166,
        longitude=-73.9490,
        source_url="https://www.nyc.gov/site/records/historical-research/ruth-bader-ginsburg.page",
        confidence=0.9,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="brooklyn-borough-hall",
        character=TourCharacter.RBG,
        name="Brooklyn Borough Hall",
        description="Civic landmark that anchors a Brooklyn legal-history route.",
        latitude=40.6932,
        longitude=-73.9907,
        source_url="https://www.nyc.gov/site/queens/about/borough-hall.page",
        confidence=0.65,
        estimated_minutes=20,
    ),
]


class PreferenceStore:
    """In-memory demo store; production will use the configured database repository."""

    def __init__(self) -> None:
        self._weights: dict[tuple[str, TourCharacter], float] = {}

    def record(self, feedback: FeedbackRequest) -> FeedbackResponse:
        key = (feedback.session_id, feedback.character)
        current = self._weights.get(key, 0.5)
        adjustment = {
            FeedbackType.ACCEPTED: 0.15,
            FeedbackType.NOT_NOW: -0.08,
            FeedbackType.KEEP_ORIGINAL: -0.15,
        }[feedback.feedback_type]
        updated = min(1.0, max(0.0, current + adjustment))
        self._weights[key] = updated
        return FeedbackResponse(character_preference_weight=updated)

    def weight_for(self, session_id: str, character: TourCharacter) -> float:
        return self._weights.get((session_id, character), 0.5)


def distance_meters(latitude: float, longitude: float, point: PointOfInterest) -> int:
    earth_radius_meters = 6_371_000
    latitude_delta = radians(point.latitude - latitude)
    longitude_delta = radians(point.longitude - longitude)
    a = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude))
        * cos(radians(point.latitude))
        * sin(longitude_delta / 2) ** 2
    )
    return round(2 * earth_radius_meters * asin(sqrt(a)))


def crossover_offers(request: CrossoverRequest, preferences: PreferenceStore) -> list[CrossoverOffer]:
    offers: list[CrossoverOffer] = []
    for point in POINTS_OF_INTEREST:
        if point.character == request.primary_character:
            continue
        distance = distance_meters(request.latitude, request.longitude, point)
        added_minutes = max(8, round(distance / 75) + point.estimated_minutes)
        if distance > 2_000 or added_minutes > request.remaining_minutes:
            continue
        relevance = round(
            min(1.0, point.confidence * 0.6 + preferences.weight_for(request.session_id, point.character) * 0.4),
            2,
        )
        offers.append(
            CrossoverOffer(
                point=point,
                added_minutes=added_minutes,
                added_cost_usd=0,
                distance_meters=distance,
                relevance_score=relevance,
            )
        )
    return sorted(offers, key=lambda offer: offer.relevance_score, reverse=True)
