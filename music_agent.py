import os
import time
from autogen import AssistantAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv


load_dotenv()
llm_config = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.2
}

# --- AGENTS ---

# Agent to analyze mood and generate music-related keywords
mood_agent = AssistantAgent(
    name="mood_agent",
    llm_config=llm_config,
    system_message="""
    You are a mood interpreter. Given a user's emotional state or mood, you generate a list of descriptive keywords 
    that can be used to search for music that matches that mood. Avoid generic responses. Output only keywords 
    separated by commas.
    """
)

# Agent to generate YouTube links for songs
search_agent = AssistantAgent(
    name="search_agent",
    llm_config=llm_config,
    system_message="""
    You are a music recommendation assistant. Given a list of mood-related keywords, search the web and return
    a list of direct YouTube links to popular songs that match those keywords. Ensure that each link is on a new line
    and represents a real song on YouTube. Output only the links.
    """
)

# --- BROWSER HANDLER ---
class BrowserAgent:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)  # Keep browser open

        self.driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)

    def play_songs(self, urls):
        for url in urls:
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(1)

# --- WORKFLOW ---
def run_mood_playlist_workflow(user_mood):
    mood_keywords = mood_agent.generate_reply([
        {"role": "user", "content": user_mood}
    ]).strip()
    print("[Mood Keywords]", mood_keywords)

    song_links_response = search_agent.generate_reply([
        {"role": "user", "content": f"Suggest songs for mood: {mood_keywords}"}
    ]).strip()
    song_links = [line for line in song_links_response.splitlines() if line.startswith("http")]
    print("[YouTube Links]", song_links)

    browser = BrowserAgent()
    browser.play_songs(song_links)

# --- ENTRY POINT ---
if __name__ == "__main__":
    mood_input = input("Enter your current mood: ")
    run_mood_playlist_workflow(mood_input)
