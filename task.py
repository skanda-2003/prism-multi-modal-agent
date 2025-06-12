# task.py

from agents import get_agent
from db import SessionLocal, Conversation
from typing import Dict
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_agent_query(agent_name: str, user_input: str, model_name: str, conversation_id: str) -> dict:
    session_db = SessionLocal()
    try:
        agent = get_agent(agent_name, model_name, conversation_id)
        result = agent({"input": user_input})
        response = result.get("output", result.get("text", "No response"))
        
        # Save conversation to database
        conversation = session_db.query(Conversation).filter_by(id=conversation_id).first()
        if not conversation:
            conversation = Conversation(id=conversation_id, agent_name=agent_name, model_name=model_name, chat_history="")
            session_db.add(conversation)
        conversation.chat_history += f"User: {user_input}\nAssistant: {response}\n"
        session_db.commit()
        
        return {"response": response, "reasoning": ""}
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        return {"response": f"Unexpected error occurred: {str(e)}", "reasoning": str(e)}
    finally:
        session_db.close()
    