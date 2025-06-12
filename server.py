# server.py

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from task import run_agent_query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

app = FastAPI()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow CORS from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update if frontend is hosted elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")
    user_input: str = Field(..., description="User's input query")
    model_name: str = Field(..., description="Name of the model to use")
    conversation_id: str = Field(..., description="Unique identifier for the conversation")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

@app.post("/query")
def query_agent(request: QueryRequest):
    try:
        result = run_agent_query(
            agent_name=request.agent_name,
            user_input=request.user_input,
            model_name=request.model_name,
            conversation_id=request.conversation_id
        )
        return {"response": result["response"], "reasoning": result["reasoning"]}
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
