import sys
import os
import json

# 🌟 FIX: Force Python to look at the project root directory for 'helper_functions'
# This calculates the parent folder of 'logics' and adds it to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now Python can safely discover and load this module without crashing
from helper_functions import llm 

# Load the updated Singapore Parliamentary Dataset
def load_political_data():
    filepath = './data/mp_ministers_data.json'
    if not os.path.exists(filepath) and os.path.exists('mp_ministers_data.json'):
        filepath = 'mp_ministers_data.json'
    with open(filepath, 'r') as file:
        return json.load(file)

def identify_relevant_politicians(user_message):
    delimiter = "####"
    politicians_data = load_political_data()
    
    # Get just names to give the LLM options to match
    available_names = list(politicians_data.keys())

    system_message = f"""
    You are an administrative data parser for SGPayPulse.
    Your task is to identify which individuals from the following list are relevant to the user's query.
    
    Available Individuals: {available_names}

    Output the matched names strictly as a JSON list of strings. 
    If no specific individuals match, return an empty list [].
    Do not add extra conversational markdown text, backticks, or system delimiters.
    """

    messages =  [
        {'role':'system', 'content': system_message},
        {'role':'user', 'content': f"{delimiter}{user_message}{delimiter}"},
    ]
    response_str = llm.get_completion_by_messages(messages)
    
    try:
        # Clean up possible markdown wrappers if added by model
        cleaned_str = response_str.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_str)
    except Exception:
        return []

def generate_political_response(user_message, structured_profiles):
    delimiter = "####"

    system_message = f"""
    You are the SGPayPulse AI Transparency Chatbot. Your goal is to provide clear, transparent, and accurate information regarding Singapore's Ministers and Members of Parliament (MPs).
    
    Use the following verified profiles to fulfill the user's inquiry:
    {structured_profiles}

    Instructions:
    1. Respond in a highly professional, objective, and neutral tone.
    2. Address the user's questions about career progression, represented constituencies, terms, or historical portfolios accurately based ONLY on the provided context.
    3. Construct a concise comparative analysis if multiple individuals are mentioned.
    """

    messages =  [
        {'role':'system', 'content': system_message},
        {'role':'user', 'content': f"{delimiter}{user_message}{delimiter}"},
    ]
    return llm.get_completion_by_messages(messages)

def process_user_message(user_input):
    # 1. Identity who the query is about
    matched_names = identify_relevant_politicians(user_input)
    
    # 2. Extract profile records
    all_data = load_political_data()
    matched_profiles = [all_data[name] for name in matched_names if name in all_data]
    
    # 3. Generate natural language response
    reply = generate_political_response(user_input, matched_profiles)
    
    return {
        "text_reply": reply,
        "structured_profiles": matched_profiles
    }
