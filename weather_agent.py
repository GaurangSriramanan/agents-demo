import autogen
import os
import json
import requests # To fetch actual weather data
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": openai_api_key,
    }
]

# --- Function for Weather Retrieval ---
def get_current_weather(location: str) -> str:
    """
    Fetches the current weather for a specified location using OpenWeatherMap API.

    Args:
        location (str): The city name (e.g., "College Park, MD", "London, UK").

    Returns:
        str: A JSON string containing the weather data, or an error message.
    """
    print(f"\n--- Function Call: get_current_weather(location='{location}') ---")

    if not weather_api_key:
        return json.dumps({"error": "Weather API key not configured."})

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    # Use Celsius for temperature units
    complete_url = base_url + "appid=" + weather_api_key + "&q=" + location + "&units=metric"

    try:
        response = requests.get(complete_url)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        weather_data = response.json()
        print(f"--- Weather API Response Code: {weather_data.get('cod')} ---")
        # Check if the API returned a valid response code (usually 200)
        if weather_data.get("cod") != 200:
             return json.dumps({"error": f"API Error: {weather_data.get('message', 'Unknown error')}", "cod": weather_data.get("cod")})
        return json.dumps(weather_data)
    except requests.exceptions.RequestException as e:
        print(f"--- Weather API Request Error: {e} ---")
        return json.dumps({"error": f"Could not connect to weather service: {e}"})
    except json.JSONDecodeError:
        print(f"--- Weather API JSON Decode Error ---")
        return json.dumps({"error": "Failed to parse weather service response."})
    except Exception as e:
        print(f"--- Unexpected Error in get_current_weather: {e} ---")
        return json.dumps({"error": f"An unexpected error occurred: {e}"})

# --- Agent Definitions ---

# Assistant Agent: The LLM-powered agent that processes information and decides actions.
assistant = autogen.AssistantAgent(
    name="Weather_Assistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.7,
         # Tell the LLM about the function it can call
        "functions": [
            {
                "name": "get_current_weather",
                "description": "Fetch the current weather for a given location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state/country (e.g., 'College Park, MD', 'Paris, France').",
                        }
                    },
                    "required": ["location"],
                },
            }
        ],
    },
    system_message="""You are a helpful weather advisor.
    1. Your primary goal is to get the current weather for the user's specified location using the available get_current_weather function.
    2. Once you have the weather data (in JSON format), analyze it carefully. Key factors are temperature, 'feels like' temperature, weather condition (rain, clouds, sun, etc.), wind speed, and humidity.
    3. Based on your analysis, recommend appropriate clothing (e.g., t-shirt, sweater, jacket, coat, shorts, pants). Be specific (e.g., "light jacket", "warm coat").
    4. Recommend necessary accessories (e.g., umbrella, sunglasses, hat, scarf, gloves).
    5. If there are any potential hazards or notable conditions (e.g., strong wind, heavy rain, high UV index - though UV isn't in basic data), mention them as cautions.
    6. Present the information clearly to the user. Start by stating the current weather conditions briefly before giving recommendations.
    7. If the weather function returns an error, inform the user that you couldn't retrieve the weather data and state the error reason if available. Do not invent weather data.
    8. Assume temperatures are in Celsius unless otherwise specified in the data. Wind speed is likely in meters/second.
    """
)

# User Proxy Agent: Represents the user, initiates the chat, and can execute functions/code.
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER", 
    max_consecutive_auto_reply=1, 
    is_termination_msg=lambda x: (x.get("content", "") or "").rstrip().endswith("TERMINATE"),
    code_execution_config=False, 
    function_map={
        "get_current_weather": get_current_weather
    }
)

# --- Initiate the Chat ---
current_location = "Washington DC, USA"
current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print(f"--- Starting Weather Agent Chat ---")
print(f"Time: {current_time_str}")
print(f"Location: {current_location}")
print("-" * 30)

user_proxy.initiate_chat(
    assistant,
    message=f"""Please get the current weather for {current_location}.
    Based on the weather conditions, tell me what clothes I should wear today and if I need any accessories like an umbrella or sunglasses.
    Also, mention any cautions I should be aware of.""",
)

print("-" * 30)
print("--- Weather Agent Chat Finished ---")
