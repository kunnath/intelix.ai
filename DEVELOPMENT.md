# Development Guide for IntelliX.AI

This document provides guidance for developers working on the IntelliX.AI Test Case Generator project.

## Project Structure

```
.
├── backend/
│   ├── Dockerfile           # Python container configuration
│   ├── requirements.txt     # Python dependencies
│   └── app/
│       ├── __init__.py      # Python package marker
│       ├── main.py          # FastAPI application
│       └── vector_store.py  # Qdrant integration
├── frontend/
│   ├── Dockerfile           # Node.js container configuration
│   ├── index.html           # HTML entry point
│   ├── package.json         # NPM dependencies
│   ├── vite.config.js       # Vite configuration
│   └── src/
│       ├── index.css        # Global styles
│       ├── main.jsx         # React entry point
│       ├── App.jsx          # Main application component
│       └── components/      # React components
│           ├── Header.jsx   # Navigation header
│           ├── TestCaseViewer.jsx  # Test case generation UI
│           └── QdrantViewer.jsx    # Search and view UI
├── docker-compose.yml       # Container orchestration
├── .env                     # Environment variables
└── run.sh                   # Startup script
```

## Development Workflow

### Backend Development

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Activate the virtual environment:
   ```
   source ../venv/bin/activate
   ```

3. Run the FastAPI server:
   ```
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

### Frontend Development

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

4. Access the frontend:
   ```
   http://localhost:3000
   ```

### Docker Development

Run all services together:
```
docker-compose up --build
```

**Note:** The Qdrant UI is accessible directly through Qdrant's built-in web UI at `http://localhost:6333/dashboard`.

## API Endpoints

- `POST /generate-test-case` - Generate test cases from JIRA ID
- `GET /fetch-stored-case/{jira_id}` - Retrieve stored test cases
- `GET /get-test-case-csv/{jira_id}` - Download test cases as CSV
- `POST /search-test-cases` - Search for similar test cases

## Adding New Features

1. **Backend Changes**:
   - Add new endpoints in `app/main.py`
   - Update the vector store in `app/vector_store.py`
   - Add new dependencies to `requirements.txt`

2. **Frontend Changes**:
   - Create new components in `frontend/src/components/`
   - Update routing in `frontend/src/App.jsx`
   - Update API calls in the relevant components

## Troubleshooting

- **Ollama Connection Issues**: Ensure Ollama is running with `ollama serve`
- **Model Availability**: Make sure the DeepSeek-R1 8B model is available with `ollama list`
- **JIRA API Errors**: Verify your JIRA credentials in `.env`
- **Qdrant Connection**: Check Docker logs with `docker logs intellix-ai_qdrant_1`

## Future Development

- Semantic search over all test cases
- Support for editing and re-generating test cases
- Export to XRAY test management system
- Improved error handling and validation
