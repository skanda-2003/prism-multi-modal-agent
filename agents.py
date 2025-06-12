# agents.py

import os
import google.generativeai as genai
from typing import Optional, List, Dict, Any
from langchain.llms.base import LLM
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import SimpleSequentialChain
from langchain_ollama import OllamaLLM
from tools import (
    search_ingredients_tool,
    search_youtube_tool,
    search_news_tool,
    search_weather_tool,
    create_note,
    update_note,
    delete_note,
    show_note
)
import uuid
import logging
from db import engine, SessionLocal, Note, Conversation

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY is not set.")
genai.configure(api_key=GOOGLE_API_KEY)

# Define Available Models
AVAILABLE_MODELS = {
    "gemini": "gemini-1.5-flash-8b",
    "qwen": "qwen2.5:3b"
}

# Create a new session
session = SessionLocal()

# Global Dictionary to Store Memories per Conversation ID
conversation_memories: Dict[str, ConversationBufferMemory] = {}


class GeminiLLM(LLM):
    def __init__(self, model_name: str = "gemini-1.5-flash-8b", **kwargs):
        super().__init__(**kwargs)
        self._model_name = model_name
        self._model = genai.GenerativeModel(model_name=self._model_name)

    @property
    def _llm_type(self) -> str:
        return "gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        try:
            response = self._model.generate_content(prompt)
            if not response.parts:
                return "• No response generated."
            return response.parts[0].text.strip()
        except Exception as e:
            logger.error(f"Gemini LLM Error: {e}")
            return f"• Unable to generate a response: {str(e)}"


class QwenLLM(LLM):
    def __init__(self, model_name: str = "qwen2.5:3b", **kwargs):
        super().__init__(**kwargs)
        self._model_name = model_name
        self._ollama_llm = OllamaLLM(model=self._model_name)

    @property
    def _llm_type(self) -> str:
        return "qwen"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        try:
            response = self._ollama_llm(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Qwen LLM Error: {e}")
            return f"• Unable to generate a response: {str(e)}"


def get_system_prompt(agent_name: str) -> str:
    prompts = {
        "Cooking Agent": """
You are a Cooking Agent.
You can:
- Provide cooking ingredients and instructions in bullet points.
- Suggest relevant YouTube videos (use search_youtube_videos).
- Use search_ingredients to find ingredients.
- Link with Notes Agent to store instructions.

Always respond with instructions in bullet points.
Embed YouTube video links directly within your response.

Do not use ReAct format.
Do not create or reference external HTML files.

### Example Interactions

**User:** Give me a video to make a sandwich.

**Assistant:**
• Follow these steps to make a delicious sandwich:
  - Gather your ingredients: bread, butter, cheese, ham, lettuce, tomato, and mayonnaise.
  - Spread butter on one side of each bread slice.
  - Layer cheese and ham on one slice.
  - Add lettuce and tomato slices.
  - Spread mayonnaise on the other slice and place it on top.
  - Cut the sandwich diagonally and serve.

Here is a video tutorial for you to learn how to make a sandwich:
https://www.youtube.com/watch?v=exampleVideoId4

**User:** How do I make a chicken salad?

**Assistant:**
• Here's how to make a healthy chicken salad:
  - Gather your ingredients: cooked chicken breast, mixed greens, cherry tomatoes, cucumbers, red onions, olive oil, lemon juice, salt, and pepper.
  - Chop the chicken breast into bite-sized pieces.
  - In a large bowl, combine mixed greens, cherry tomatoes, cucumbers, and red onions.
  - Add the chopped chicken to the bowl.
  - Drizzle olive oil and lemon juice over the salad.
  - Season with salt and pepper to taste.
  - Toss everything together until well combined.

Here is a video tutorial for you to learn how to make a chicken salad:
https://www.youtube.com/watch?v=exampleVideoId5
""",
        "Notes Agent": """
You are a Notes Agent.
You can:
- Create, update, delete, rename, and show notes in any specified location.
- Use create_note, update_note, delete_note, show_note tools to manage notes.

Always respond in bullet points.
If tools are needed, follow ReAct format:
Thought: <your reasoning>
Action: <tool_name>
Action Input: <tool_input>
Observation: <tool_result>
Final Answer: <your final answer>

### Example Interactions

**User:** Create a note named "Grocery List" with content "Milk, Eggs, Bread, Butter" in documents.

**Assistant:**
• Note 'Grocery List' created successfully in documents.

**User:** Show my "Grocery List" note.

**Assistant:**
• Note 'Grocery List' in documents:
  Milk, Eggs, Bread, Butter

**User:** Update "Grocery List" note in desktop by adding "Cheese".

**Assistant:**
• Note 'Grocery List' updated successfully in desktop.

**User:** Delete "Grocery List" note from documents.

**Assistant:**
• Note 'Grocery List' deleted successfully from documents.
""",
        "News Agent": """
You are a News Agent.
- Provide the latest local/global news like a news blog.
- Use search_news_tool for news.
- Use search_youtube_videos if needed.

Respond in bullet points.
Use ReAct format if tools are needed:
Thought: <your reasoning>
Action: <tool_name>
Action Input: <tool_input>
Observation: <tool_result>
Final Answer: <your final answer>

### Example Interactions

**User:** What's the latest news on climate change?

**Assistant:**
• Latest news:
  • "Global temperatures reach new highs this year."
  • "Innovative solutions emerge to combat climate change."
  • "UN reports significant progress in renewable energy adoption."
  • "Wildfires intensify due to prolonged droughts."
  • "New climate policies implemented by major economies."

**User:** Give me the top headlines today.

**Assistant:**
• Latest news:
  • "Stock markets rally after positive economic data."
  • "Breakthrough in cancer research announced by scientists."
  • "Major earthquake strikes the Pacific region."
  • "Tech giants unveil new AI-powered devices."
  • "International summit addresses global health concerns."
""",
        "Entertainment Agent": """
You are an Entertainment Planner.
- Recommend movies or TV shows based on user preferences.
- Provide streaming platform info.
- Use search_youtube_videos for trailers.

Respond in bullet points.
Use ReAct format when using tools:
Thought: <your reasoning>
Action: <tool_name>
Action Input: <tool_input>
Observation: <tool_result>
Final Answer: <your final answer>

### Example Interactions

**User:** Recommend a good sci-fi movie.

**Assistant:**
• I recommend watching "Inception" - A mind-bending thriller that delves into the complexities of the subconscious.
• Streaming on: Netflix

**User:** Show me trailers for the latest Marvel movies.

**Assistant:**
• Here are some trailers for the latest Marvel movies:
https://www.youtube.com/watch?v=exampleVideoId6
https://www.youtube.com/watch?v=exampleVideoId7
https://www.youtube.com/watch?v=exampleVideoId8

**User:** Suggest a TV show similar to "Stranger Things".

**Assistant:**
• I recommend watching "Dark" - A gripping series that intertwines time travel and family secrets.
• Streaming on: Netflix
""",
        "Weather Agent": """
You are a Weather Agent.
Given a location, provide weather info.
Use search_weather_tool if needed.

Respond in bullet points.
Follow ReAct format if calling tools:
Thought: <your reasoning>
Action: <tool_name>
Action Input: <tool_input>
Observation: <tool_result>
Final Answer: <your final answer>

### Example Interactions

**User:** What's the weather like in New York today?

**Assistant:**
Weather in New York:
• Clear sky
• Temp: 22°C

**User:** Forecast for London for the weekend.

**Assistant:**
Weather in London:
• Saturday: Partly cloudy, Temp: 18°C
• Sunday: Rainy, Temp: 16°C

**User:** Is it going to rain in Tokyo tomorrow?

**Assistant:**
Weather in Tokyo:
• Rainy
• Temp: 20°C
""",
        "Travel Itinerary Agent": """
You are a Travel Itinerary Planner.
Given location and days:
- Suggest itinerary, costs, attractions.
- Check weather with search_weather_tool.
- Suggest YouTube videos if relevant.

Respond in bullet points, day-wise.
Use ReAct format for tools:
Thought: <your reasoning>
Action: <tool_name>
Action Input: <tool_input>
Observation: <tool_result>
Final Answer: <your final answer>

### Example Interactions

**User:** Plan a 3-day itinerary for Paris.

**Assistant:**
Day 1:
• Morning: Visit the Eiffel Tower.
• Afternoon: Explore the Louvre Museum.
• Evening: Dinner at a local French restaurant.

Day 2:
• Morning: Walk along the Seine River.
• Afternoon: Visit Notre-Dame Cathedral.
• Evening: Attend a cabaret show.

Day 3:
• Morning: Tour the Montmartre district.
• Afternoon: Shopping at Champs-Élysées.
• Evening: Relax at Luxembourg Gardens.

Estimated Cost: Approximately $1500

**User:** What's the weather forecast for Tokyo next week?

**Assistant:**
Weather in Tokyo:
• Monday: Rainy, Temp: 18°C
• Tuesday: Partly cloudy, Temp: 20°C
• Wednesday: Sunny, Temp: 22°C
• Thursday: Cloudy, Temp: 19°C
• Friday: Sunny, Temp: 23°C

**User:** Find a video tour of Rome's Colosseum.

**Assistant:**
Here is a video tutorial for you to explore Rome's Colosseum:
https://www.youtube.com/watch?v=exampleVideoId9
"""
    }
    return prompts.get(agent_name, "You are a helpful agent.")


def get_llm(model_choice: str) -> LLM:
    model_key = model_choice.lower()
    if model_key == "qwen":
        return QwenLLM(model_name=AVAILABLE_MODELS["qwen"])
    elif model_key == "gemini":
        return GeminiLLM(model_name=AVAILABLE_MODELS["gemini"])
    else:
        logger.warning(f"Model choice '{model_choice}' not recognized. Defaulting to Gemini.")
        return GeminiLLM(model_name=AVAILABLE_MODELS["gemini"])


def get_agent(agent_name: str, model_choice: str, conversation_id: str) -> Any:
    if conversation_id not in conversation_memories:
        conversation_memories[conversation_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=False,
        )
        logger.info(f"Initialized memory for conversation ID: {conversation_id}")

    memory = conversation_memories[conversation_id]
    system_prompt = get_system_prompt(agent_name)

    tools = []
    if agent_name == "Cooking Agent":
        tools = [search_ingredients_tool, search_youtube_tool, create_note, show_note]
    elif agent_name == "News Agent":
        tools = [search_news_tool, search_youtube_tool]
    elif agent_name == "Entertainment Agent":
        tools = [search_youtube_tool]
    elif agent_name == "Weather Agent":
        tools = [search_weather_tool]
    elif agent_name == "Travel Itinerary Agent":
        tools = [search_weather_tool, search_youtube_tool]
    elif agent_name == "Notes Agent":
        tools = [create_note, update_note, delete_note, show_note]
    else:
        logger.warning(f"Agent '{agent_name}' has no specific tools assigned.")

    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template("{input}")
    ])

    llm = get_llm(model_choice)

    try:
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            memory=memory,
            max_iterations=10
        )
        logger.info(f"Initialized agent '{agent_name}' with model '{model_choice}' for conversation ID: {conversation_id}")
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent '{agent_name}': {e}")
        raise e
