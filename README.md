# Agentic Triage System with Crew AI

Author - Venkat Movva

Overview
This is a Triage Management System that is designed to take over the manual triaging process by reading user feedback from csv files containing app store reviews and support 
emails. The system uses AI to automatically classify content into categories (Bug / Feature Request / Praise / Complaint / Spam),  extracts actionable insights and technical details and creates structured tickets and logs them to CSV files with appropriate priority. The system self checks its classification and also provides a user interface for monitoring and manual overriding the generated tickets.

Scenario
As a product engineer at a B2C mobile app company that manages a productivity app with around 10,000 active users. The team currently receives: 
• 10-20 app store reviews daily 
• 5-10 customer support emails per day 
• Occasional in-app feedback submissions 
A team member manually reads through this feedback and creates tickets in your project management system. This process takes 1-2 hours daily and often results in: 
• Delayed response to critical bugs 
• Inconsistent ticket formatting and prioritization 
• Lost or overlooked feedback 
• Poor traceability from user complaint to engineering resolution 

Problem Statement
Modern SaaS and app-based companies receive dozens of user reviews and feedback daily from multiple channels including app stores (Google Play, App Store), customer support emails, and user surveys. The current manual triaging process is slow, inconsistent, and doesn't scale effectively resulting in critical bugs being missed, feature requests being delayed, and inconsistent prioritization across teams. 

Approach:-
Design, implement, and demonstrate a complete multi-agent AI system that: 
- Reads user feedback from CSV files containing app store reviews and support emails 
- Classifies content into categories (Bug / Feature Request / Praise / Complaint / Spam) 
- Extracts actionable insights and technical details 
- Creates structured tickets and logs them to CSV files with appropriate priority levels and metadata 
- Ensures quality and consistency through automated review 
- Provides a user interface for monitoring and manual overrides 


Project Structure
- main.py: Main application code for the Feedback Management System. 
- crew.py: Defines all the crew tools, agents and thier tasks
- helpers.py: For modularity, to keep all the helper functions.
- requirements.txt: List of dependencies required to run the application.
- config folder: Has Agents yaml and Tasks yaml files for thier configurations
- output folder: To save the JSON files writted by each Agent. It also has metrics and processing_log files
- data folder: Has the app store review and support email csv files
- venv/: Virtual environment directory (e.g., env for storing installed packages).

Setup Instructions:-
Create a Virtual Environment:
- Navigate to the project directory.
- Run: python -m venv venv (or env if preferred).
- Activate the virtual environment:
- Windows: venv\Scripts\activate
- macOS/Linux: source venv/bin/activate


Install Dependencies:
- Ensure requirements.txt is in the project directory.
- Run: pip install -r requirements.txt

Run the Application Locally:
- Run: streamlit run app.py
- Open the provided URL (e.g., http://localhost:8501) in your browser to access the app.
- Give Open API key in the left nav bar of streamlit UI

Deploying on Streamlit Cloud:-

Prepare Your Project:
- Ensure app.py, doc_processor.py, requirements.txt, and .env are in the project directory.
- Create a Streamlit Cloud account at https://streamlit.io/cloud.

Upload to Streamlit Cloud:
- Log in to Streamlit Cloud.
- Create a new app and connect it to your project directory (e.g., upload the files manually or link to a cloud storage service).
- Specify app.py as the main script.

Configure Environment Variables:
- In Streamlit Cloud, go to your app’s settings.
- Add the GOOGLE_API_KEY as a secret environment variable (do not include .env in the uploaded files for security).

Deploy the App:
- vClick “Deploy” in Streamlit Cloud.
- Once deployed, access the app via the provided URL (e.g., https://your-app-name.streamlit.app).

Test the Deployed App:
- Input job requirements, upload a resume, and analyze it.
- Verify that the analysis report is generated and downloadable.

Requirements
The requirements.txt file includes all necessary dependencies.

Usage
- Run the app locally or access the deployed version on Streamlit Cloud.
- Make sure you have created 2 csv files with data in it, app_store_reviews.csv and customer_emails.csv.
- Click “Start Analysis” to read the data from the above mentoned csv files and generate tickets automatically with AI-driven analysis.
- You can then navigate to different options available to see the details
- Dashboard: Gives overview of processed feedback and generated tickets 
- Manual Override:  Lets you edit or approve generated tickets
- Configuration Panel: Lets you adjust classification thresholds and priorities
- Analytics: Showes processing statistics and performance metrics 


## 🚀 Features
- Reads csv files files to generate tickets automatically with AI-driven analysis.
- Dashboard: Overview of processed feedback and generated tickets 
- Manual Override:  Edit or approve generated tickets
- Configuration Panel: Adjust classification thresholds and priorities
- Analytics: Processing statistics and performance metrics 

---

## 📦 Tech Stack

- **CrewAI** for buiding a complete multi-agent AI system
- **Streamlit** for the frontend web interface
- **Open AI** for LLM to provide reasoning
- **Pandas** for displaying and editing data in data grids
- **dotenv** for API key and environment config

---

## 🛠️ Setup Instructions
````

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API key**
   Create a `.env` file in the project root and add:

   ```
   GOOGLE_API_KEY=your_google_api_key
   ```

4. **Run the app**

   ```bash
   streamlit run app.py
   ```

---

## 📄 File Structure

```plaintext
├── main.py                 # Main Streamlit app
├── crew.py                 # Defines all the crew tools, agents and thier tasks
├── helpers.py              # For keeping all the helper functions.
├── config/                 # Folder for Agents yaml and Tasks yaml files
├── data/                   # Folder for app_store_reviews and customer_emails csv files.
├── output/                 # Folder to store ouput JSON files written by each Agent.
├── .env                    # Contains API key (not committed)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```


## 📈 Example Output

```
Structured Analysis:
- Strengths: Speeding up of triaging a large number of customer feedback items with in no time, and creating tickets respectively
- Weaknesses: May some time hallucinate information regarding tickets, So we will need a manual override

```

---

## 🧑‍💼 Ideal For

* Companies that care about customer feedback and quickly want to address their concerns
* Feedback Management Application, Triage tool
* Good use of crew agents that take tasks and start off working on completing them.

```

