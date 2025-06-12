# tools.py

import os
import requests
from langchain.agents import Tool
from db import engine, SessionLocal, Note
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables for API Keys
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

def search_ingredients(query: str) -> str:
    params = {
        "engine": "google",
        "q": f"Ingredients for {query}",
        "api_key": SERPAPI_API_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"SerpAPI Error: {e}")
        return "• Unable to connect to SerpAPI."
    
    ingredients_list = []
    if "organic_results" in data:
        for res in data["organic_results"]:
            snippet = res.get("snippet", "")
            if "ingredients" in snippet.lower():
                ingredients_list.append(f"• {snippet}")
    if not ingredients_list:
        return "No specific ingredients found."
    return "Suggested ingredients:\n" + "\n".join(ingredients_list)

def search_youtube_videos(query: str) -> str:
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": 1   # Fetch top 3 relevant videos
    }
    try:
        response = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"YouTube API Error: {e}")
        return "• Unable to connect to YouTube Data API."
    
    video_links = extract_video_links(data)
    if video_links:
        return "\n".join(video_links)
    else:
        return "No video found."

def extract_video_links(data: dict) -> list:
    """
    Extracts YouTube video links from the API response.

    Args:
        data (dict): The JSON response from the YouTube Data API.

    Returns:
        list: A list of YouTube video URLs.
    """
    video_links = []
    if "items" in data:
        for item in data["items"]:
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_links.append(video_url)
    return video_links

def search_news(query: str) -> str:
    url = "https://newsapi.org/v2/top-headlines"
    params = {"apiKey": NEWS_API_KEY, "q": query, "country": "india", "pageSize": 5}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"News API Error: {e}")
        return "• Unable to connect to News API."
    
    if "articles" in data and data["articles"]:
        return "Latest news:\n" + "\n".join("• " + a["title"] for a in data["articles"] if a.get("title"))
    return "No relevant news found."

def search_weather(location: str) -> str:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": WEATHER_API_KEY, "units": "metric"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Weather API Error: {e}")
        return "• Unable to connect to Weather API."
    
    if data.get("weather"):
        desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        return f"Weather in {location}:\n• {desc}\n• Temp: {temp}°C"
    return "No weather info found."

def create_note_tool(note_name: str, content: str, location: str) -> str:
    known_locations = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents")
    }
    if location not in known_locations:
        return "Invalid location. Use 'desktop' or 'documents'."
    path = os.path.join(known_locations[location], f"{note_name}.txt")
    session_db = SessionLocal()
    try:
        existing_note = session_db.query(Note).filter_by(name=note_name, location=location).first()
        if existing_note:
            return f"Note '{note_name}' already exists in {location}."
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        new_note = Note(name=note_name, content=content, location=location)
        session_db.add(new_note)
        session_db.commit()
        return f"Note '{note_name}' created successfully in {location}."
    except Exception as e:
        session_db.rollback()
        logger.error(f"Create Note Error: {e}")
        return f"Failed to create note: {e}"
    finally:
        session_db.close()

def update_note_tool(note_name: str, content: str, location: str) -> str:
    known_locations = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents")
    }
    if location not in known_locations:
        return "Invalid location. Use 'desktop' or 'documents'."
    path = os.path.join(known_locations[location], f"{note_name}.txt")
    session_db = SessionLocal()
    try:
        note = session_db.query(Note).filter_by(name=note_name, location=location).first()
        if not note:
            return f"Note '{note_name}' does not exist in {location}."
        with open(path, 'a', encoding='utf-8') as f:
            f.write("\n" + content)
        note.content += "\n" + content
        session_db.commit()
        return f"Note '{note_name}' updated successfully in {location}."
    except Exception as e:
        session_db.rollback()
        logger.error(f"Update Note Error: {e}")
        return f"Failed to update note: {e}"
    finally:
        session_db.close()

def delete_note_tool(note_name: str, location: str) -> str:
    known_locations = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents")
    }
    if location not in known_locations:
        return "Invalid location. Use 'desktop' or 'documents'."
    path = os.path.join(known_locations[location], f"{note_name}.txt")
    session_db = SessionLocal()
    try:
        note = session_db.query(Note).filter_by(name=note_name, location=location).first()
        if not note:
            return f"Note '{note_name}' does not exist in {location}."
        if os.path.exists(path):
            os.remove(path)
        session_db.delete(note)
        session_db.commit()
        return f"Note '{note_name}' deleted successfully from {location}."
    except Exception as e:
        session_db.rollback()
        logger.error(f"Delete Note Error: {e}")
        return f"Failed to delete note: {e}"
    finally:
        session_db.close()

def show_note_tool(note_name: str, location: str) -> str:
    known_locations = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents")
    }
    if location not in known_locations:
        return "Invalid location. Use 'desktop' or 'documents'."
    path = os.path.join(known_locations[location], f"{note_name}.txt")
    session_db = SessionLocal()
    try:
        note = session_db.query(Note).filter_by(name=note_name, location=location).first()
        if not note:
            return f"Note '{note_name}' does not exist in {location}."
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"Note '{note_name}' in {location}:\n{content}"
        return "Note file not found."
    except Exception as e:
        logger.error(f"Show Note Error: {e}")
        return f"Failed to read note: {e}"
    finally:
        session_db.close()

# Define Tools
search_ingredients_tool = Tool(
    name="search_ingredients",
    func=search_ingredients,
    description="Find ingredients for a given dish."
)

search_youtube_tool = Tool(
    name="search_youtube_videos",
    func=search_youtube_videos,
    description="Find relevant YouTube videos."
)

search_news_tool = Tool(
    name="search_news_tool",
    func=search_news,
    description="Find the latest news on a topic."
)

search_weather_tool = Tool(
    name="search_weather_tool",
    func=search_weather,
    description="Fetch weather information for a location."
)

create_note = Tool(
    name="create_note",
    func=create_note_tool,
    description="Creates a new note with the given name, content, and location. Location can be 'desktop' or 'documents'."
)

update_note = Tool(
    name="update_note",
    func=update_note_tool,
    description="Updates an existing note with the given name by appending the provided content. Location can be 'desktop' or 'documents'."
)

delete_note = Tool(
    name="delete_note",
    func=delete_note_tool,
    description="Deletes the note with the given name from the specified location. Location can be 'desktop' or 'documents'."
)

show_note = Tool(
    name="show_note",
    func=show_note_tool,
    description="Displays the content of the note with the given name from the specified location. Location can be 'desktop' or 'documents'."
)
