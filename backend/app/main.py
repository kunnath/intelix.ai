import os
import json
import pandas as pd
import asyncio
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import uuid
from dotenv import load_dotenv
import base64
import logging
import traceback

from app.vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("intellix-backend")

# Load environment variables
load_dotenv()

app = FastAPI(title="IntelliX.AI Test Case Generator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store
vector_store = VectorStore()

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {
        "status": "ok", 
        "message": "Backend API is running", 
        "version": "1.0.0",
        "model_loaded": vector_store.model_is_loaded()
    }

# Models
class JiraTicket(BaseModel):
    jira_id: str
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_base_url: Optional[str] = None

class TestCase(BaseModel):
    test_id: str
    title: str
    steps: List[str]
    expected_result: str

class TestCaseResponse(BaseModel):
    jira_id: str
    description: str
    test_cases: List[TestCase]

class QueryRequest(BaseModel):
    query: str
    limit: int = 5

# Helper functions
async def fetch_jira_description(
    jira_id: str, 
    username: str = os.getenv("JIRA_USERNAME", ""), 
    api_token: str = os.getenv("JIRA_API_TOKEN", ""),
    base_url: str = os.getenv("JIRA_BASE_URL", "")
) -> str:
    """Fetch JIRA ticket description using the JIRA API."""
    if not all([username, api_token, base_url]):
        raise HTTPException(status_code=400, detail="JIRA credentials not provided")
    
    auth_header = base64.b64encode(f"{username}:{api_token}".encode()).decode()
    
    url = f"{base_url}/rest/api/2/issue/{jira_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error fetching JIRA ticket: {response.text}"
            )
        
        data = response.json()
        description = data.get("fields", {}).get("description", "No description available")
        return description

async def generate_test_cases(description: str) -> List[Dict[str, Any]]:
    """Generate test cases using Ollama."""
    ollama_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    if os.getenv("DOCKER_CONTAINER", "false").lower() == "true":
        ollama_base = "http://host.docker.internal:11434"
    
    # Get model from environment variable or use DeepSeek-R1 8B as default
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    
    # Get timeout from environment variable or use default of 120 seconds
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
    
    logger.info(f"Using Ollama base URL: {ollama_base}")
    logger.info(f"Using model: {model}")
    logger.info(f"Using timeout: {timeout} seconds")
    
    prompt = f"""You are a QA analyst. Based on the following JIRA ticket description, generate manual test cases in XRAY format with steps, expected result, and test ID.

JIRA Description:
{description}

Output format:
[
  {{
    "test_id": "TC-001",
    "title": "Verify login with valid credentials",
    "steps": ["Open login page", "Enter valid credentials", "Click login"],
    "expected_result": "User is logged in"
  }}
]

Return ONLY valid JSON without any extra text.
"""
    
    # Maximum retry attempts
    max_retries = 3
    retry_count = 0
    retry_delay = 2  # seconds
    
    while retry_count < max_retries:
        try:
            logger.info(f"Sending request to Ollama API at {ollama_base}/api/generate (attempt {retry_count + 1}/{max_retries})")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ollama_base}/api/generate",
                    json={
                        "model": model, 
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=timeout  # Use timeout from environment or default
                )
                
                logger.info(f"Ollama API response status code: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"Error generating test cases: {response.text}"
                    logger.error(error_msg)
                    
                    # If we get an actual error response (not a timeout), raise exception
                    if retry_count == max_retries - 1:  # On last retry
                        raise HTTPException(
                            status_code=500, 
                            detail=error_msg
                        )
                    # Otherwise retry
                    retry_count += 1
                    await asyncio.sleep(retry_delay * (2 ** retry_count))  # Exponential backoff
                    continue
                
                # Extract the response and parse the JSON
                try:
                    logger.info("Parsing Ollama response")
                    result = response.json()
                    response_text = result.get("response", "")
                    logger.debug(f"Raw response: {response_text[:500]}...")  # Log first 500 chars
                    
                    # Extract JSON from the response (in case there's extra text)
                    json_start = response_text.find("[")
                    json_end = response_text.rfind("]") + 1
                    
                    logger.info(f"JSON found in response: start={json_start}, end={json_end}")
                    
                    if json_start >= 0 and json_end > 0:
                        json_str = response_text[json_start:json_end]
                        logger.debug(f"Extracted JSON string: {json_str[:500]}...")  # Log first 500 chars
                        test_cases = json.loads(json_str)
                        logger.info(f"Successfully parsed {len(test_cases)} test cases")
                        return test_cases
                    else:
                        error_msg = "No valid JSON found in response"
                        logger.error(f"{error_msg}. Response text: {response_text[:500]}...")
                        raise ValueError(error_msg)
                        
                except Exception as e:
                    error_msg = f"Failed to parse LLM response: {str(e)}"
                    logger.error(f"{error_msg}. Response text: {response_text[:500]}...")
                    logger.error(traceback.format_exc())
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )
                
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            error_msg = f"Timeout error communicating with Ollama (attempt {retry_count + 1}/{max_retries}): {str(e)}"
            logger.warning(error_msg)
            
            if retry_count == max_retries - 1:  # On last retry
                logger.error(f"All {max_retries} attempts to call Ollama API failed with timeout")
                raise HTTPException(
                    status_code=500,
                    detail=f"Timeout error communicating with Ollama after {max_retries} attempts: {str(e)}"
                )
            
            retry_count += 1
            await asyncio.sleep(retry_delay * (2 ** retry_count))  # Exponential backoff
            
        except Exception as e:
            error_msg = f"Error communicating with Ollama: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )

def create_csv_file(jira_id: str, test_cases: List[Dict[str, Any]]) -> str:
    """Create a CSV file from test cases."""
    filename = f"test_cases_{jira_id}_{uuid.uuid4()}.csv"
    
    # Create a list of rows for the CSV
    rows = []
    for tc in test_cases:
        steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(tc.get("steps", []))])
        rows.append({
            "Test ID": tc.get("test_id", ""),
            "Title": tc.get("title", ""),
            "Steps": steps_str,
            "Expected Result": tc.get("expected_result", "")
        })
    
    # Create DataFrame and save as CSV
    df = pd.DataFrame(rows)
    csv_path = f"/tmp/{filename}"
    df.to_csv(csv_path, index=False)
    
    return csv_path

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "IntelliX.AI Test Case Generator API"}

@app.post("/generate-test-case", response_model=TestCaseResponse)
async def generate_test_case(ticket: JiraTicket, background_tasks: BackgroundTasks):
    """Generate test cases for a JIRA ticket and store them."""
    try:
        logger.info(f"Received request to generate test cases for JIRA ID: {ticket.jira_id}")
        
        # Use provided JIRA credentials if available, otherwise use environment variables
        username = ticket.jira_username or os.getenv("JIRA_USERNAME", "")
        api_token = ticket.jira_api_token or os.getenv("JIRA_API_TOKEN", "")
        base_url = ticket.jira_base_url or os.getenv("JIRA_BASE_URL", "")
        
        logger.info(f"Using JIRA base URL: {base_url}")
        
        # Check if we already have test cases for this JIRA ID
        logger.info(f"Checking if test cases already exist for JIRA ID: {ticket.jira_id}")
        stored_case = vector_store.retrieve_test_case(ticket.jira_id)
        if stored_case:
            logger.info(f"Found existing test cases for JIRA ID: {ticket.jira_id}")
            return TestCaseResponse(
                jira_id=ticket.jira_id,
                description=stored_case.get("description", ""),
                test_cases=stored_case.get("test_cases", [])
            )
        
        # For testing purposes, if test_user and test_token are provided, use a mock description
        is_test_request = username == "test_user" and api_token == "test_token"
        
        if is_test_request:
            logger.info("Using mock description for testing")
            description = """
            Test JIRA ticket description for IntelliX.AI
            
            As a user, I want to be able to login to the system using my credentials
            so that I can access my account and perform operations.
            
            Acceptance Criteria:
            1. User should be able to enter username and password
            2. System should validate credentials
            3. User should be redirected to dashboard on successful login
            4. Error message should be shown for invalid credentials
            5. "Forgot Password" link should be available
            """
        else:
            # Fetch JIRA description
            logger.info(f"Fetching description for JIRA ID: {ticket.jira_id}")
            description = await fetch_jira_description(
                ticket.jira_id, 
                username=username, 
                api_token=api_token, 
                base_url=base_url
            )
            logger.info(f"Successfully fetched JIRA description ({len(description)} chars)")
        
        # Generate test cases
        logger.info(f"Generating test cases for JIRA ID: {ticket.jira_id}")
        test_cases = await generate_test_cases(description)
        logger.info(f"Successfully generated {len(test_cases)} test cases")
        
        # Store in vector database (in background to improve response time)
        logger.info(f"Storing test cases in vector database for JIRA ID: {ticket.jira_id}")
        background_tasks.add_task(
            vector_store.store_test_case, 
            ticket.jira_id, 
            description, 
            test_cases
        )
        
        return TestCaseResponse(
            jira_id=ticket.jira_id,
            description=description,
            test_cases=test_cases
        )
        
    except Exception as e:
        error_msg = f"Error generating test cases: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/get-test-case-csv/{jira_id}")
async def get_test_case_csv(jira_id: str):
    """Export test cases as CSV."""
    stored_case = vector_store.retrieve_test_case(jira_id)
    
    if not stored_case:
        raise HTTPException(status_code=404, detail=f"No test cases found for JIRA ID: {jira_id}")
    
    test_cases = stored_case.get("test_cases", [])
    csv_path = create_csv_file(jira_id, test_cases)
    
    return FileResponse(
        csv_path, 
        media_type="text/csv",
        filename=f"test_cases_{jira_id}.csv"
    )

@app.get("/fetch-stored-case/{jira_id}", response_model=TestCaseResponse)
async def fetch_stored_case(jira_id: str):
    """Fetch stored test case by JIRA ID."""
    stored_case = vector_store.retrieve_test_case(jira_id)
    
    if not stored_case:
        raise HTTPException(status_code=404, detail=f"No test cases found for JIRA ID: {jira_id}")
    
    return TestCaseResponse(
        jira_id=jira_id,
        description=stored_case.get("description", ""),
        test_cases=stored_case.get("test_cases", [])
    )

@app.post("/search-test-cases")
async def search_test_cases(query: QueryRequest):
    """Search for similar test cases."""
    results = vector_store.search_similar_test_cases(query.query, query.limit)
    
    if not results:
        return {"message": "No matching test cases found", "results": []}
    
    return {"results": results}

@app.get("/test-ollama-api")
async def test_ollama_api():
    """Test Ollama API connectivity and generation."""
    ollama_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    if os.getenv("DOCKER_CONTAINER", "false").lower() == "true":
        ollama_base = "http://host.docker.internal:11434"
    
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    
    # Get timeout from environment variable or use default of 120 seconds
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
    
    logger.info("Testing version API...")
    try:
        async with httpx.AsyncClient() as client:
            version_resp = await client.get(
                f"{ollama_base}/api/version",
                timeout=30.0
            )
            version_info = version_resp.json() if version_resp.status_code == 200 else None
    except Exception as e:
        version_info = {"error": str(e)}

    logger.info("Testing generate API...")
    try:
        async with httpx.AsyncClient() as client:
            gen_resp = await client.post(
                f"{ollama_base}/api/generate",
                json={
                    "model": model,
                    "prompt": "Generate a simple test case for a login page",
                    "stream": False
                },
                timeout=timeout
            )
            if gen_resp.status_code == 200:
                generation_result = {"success": True, "status_code": gen_resp.status_code}
            else:
                generation_result = {"success": False, "status_code": gen_resp.status_code, "error": gen_resp.text}
    except Exception as e:
        generation_result = {"success": False, "error": str(e)}
    
    return {
        "version_api_check": {"success": version_info is not None, "result": version_info},
        "generate_api_check": generation_result,
        "ollama_base": ollama_base,
        "model": model,
        "timeout": timeout
    }
