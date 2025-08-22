from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage


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
            allow_delegation=True
        )

    @agent
    def subject_matter_expert2(self) -> Agent:
        return Agent(
            config=self.agents_config['subject_matter_expert2'],
            verbose=True,
            tools=[SerperDevTool()],
            allow_delegation=True
        )

    @agent
    def subject_matter_expert3(self) -> Agent:
        return Agent(
            config=self.agents_config['subject_matter_expert3'],
            verbose=True,
            tools=[SerperDevTool()],
            allow_delegation=True
        )

    @agent
    def facilitator(self) -> Agent:
        return Agent(
            config=self.agents_config['facilitator'],
            verbose=True,
            allow_delegation=True
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
            context=[self.create_skilling_plan1(),self.create_skilling_plan2(),self.create_skilling_plan3()]
        )




    @crew
    def crew(self) -> Crew:
        """Creates the JTA crew"""
        
        manager = Agent(
            config=self.agents_config['manager'],
            memory=True
        )

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            manager_agent = manager,
            memory=True,
            verbose=True,
        )
