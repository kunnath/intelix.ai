implement this project from scratch using Docker Compose, FastAPI, React, Qdrant, and Ollama (local LLM).

⸻

Project: AI-Generated Manual Test Cases from JIRA ID using FastAPI, React, Ollama, and Qdrant

Objective

Automatically generate manual test cases in XRAY format using a local LLM (e.g., via Ollama) by fetching JIRA ticket descriptions via API, storing them in Qdrant vector DB, and providing a React-based UI to generate, view, and download test cases.

⸻

System Architecture

[React UI] <--> [FastAPI Backend] <--> [JIRA API / Ollama / Qdrant]
                              |
                              --> [LLM: Generate Test Case]
                              --> [Store Test Case in Qdrant]


⸻

Features
	1.	Fetch JIRA description using JIRA ID
	2.	Generate manual test case in XRAY format using LLM (Ollama local)
	3.	Store test case + JIRA ID + description in Qdrant
	4.	View test case in UI by JIRA ID
	5.	Download test case in .csv format
	6.	Admin-friendly Qdrant Dashboard to view vector data

⸻

Tech Stack

Layer	Tech
Backend	FastAPI, Python, LangChain, Qdrant
Frontend	React + Material UI
LLM	Ollama (e.g. Mistral or LLaMA3)
Vector DB	Qdrant
Tooling	Docker Compose


⸻

Setup Instructions

✅ 1. Clone Project

git clone https://github.com/your-username/jira-testcase-gen
cd jira-testcase-gen


⸻

✅ 2. Project Structure

.
├── backend/
│   ├── main.py
│   ├── vector_store.py
│   └── requirements.txt
├── frontend/
│   └── React App (React + Material UI)
├── docker-compose.yml
└── README.md


⸻

✅ 3. Docker Compose

docker-compose.yml:

version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - qdrant
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"

  qdrant-ui:
    image: qdrant/qdrant-dashboard
    ports:
      - "3001:80"


⸻

✅ 4. Backend – FastAPI Setup

/backend/requirements.txt

fastapi
uvicorn
requests
qdrant-client
langchain
sentence-transformers
pandas

/backend/main.py
	•	Fetch JIRA description (mock or real)
	•	Generate test case using Ollama
	•	Store test case in Qdrant
	•	Provide APIs:
	•	POST /generate-test-case
	•	GET /get-test-case-csv/{jira_id}
	•	GET /fetch-stored-case/{jira_id}

/backend/vector_store.py
	•	Qdrant connection
	•	Store & retrieve payload by jira_id

⸻

✅ 5. LLM Setup – Ollama

Install and run locally:

brew install ollama
ollama run mistral  # or llama3

Ollama runs at http://localhost:11434

⸻

✅ 6. Frontend – React Setup

Use create-react-app, or Vite.

Components:
	•	TestCaseViewer.js: Enter JIRA ID, generate test case, download CSV
	•	QdrantViewer.js: View stored test case using JIRA ID

API Calls:
	•	POST /generate-test-case
	•	GET /get-test-case-csv/:jira_id
	•	GET /fetch-stored-case/:jira_id

Use axios and Material UI for UI.

⸻

✅ 7. Run the System

docker-compose up --build

	•	React: http://localhost:3000
	•	Backend: http://localhost:8000
	•	Qdrant Dashboard: http://localhost:3001
	•	Ollama: http://localhost:11434

⸻

✅ 8. Example Usage
	•	User enters JIRA ID ABC-123
	•	System fetches description from JIRA
	•	LLM generates XRAY-style test case
	•	Test case is stored in Qdrant
	•	User views and downloads .csv file from frontend

⸻

✅ 9. Future Enhancements
	•	Integrate real JIRA OAuth + API token fetch
	•	Add semantic search over all test cases
	•	Allow editing & re-generating test cases
	•	Export to XRAY test management system

⸻

✅ 10. Sample Prompt for LLM

You are a QA analyst. Based on the following JIRA ticket description, generate manual test cases in XRAY format with steps, expected result, and test ID.

JIRA Description:
{{description}}

Output format:
[
  {
    "test_id": "TC-001",
    "title": "Verify login with valid credentials",
    "steps": ["Open login page", "Enter valid credentials", "Click login"],
    "expected_result": "User is logged in"
  }
]


⸻

✅ Summary

You now have a complete AI-powered QA system with:
	•	JIRA API integration
	•	LLM-based test case generation (offline)
	•	Test case storage in Qdrant
	•	UI for generation, viewing, and CSV export

⸻
