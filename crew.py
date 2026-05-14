import os
import pandas as pd
from typing import Any, Dict, List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai.agents.agent_builder.base_agent import BaseAgent
from feedbackmanagement.helpers import BugAnalysisOutputList, CSVReaderOutputList, FeedbackClassifierOutputList, helpers, FeatureExtractorOutputList, QualityCriticOutputList, TicketCreatorOutputList


@tool("review_tool")
def review_tool(file_path: str):
    """Reads all records from the app store reviews CSV file."""
    
    # This helps debug if the file actually exists where you think it is
    if not os.path.exists(file_path):
        return f"Error: File not found at {os.path.abspath(file_path)}"

    df = pd.read_csv(file_path)
    return df.to_string()
    
@tool("email_tool")
def email_tool(file_path: str):
    """Reads all records from the customer emails CSV file."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {os.path.abspath(file_path)}"
    df = pd.read_csv(file_path)
    return df.to_string()


@CrewBase
class feedbackmanagement():
    """Feedbackmanagement crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/agents.yaml'    
    tasks_config = 'config/tasks.yaml'
    

    @agent
    def csv_reader(self) -> Agent:
        print("DEBUG: Available Agents in YAML: {self.agents_config.keys() } ")
        return Agent(
            config=self.agents_config['csv_reader'], # type: ignore[index]
            tools=[review_tool, email_tool],
            verbose=True
        )

    @agent
    def feedback_classifier(self) -> Agent:
        return Agent(
            config=self.agents_config['feedback_classifier'], # type: ignore[index]
            verbose=True
        )
    
    @agent
    def bug_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['bug_analyst'], # type: ignore[index]
            verbose=True
        )
    
    @agent
    def feature_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['feature_extractor'], # type: ignore[index]
            verbose=True
        )
    
    @agent
    def ticket_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['ticket_creator'], # type: ignore[index]
            verbose=True
        )   
    
    @agent
    def quality_critic(self) -> Agent:
        return Agent(
            config=self.agents_config['quality_critic'], # type: ignore[index]
            verbose=True
        )
    

    @task
    def csv_reader_task(self) -> Task:
        # print(f"DEBUG: Available Tasks in YAML: {self.tasks_config.keys() } ")
        return Task(
            config=self.tasks_config['csv_reader_task'], # type: ignore[index]
            # callback=helpers.log_task_completion,
        )

    @task
    def feedback_classifier_task(self) -> Task:
        return Task(
            config=self.tasks_config['feedback_classifier_task'], # type: ignore[index]
            # callback=helpers.log_task_completion,
        )

    @task
    def bug_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['bug_analysis_task'], # type: ignore[index]
            # callback=helpers.log_task_completion,
        )

    @task
    def feature_extractor_task(self) -> Task:
        return Task(
            config=self.tasks_config['feature_extractor_task'], # type: ignore[index]
            # callback=helpers.log_task_completion,
        )

    @task
    def ticket_creator_task(self) -> Task:
        return Task(
            config=self.tasks_config['ticket_creator_task'], # type: ignore[index]
            # callback=helpers.log_task_completion,
        )

    @task
    def quality_critic_task(self) -> Task:
        return Task(
            config=self.tasks_config['quality_critic_task'], # type: ignore[index]
            # callback=helpers.log_task_completion,
        )
    
  
    @crew
    def crew(self) -> Crew:
        """Creates the Feedback Management crew"""
        print("DEBUG: Building Crew with agents and tasks")
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
            output_log_file='crew_log.txt'
        )

