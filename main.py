import sys
import warnings
import os
import sys
import re
import json
import csv
from io import StringIO
import streamlit as st
from datetime import datetime
import time
import pandas as pd
from feedbackmanagement import helpers
from feedbackmanagement.crew import feedbackmanagement
from feedbackmanagement.helpers import helpers, CSVLoggerHandler, StreamlitRedirect

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)


# --- 1. ALWAYS INITIALIZE FIRST ---
if "config_settings" not in st.session_state:
    st.session_state.config_settings = {
        "confidence_threshold": 0.70,
        "priority_levels": ["Low", "Medium", "High", "Urgent"],
        "urgent_keywords": ["security", "crash", "payment", "bug"]
    }


# Page Configuration
st.set_page_config(page_title="AI - User Feedback Analysis and Action System", layout="wide")
st.title("📊 Customer Feedback AI Agent")
st.markdown("Analyze 50+ reviews and 50+ emails using Crew AI agents.")

# tab_dashboard, tab_review, tab_analytics, tab_run = 
# st.tabs(["🚀 Dashboard", "🛠️ Manual Override & Tickets Review", "📈 Analytics & System Performance", "⚙️ Run Agents"])

st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Option:", ["Run Agents", "Dashboard", "Manual Override", "Configuration Panel", "Analytics"])


# DASHBOARD SECTION
if page == "Dashboard":
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

    # Load your CrewAI outputs
    df_feedback = helpers.load_data("output/feedback_classifier.json")
    df_tickets = helpers.load_data("output/ticket_creator.json")
    df_final_tickets = helpers.load_data("output/generated_tickets.json")


    st.subheader("🚀 Dashboard") 
    if st.button("🔄 Refresh Data.. after you approve the tickets", type="primary"):
        st.rerun()
    with st.expander("Feedback & Ticket Dashboard", expanded=True):

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Feedback", len(df_feedback))
        with col2:
            st.metric("Tickets Generated", len(df_tickets))
        with col3:
            # Calculate conversion rate or high-priority count
            high_priority = (df_tickets['priority'].str.lower() == 'high').sum() if isinstance(df_tickets, pd.DataFrame) and 'priority' in df_tickets.columns else 0
            st.metric("Urgent Tickets", high_priority, delta_color="inverse")
        with col4:
            st.metric("Approved Tickets", len(df_final_tickets) if not df_final_tickets.empty else 0)



        st.subheader("Analysis Overview")
        c1, c2 = st.columns(2)

        with c1:
            st.write("**Feedback Categories**")
            if not df_feedback.empty:
                category_counts = df_feedback['category'].value_counts()
                st.bar_chart(category_counts)

        with c2:
            st.write("**Sentiment Trend**")
            if not df_tickets.empty:
                # Assuming sentiment is a score from -1 to 1
                st.line_chart(df_tickets['category'].value_counts())
                

        st.subheader("🎫 Generated Tickets")
        search = st.text_input("Search tickets by keyword...")

        if not df_tickets.empty:
            # Filter data based on search
            filtered_df = df_tickets[df_tickets.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
            st.dataframe(
                filtered_df,
                column_config={
                    "status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Closed"]),
                    "ticket_url": st.column_config.LinkColumn("Reference")
                },
                hide_index=True
            )



# MANUAL OVERIDE SECTION
if page == "Manual Override":
    def load_drafts(file_path):
        try:
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
        except:
            return pd.DataFrame(columns=["approved", "ticket_id", "feedback_id", "category", "priority", "summary","details","steps_to_reproduce", "use_case", "device", "os", "created_at", "source"])

    st.subheader("🛠️ Manual Ticket Review & Override")

    # 1. Load the drafts generated by your Crew
    df_drafts = load_drafts("output/ticket_creator.json")

    if not df_drafts.empty:
        # 2. Add an 'approved' column if it doesn't exist
        if 'approved' not in df_drafts.columns:
            df_drafts['approved'] = False

        st.info("Edit Priority and check 'Approve?' to finalize the ticket.\n Once done, click 'Push Approved Tickets' to save the final list. Click on the column to sort the tickets based on that column. You can also search for specific tickets using the search bar above the table.")

        # 3. The Data Editor (The Magic Component)
        # This allows you to edit text, change priority, and toggle checkboxes
        edited_df = st.data_editor(
            df_drafts,
            column_order=["approved", "ticket_id", "feedback_id", "category", "priority", "summary","details","steps_to_reproduce", "use_case", "device", "os", "created_at", "source"],
            column_config={
                "approved": st.column_config.CheckboxColumn("Approve?", default=False),
                "priority": st.column_config.SelectboxColumn(
                    "Priority", options=["Low", "Medium", "High", "Urgent"]
                ),
                "details": st.column_config.TextColumn("Ticket Content", width="large")
            },
            disabled=["ticket_id", "feedback_id", "category", "summary", "details", "steps_to_reproduce", "use_case", "device", "os", "created_at", "source"], # Prevent editing these columns
            hide_index=True,
            key="ticket_editor"
        )

        # 4. Save the Override
        if st.button("🚀 Push Approved Tickets"):
            # Filter for only the ones you checked
            final_tickets = edited_df[edited_df['approved'] == True]
            
            if not final_tickets.empty:
                # Save to a final file
                final_data = final_tickets.to_dict(orient='records')
                with open('output/generated_tickets.json', 'w') as f:
                    json.dump(final_data, f, indent=4)
                
                st.success(f"Successfully finalized {len(final_data)} tickets!")
            else:
                st.warning("No tickets were marked as approved.")
    else:
        st.write("No draft tickets found. Run the Crew first!")



# ANALYTICS SECTION
if page == "Analytics":
    def load_feedbackdata(file_path):
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
        
    df_feedback = load_feedbackdata("output/feedback_classifier.json")
    df_tickets =  load_feedbackdata("output/ticket_creator.json")
    if 'metrics' not in st.session_state:
        st.session_state.metrics = None

    if 'execution_time' not in st.session_state:
        st.session_state.execution_time = 0

    if 'df_feedback' not in st.session_state:
        st.session_state.df_feedback = None


    def show_analytics():
        st.subheader("📈 System Performance")

        if st.session_state.metrics is None:
                st.warning("📊 No data to show yet. Please run the process first!")
                return

        metrics = st.session_state.metrics
        
        # 1. Top Level KPIs
        m1, m2, m3 = st.columns(3)
        
        with m1:
            # Total tokens consumed across the whole run
            total_tokens = metrics.total_tokens if hasattr(metrics, 'total_tokens') else 0
            st.metric("Total Tokens", f"{total_tokens:,}", "API Usage")
            
        with m2:
            # Speed metric
            avg_speed = st.session_state.execution_time / len(df_feedback) if not df_feedback.empty else 0
            st.metric("Avg Speed", f"{avg_speed:.2f}s / item")
            
        with m3:
            # Success Rate (Feedback vs Tickets)
            success_rate = (len(df_tickets) / len(df_feedback)) * 100 if not df_feedback.empty else 0
            st.metric("Ticket Conversion", f"{success_rate:.1f}%")

        # 2. Token Breakdown Chart
        st.subheader("Token Allocation")
        usage_data = pd.DataFrame({
            "Type": ["Input", "Output"],
            "Tokens": [metrics.prompt_tokens, metrics.completion_tokens]
        })
        st.bar_chart(usage_data, x="Type", y="Tokens")

    show_analytics()

    st.subheader("AI Certainty Distribution")
    if 'confidence' in df_feedback.columns:
        # Use a histogram to see where the agent struggles
        st.bar_chart(df_feedback['confidence'].value_counts())
    

        confidence_val = st.session_state.config_settings["confidence_threshold"]
        print(confidence_val)
        low_confidence = df_feedback[df_feedback['confidence'] < confidence_val]
        if not low_confidence.empty:
            st.warning(f"⚠️ {len(low_confidence)} items require manual review due to low AI confidence.")


# Configuration for Crew Agents and Tasks
if page == "Configuration Panel":
# --- INITIALIZE CONFIGURATION ---
    if 'config_settings' not in st.session_state:
        st.session_state.config_settings = {
            "confidence_threshold": 0.70,
            "priority_levels": ["Low", "Medium", "High", "Urgent"]
        }
    conf_val = st.session_state.config_settings["confidence_threshold"]
    st.subheader("⚙️ Agent Configuration")
    
    # Adjust Confidence Threshold
    st.session_state.config_settings["confidence_threshold"] = st.slider(
        "AI Confidence Threshold", 
        min_value=0.0, max_value=1.0, value=conf_val, step=0.05,
        help="If AI certainty is below this, tickets are marked for manual review."
    )

    # Adjust Priority Keywords
    st.session_state.config_settings["priority_levels"] = st.multiselect(
        "Priority Levels",
        options=["Low", "Medium", "High", "Urgent"],
        default=st.session_state.config_settings["priority_levels"]
    )



# Run Agents Section
if page == "Run Agents":
    
    # Sidebar for Configuration
    with st.sidebar:
        st.header("Settings")
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.info("Your key is used only for this session and is not stored.")

    if st.button("Start Analysis", type="primary"):
        if not openai_api_key:
            st.error("Please enter your OpenAI API Key in the sidebar to proceed.")
        else:
            with st.expander("Showing Trace...", expanded=True):
                # place holder for terminal logs
                terminal_container = st.empty()
                # Redirect stdout to streamlit
                old_stdout = sys.stdout
                sys.stdout = StreamlitRedirect(terminal_container)

            try:
                # Setting API key
                os.environ["OPENAI_API_KEY"] = openai_api_key
                
                with st.status("🤖 Crew Agents are working...", expanded=True) as status:
                    inputs = {
                        "app_store_reviews": "data/app_store_reviews.csv",
                        "support_emails":  "data/customer_emails.csv",
                        "threshold": st.session_state.config_settings["confidence_threshold"],
                        "keywords": ", ".join(st.session_state.config_settings["urgent_keywords"])
                    }

                    start_time = time.time()  # Start the clock
                    start_perf_time = time.perf_counter()

                    crew_instance = feedbackmanagement().crew()
                    result = crew_instance.kickoff(inputs=inputs)

                    end_time = time.time()
                    end_perf_time = time.perf_counter()
                    duration = (end_perf_time - start_perf_time)/100  # Convert to seconds

                    # Reload feedback data after crew execution
                    df_feedback = helpers.load_data("output/feedback_classifier.json")
                    avg_conf = df_feedback['confidence'].mean() if isinstance(df_feedback, pd.DataFrame) and 'confidence' in df_feedback.columns else 0

                    # Capture the raw metrics from the Crew run
                    st.session_state.metrics = crew_instance.usage_metrics
                    st.session_state.execution_time = end_time - start_time  # Total time in seconds

                    run_metrics = {
                        "total_tokens": crew_instance.usage_metrics.total_tokens if crew_instance.usage_metrics else 0,
                        "prompt_tokens": crew_instance.usage_metrics.prompt_tokens if crew_instance.usage_metrics else 0,
                        "completion_tokens": crew_instance.usage_metrics.completion_tokens if crew_instance.usage_metrics else 0,
                        "execution_time": duration,
                        "items_count": len(df_feedback),
                        "avg_confidence": avg_conf
                    }

                    helpers.log_performance_metrics(run_metrics, "output/metrics.csv")
                    
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)


                st.subheader("Final Analysis Results")
                # Handle both streaming and non-streaming outputs
                if hasattr(result, 'raw'):
                    # Non-streaming: direct access
                    output_text = result
                else:
                    output_text = str(result)
                st.markdown(output_text)
                
                st.write("Generated CSV files can be found in the 'output' directory for online analysis.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.status("Error..Please check", state="error", expanded=True)
                st.write("Agents stopped. Please fix the error and try again.")

            finally:
                # Reset stdout
                sys.stdout = old_stdout 



# def run():
#     """
#     Run the Feedback Management Crew.
#     """
#     inputs = {
#         "app_store_reviews": "data/app_store_reviews.csv",
#         "support_emails":  "data/support_emails.csv",
#     }

#     try:
#         result = feedbackmanagement().crew().kickoff(inputs=inputs)
#         print(result.raw) 
#     except Exception as e:
#         raise Exception(f"An error occurred while running the crew: {e}")




# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         'current_year': str(datetime.now().year)
#     }
#     try:
#         Feedbackmanagement().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         Feedbackmanagement().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         "current_year": str(datetime.now().year)
#     }

#     try:
#         Feedbackmanagement().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")

# def run_with_trigger():
#     """
#     Run the crew with trigger payload.
#     """
#     import json

#     if len(sys.argv) < 2:
#         raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

#     try:
#         trigger_payload = json.loads(sys.argv[1])
#     except json.JSONDecodeError:
#         raise Exception("Invalid JSON payload provided as argument")

#     inputs = {
#         "crewai_trigger_payload": trigger_payload,
#         "topic": "",
#         "current_year": ""
#     }

#     try:
#         result = Feedbackmanagement().crew().kickoff(inputs=inputs)
#         return result
#     except Exception as e:
#         raise Exception(f"An error occurred while running the crew with trigger: {e}")
