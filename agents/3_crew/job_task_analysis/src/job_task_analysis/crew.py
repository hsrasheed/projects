from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool


@CrewBase
class JobTaskAnalysis():
    """Job Task Analysis crew"""


    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def subject_matter_expert1(self) -> Agent:
        return Agent(
            config=self.agents_config['subject_matter_expert1'],
            verbose=True,
            tools=[SerperDevTool()],
            llm = LLM( model="azure/gpt-4.1-mini",api_version="2025-04-14")
        )

    @agent
    def subject_matter_expert2(self) -> Agent:
        return Agent(
            config=self.agents_config['subject_matter_expert2'],
            verbose=True,
            tools=[SerperDevTool()],
            llm = LLM( model="azure/gpt-4.1-nano",api_version="2025-04-14")
        )

    @agent
    def subject_matter_expert3(self) -> Agent:
        return Agent(
            config=self.agents_config['subject_matter_expert3'],
            verbose=True,
            tools=[SerperDevTool()],
            llm = LLM( model="azure/gpt-5-mini",api_version="2025-08-07")
        )

    @agent
    def facilitator(self) -> Agent:
        return Agent(
            config=self.agents_config['facilitator'],
            verbose=True,
            llm = LLM( model="azure/gpt-5-nano",api_version="2025-08-07")
        )

    @task
    def create_skilling_plan1(self) -> Task:
        return Task(
            config=self.tasks_config['create_skilling_plan1'],
        )

    @task
    def create_skilling_plan2(self) -> Task:
        return Task(
            config=self.tasks_config['create_skilling_plan2'],
        )

    @task
    def create_skilling_plan3(self) -> Task:
        return Task(
            config=self.tasks_config['create_skilling_plan3'],
        )


    @task
    def create_final_skilling_plan(self) -> Task:
        return Task(
            config=self.tasks_config['create_final_skilling_plan'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the JTA crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
