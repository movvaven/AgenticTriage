import os
import json
import pandas as pd 
import csv
import re
from datetime import datetime
import time
from io import StringIO
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, List

class helpers:
    
    @staticmethod
    def load_data(file_path):
        try:
            if not os.path.exists(file_path):
                return f"Error: File not found at {os.path.abspath(file_path)}"
        
            with open(file_path, 'r') as f:
                content = f.read().strip()
            
                # Use Regex to find everything between the first [ and the last ]
                # or simply strip the markdown backticks
                if content.startswith("```json"):
                    content = content.replace("```json", "", 1)
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]

                clean_content = content.strip()

                data = json.loads(clean_content)
                return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()
        

    @staticmethod
    def log_performance_metrics(metrics_data, filename):
        """
        Appends a single row of performance data to the CSV.
        metrics_data: dict containing keys like 'tokens', 'time', 'accuracy'
        """
        file_exists = os.path.isfile(filename)
        
        # Define your headers
        headers = [
            "Timestamp", "Total_Tokens", "Prompt_Tokens", 
            "Completion_Tokens", "Execution_Time_Sec", 
            "Items_Processed", "Avg_Confidence"
        ]
        
        # Prepare the row
        row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Total_Tokens": metrics_data.get("total_tokens", 0),
            "Prompt_Tokens": metrics_data.get("prompt_tokens", 0),
            "Completion_Tokens": metrics_data.get("completion_tokens", 0),
            "Execution_Time_Sec": round(metrics_data.get("execution_time", 0), 2),
            "Items_Processed": metrics_data.get("items_count", 0),
            "Avg_Confidence": round(metrics_data.get("avg_confidence", 0), 2)
        }
        
        with open(filename, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row) 

    
    @staticmethod
    def log_task_completion(task_output):
        """
        Captures the specific agent's thoughts and results after a task ends.
        """
        filename = "output/processing_log.csv"
        file_exists = os.path.isfile(filename)
        
        # Extract data from the CrewAI TaskOutput object
        agent_name = task_output.agent
        description = task_output.description
        summary = task_output.summary
        raw_output = task_output.raw
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        headers = ["Timestamp", "Agent", "Task_Description", "Decision_Summary", "Raw_Result"]
        
        with open(filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow([timestamp, agent_name, description, summary, raw_output])            

        return None


class StreamlitRedirect:
    def __init__(self, container):
        self.container = container
        self.terminal_output = StringIO()

    def write(self, text):
        # Remove ANSI color codes that CrewAI uses (the [32m stuff)
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        self.terminal_output.write(clean_text)
        # Update the Streamlit container with the latest text
        self.container.code(self.terminal_output.getvalue())

    def flush(self):
        pass


class CSVLoggerHandler(BaseCallbackHandler):
    def __init__(self, filename: str = "output/processing_log.csv", **kwargs: Any):
        super().__init__(**kwargs)
        self.filename = filename
        # Initialize the CSV with headers if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Agent", "Action", "Action Input", "Thought"])

    def on_agent_action(self, action, **kwargs):
        """This runs every time an agent decides to use a tool or take a step."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        agent_name = kwargs.get("name", "Unknown Agent")
        
        # 'action.log' contains the "Thought" process from the LLM
        thought = action.log.split("Action:")[0].replace("Thought:", "").strip()
        
        with open(self.filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                agent_name,
                action.tool,
                action.tool_input,
                thought
            ])        


class OutputMetadata(BaseModel):
    """Specific technical environment details."""
    device: Optional[str] = Field(None, description="The hardware device used by the user.")
    os: Optional[str] = Field(None, description="The operating system version.")
    app_version: Optional[str] = Field(None, description="The version of the application.")


class CSVReaderOutput(BaseModel):
    """Model for the initial data ingestion from CSV sources."""
    feedback_id: str = Field(..., description="UUID or incremental unique identifier.")
    source_id: str = Field(..., description="Original ID from the source (review_id/email_id).")
    source_type: Literal["email", "app_store"] = Field(..., description="The origin of the data.")
    
    # Rating can be null for emails, so we use Optional[int]
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating from 1 to 5.")
    
    # Priority might be pre-set in some files or inferred later
    priority: Optional[Literal["High", "Medium", "Low"]] = Field(None)
    
    user: str = Field(..., description="Username or sender email address.")
    subject: str = Field(..., description="The subject line or brief summary of the feedback.")
    text: str = Field(..., description="The full, raw text content of the feedback.")
    
    # Using a string format as requested, but you can also use 'datetime' type
    timestamp: str = Field(..., description="ISO-8601 formatted date/time.")
    
    metadata: OutputMetadata



class FeedbackClassifierOutput(BaseModel):
    """The structured output for a classified feedback entry."""
    feedback_id: str = Field(..., description="Unique identifier for the feedback.")
    source_id: str = Field(..., description="ID from the original data source (email/review).")
    source_type: str = Field(..., description="Type of source (e.g., App Store, Email).")
    
    # Literal forces the AI to choose only from these specific strings
    category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"] = Field(
        ..., description="The type of feedback detected."
    )
    priority: Literal["Critical", "High", "Medium", "Low"] = Field(
        ..., description="The urgency level based on impact."
    )
    
    technical_details: str = Field(..., description="Detailed technical breakdown of the issue.")
    suggested_title: str = Field(..., description="A concise headline for a support ticket.")
    confidence: float = Field(..., description="The AI's confidence score (0.0 to 1.0).")
    
    # This nests the metadata class inside the main class
    metadata: OutputMetadata
           

class BugAnalysisOutput(BaseModel):
    """Detailed technical analysis for identified software bugs."""
    feedback_id: str = Field(
        ..., 
        description="The unique identifier passed from the feedback_classifier_task."
    )
    steps_to_reproduce: List[str] = Field(
        ..., 
        description="A bulleted list of actions required to trigger the bug."
    )
    expected_behavior: str = Field(
        ..., 
        description="Description of what the software should have done."
    )
    actual_behavior: str = Field(
        ..., 
        description="Description of the error or incorrect behavior that occurred."
    )
    device: Optional[str] = Field(
        "Unknown", 
        description="Hardware/Device model extracted from the feedback or metadata."
    )
    os: Optional[str] = Field(
        "Unknown", 
        description="Operating system and version information."
    )
    error_message: Optional[str] = Field(
        None, 
        description="Specific error codes or text strings displayed to the user."
    )
    severity: Literal["Critical", "High", "Medium", "Low"] = Field(
        ..., 
        description="The impact level of the bug on the system's core functionality."
    )
    technical_summary: str = Field(
        ..., 
        description="A deep-dive summary for developers, including suspected root causes."
    )


class FeatureExtractorOutput(BaseModel):
    """Structured data for identifying and evaluating user feature requests."""
    feedback_id: str = Field(
        ..., 
        description="The unique identifier linked back to the original feedback classification."
    )
    feature_request: str = Field(
        ..., 
        description="A clear, concise description of the functionality the user is asking for."
    )
    use_case: str = Field(
        ..., 
        description="The specific problem the user is trying to solve or the benefit this feature provides."
    )
    estimated_impact: Literal["High", "Medium", "Low"] = Field(
        ..., 
        description="The potential value this feature brings to the user base or business."
    )
    user_segment: str = Field(
        ..., 
        description="The type of user requesting this (e.g., Power User, New User, Enterprise)."
    )
    app_version: Optional[str] = Field(
        "Unknown", 
        description="The version of the app the user was using when making the request."
    )
    similar_requests: List[str] = Field(
        default_factory=list, 
        description="A list of feedback_ids from other entries that requested something similar."
    )


class TicketCreatorOutput(BaseModel):
    """The final consolidated output for support or engineering ticketing systems."""
    ticket_id: str = Field(..., description="Unique ticket identifier generated by the system.")
    feedback_id: str = Field(..., description="The original feedback ID used for cross-referencing.")
    
    category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"] = Field(
        ..., description="Final confirmed category of the feedback."
    )
    priority: Literal["High", "Medium", "Low"] = Field(
        ..., description="Assigned priority based on analysis of the impact."
    )
    
    summary: str = Field(..., description="A concise, high-level headline for the ticket.")
    details: str = Field(..., description="The comprehensive body/description of the ticket.")
    
    # These fields are conditional based on the category
    steps_to_reproduce: Optional[str] = Field(
        None, description="Technical steps to recreate the issue (for Bugs)."
    )
    use_case: Optional[str] = Field(
        None, description="The intended value or scenario (for Feature Requests)."
    )
    
    device: Optional[str] = Field("Unknown", description="User hardware information.")
    os: Optional[str] = Field("Unknown", description="Operating system version.")
    
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO-8601 timestamp of ticket creation."
    )
    source: str = Field(..., description="The original source (e.g., App Store Review #123).")


class QualityCriticOutput(BaseModel):
    """Quality assurance evaluation for a generated support ticket."""
    ticket_id: str = Field(
        ..., 
        description="The unique identifier for the ticket being reviewed."
    )
    status: Literal["Approved", "Needs Revision"] = Field(
        ..., 
        description="The final verdict after checking for accuracy and completeness."
    )
    issues_found: List[str] = Field(
        default_factory=list, 
        description="A list of specific discrepancies, hallucinations, or missing data found."
    )
    suggested_fixes: List[str] = Field(
        default_factory=list, 
        description="Specific instructions for the Ticket Creator to fix the identified issues."
    )

class CSVReaderOutputList(BaseModel):
    """The Collection class for CSVReaderModel as output for the CSV reader task."""
    entries: List[CSVReaderOutput] = Field(
        ..., 
        description="A list containing all the feedbacks, frm both reviews and emails, processed in this batch."
    )

class FeedbackClassifierOutputList(BaseModel):
    """The Collection class for FeedbackClassifierModel as output for the feedback classifier task."""
    entries: List[FeedbackClassifierOutput] = Field(
        ..., 
        description="A list containing all the features classified in this batch."
    )

class BugAnalysisOutputList(BaseModel):
    """The Collection class for BugAnalysisModel as output for the bug analysis task."""
    entries: List[BugAnalysisOutput] = Field(
        ..., 
        description="A list containing all the bugs processed in this batch."
    )

class FeatureExtractorOutputList(BaseModel):
    """The Collection class for FeatureExtractorModel as output for the feature extractor task."""
    entries: List[FeatureExtractorOutput] = Field(
        ..., 
        description="A list containing all the features extracted in this batch."
    )

class TicketCreatorOutputList(BaseModel):
    """The Collection class for TicketCreatorModel as output for the ticket creator task."""
    entries: List[TicketCreatorOutput] = Field(
        ..., 
        description="A list containing all the individual tickets created in this batch."
    )

class QualityCriticOutputList(BaseModel):
    """The Collection class for QualityCriticModel as output for the quality critic task."""
    entries: List[QualityCriticOutput] = Field(
        ..., 
        description="A list containing all the quality control objects processed in this batch."
    )                        