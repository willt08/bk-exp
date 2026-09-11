from crewai import Agent, Crew, Process, Task


def build_tour_crew() -> Crew:
    researcher = Agent(
        role="Brooklyn cultural research agent",
        goal="Find current, cited public-web evidence for culturally relevant Brooklyn places.",
        backstory="You use You.com Search for discovery and retain citations for every candidate.",
        verbose=False,
    )
    curator = Agent(
        role="Clean-data cultural curator",
        goal="Normalize evidence-backed POIs and reject ambiguous or uncited claims.",
        backstory="You protect historical accuracy, provenance, and geographic data quality.",
        verbose=False,
    )
    route_designer = Agent(
        role="Accessible route designer",
        goal="Build a coherent character-led Brooklyn itinerary within time and budget constraints.",
        backstory="You preserve the visitor's primary narrative while making travel impacts explicit.",
        verbose=False,
    )
    adaptation_evaluator = Agent(
        role="Learning crossover evaluator",
        goal="Offer only useful nearby crossover opportunities and learn from explicit feedback.",
        backstory="You never replace a chosen route without the visitor's consent.",
        verbose=False,
    )

    research = Task(
        description="Research cited Brooklyn points of interest for the selected cultural figure.",
        expected_output="A list of source-attributed candidate POIs.",
        agent=researcher,
    )
    curate = Task(
        description="Validate research candidates and return clean, normalized POIs.",
        expected_output="A provenance-preserving clean POI collection.",
        agent=curator,
        context=[research],
    )
    design = Task(
        description="Design the primary walking route within the visitor's constraints.",
        expected_output="An ordered primary route with time and budget impact.",
        agent=route_designer,
        context=[curate],
    )
    evaluate = Task(
        description="Rank nearby crossovers using constraints and explicit feedback preferences.",
        expected_output="Crossover offers that retain a resumable original route.",
        agent=adaptation_evaluator,
        context=[design],
    )
    return Crew(
        agents=[researcher, curator, route_designer, adaptation_evaluator],
        tasks=[research, curate, design, evaluate],
        process=Process.sequential,
        verbose=False,
    )
