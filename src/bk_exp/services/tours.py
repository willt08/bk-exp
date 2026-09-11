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
        source_url="https://en.wikipedia.org/wiki/Jean-Michel_Basquiat",
        source_title="Jean-Michel Basquiat biography",
        confidence=0.9,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="brooklyn-museum",
        character=TourCharacter.BASQUIAT,
        name="Brooklyn Museum",
        description="A major Brooklyn art institution that anchors the borough's contemporary-art context.",
        latitude=40.6712,
        longitude=-73.9636,
        source_url="https://en.wikipedia.org/wiki/Brooklyn_Museum",
        source_title="Brooklyn Museum overview",
        confidence=0.75,
        estimated_minutes=30,
    ),
    PointOfInterest(
        id="brooklyn-bridge-park",
        character=TourCharacter.BASQUIAT,
        name="Brooklyn Bridge Park",
        description="Waterfront setting for a reflective contemporary-art pause before continuing the tour.",
        latitude=40.7025,
        longitude=-73.9967,
        source_url="https://en.wikipedia.org/wiki/Brooklyn_Bridge_Park",
        source_title="Brooklyn Bridge Park overview",
        confidence=0.65,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="walt-whitman-park",
        character=TourCharacter.WHITMAN,
        name="Walt Whitman Park",
        description="Downtown Brooklyn park named for the poet and Brooklyn journalist.",
        latitude=40.6978,
        longitude=-73.9890,
        source_url="https://en.wikipedia.org/wiki/Walt_Whitman_Park",
        source_title="Walt Whitman Park overview",
        confidence=0.95,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="brooklyn-heights-prom",
        character=TourCharacter.WHITMAN,
        name="Brooklyn Heights Promenade",
        description="A waterfront stop that situates Whitman's nineteenth-century Brooklyn near the harbor.",
        latitude=40.6965,
        longitude=-73.9966,
        source_url="https://en.wikipedia.org/wiki/Brooklyn_Heights_Promenade",
        source_title="Brooklyn Heights Promenade overview",
        confidence=0.7,
        estimated_minutes=25,
    ),
    PointOfInterest(
        id="brooklyn-historical-society",
        character=TourCharacter.WHITMAN,
        name="Center for Brooklyn History",
        description="Brooklyn history collections offer context for Whitman's career as a local editor and writer.",
        latitude=40.6885,
        longitude=-73.9900,
        source_url="https://en.wikipedia.org/wiki/Center_for_Brooklyn_History",
        source_title="Center for Brooklyn History overview",
        confidence=0.75,
        estimated_minutes=25,
    ),
    PointOfInterest(
        id="biggie-wallace-way",
        character=TourCharacter.BIGGIE,
        name="Christopher 'Notorious B.I.G.' Wallace Way",
        description="Clinton Hill street co-named to honor Christopher Wallace.",
        latitude=40.6894,
        longitude=-73.9650,
        source_url="https://en.wikipedia.org/wiki/The_Notorious_B.I.G.",
        source_title="The Notorious B.I.G. biography",
        confidence=0.9,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="barclays-center",
        character=TourCharacter.BIGGIE,
        name="Barclays Center",
        description="Brooklyn venue that provides a contemporary setting for the borough's hip-hop legacy.",
        latitude=40.6826,
        longitude=-73.9754,
        source_url="https://en.wikipedia.org/wiki/Barclays_Center",
        source_title="Barclays Center overview",
        confidence=0.7,
        estimated_minutes=30,
    ),
    PointOfInterest(
        id="biggie-mural",
        character=TourCharacter.BIGGIE,
        name="Bedford-Stuyvesant hip-hop mural district",
        description="A self-guided visual-culture stop near the neighborhoods central to Brooklyn hip-hop history.",
        latitude=40.6879,
        longitude=-73.9545,
        source_url="https://en.wikipedia.org/wiki/Bedford%E2%80%93Stuyvesant,_Brooklyn",
        source_title="Bedford-Stuyvesant overview",
        confidence=0.65,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="james-madison-high-school",
        character=TourCharacter.RBG,
        name="James Madison High School",
        description="Brooklyn school attended by Ruth Bader Ginsburg.",
        latitude=40.6166,
        longitude=-73.9490,
        source_url="https://en.wikipedia.org/wiki/Ruth_Bader_Ginsburg",
        source_title="Ruth Bader Ginsburg biography",
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
        source_url="https://en.wikipedia.org/wiki/Brooklyn_Borough_Hall",
        source_title="Brooklyn Borough Hall overview",
        confidence=0.65,
        estimated_minutes=20,
    ),
    PointOfInterest(
        id="brooklyn-law-school",
        character=TourCharacter.RBG,
        name="Brooklyn Law School",
        description="A legal-education stop that frames Ginsburg's legacy in Brooklyn's civic and legal landscape.",
        latitude=40.6885,
        longitude=-73.9806,
        source_url="https://en.wikipedia.org/wiki/Brooklyn_Law_School",
        source_title="Brooklyn Law School overview",
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
