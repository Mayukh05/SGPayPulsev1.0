import sys
import os
import json

# Force Python to point to the parent root directory for 'helper_functions'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helper_functions import llm

def load_political_data():
    """Safely loads data from the local JSON data repository."""
    filepath = './data/mp_ministers_data.json'
    if not os.path.exists(filepath) and os.path.exists('mp_ministers_data.json'):
        filepath = 'mp_ministers_data.json'
    with open(filepath, 'r') as file:
        return json.load(file)

def extract_profiles_by_keyword(user_message):
    """
    🌟 ROBUST BUG FIX: Bypasses fragile LLM classification by scanning the 
    user query directly against your database names and portfolios.
    """
    all_data = load_political_data()
    matched_profiles = []
    
    # Lowercase the user message for flawless comparison
    query_clean = user_message.lower()
    
    for name, profile in all_data.items():
        # Clean specific subcategories to match partial user string tokens
        name_lower = name.lower()
        appointment_lower = profile.get("current_appointment", "").lower()
        constituency_lower = profile.get("constituency", "").lower()
        
        # If the user mentions the name, the role, or the constituency, match the profile!
        if (name_lower in query_clean or 
            appointment_lower in query_clean or 
            constituency_lower in query_clean or
            any(name_part in query_clean for name_part in name_lower.split() if len(name_part) > 3)):
            
            if profile not in matched_profiles:
                matched_profiles.append(profile)
                
    return matched_profiles

def generate_grounded_response(user_message, structured_profiles):
    """Generates an answer using ONLY the data records pulled from the JSON file."""
    
    # Clean fallback string if no matching parameter values exist inside our file database
    if not structured_profiles:
        return ("I am sorry, but I couldn't find records matching those individuals or roles in the "
                "SGPayPulse database. Please refer to the 'View MP & Minister Records' directory tab "
                "to verify the names currently active in our repository.")

    # Wrap instructions inside a single explicit string block for your specific get_completion helper
    prompt = f"""
    You are the SGPayPulse AI Transparency Chatbot. Your objective is to provide citizens with information regarding Singapore's Ministers and Members of Parliament (MPs).

    CRITICAL RULES FOR ACCURACY:
    1. Rely ONLY on the following verified database profiles extracted from our local data store:
       {json.dumps(structured_profiles, indent=2)}
    2. Do NOT use your own external pre-trained knowledge to invent portfolios, terms, or historical entries. 
    3. If the user asks for details that are not present in the profile data provided above, state neutrally that the data is not available in the current repository.
    4. Maintain an objective, neutral, and factually accurate tone. Do not make things up.

    User Question: {user_message}
    
    Response:
    """
    
    # Call your standard get_completion helper function
    return llm.get_completion(prompt)

def process_user_message(user_input):
    """Orchestrator pipeline ensuring data grounding before generation."""
    # Step 1 & 2: Pull exact matches from the JSON dictionary
    matched_profiles = extract_profiles_by_keyword(user_input)
    
    # Step 3: Run text synthesis through final prompt configuration
    reply = generate_grounded_response(user_input, matched_profiles)
    
    return {
        "text_reply": reply,
        "structured_profiles": matched_profiles
    }
