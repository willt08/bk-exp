"""CrewAI deployment entry point for BK-EXP."""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class BkExpCrew:
    """Curate evidence-backed Brooklyn cultural-tour recommendations."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
        )

    @agent
    def cultural_curator(self) -> Agent:
        return Agent(
            config=self.agents_config["cultural_curator"],
            verbose=True,
        )

    @agent
    def route_designer(self) -> Agent:
        return Agent(
            config=self.agents_config["route_designer"],
            verbose=True,
        )

    @agent
    def adaptation_evaluator(self) -> Agent:
        return Agent(
            config=self.agents_config["adaptation_evaluator"],
            verbose=True,
        )

    @task
    def verify_research(self) -> Task:
        return Task(
            config=self.tasks_config["verify_research"],
            agent=self.researcher(),
        )

    @task
    def curate_evidence(self) -> Task:
        return Task(
            config=self.tasks_config["curate_evidence"],
            agent=self.cultural_curator(),
            context=[self.verify_research()],
        )

    @task
    def design_tour(self) -> Task:
        return Task(
            config=self.tasks_config["design_tour"],
            agent=self.route_designer(),
            context=[self.curate_evidence()],
        )

    @task
    def evaluate_adaptation(self) -> Task:
        return Task(
            config=self.tasks_config["evaluate_adaptation"],
            agent=self.adaptation_evaluator(),
            context=[self.design_tour()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
