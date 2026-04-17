import os
import json
from dotenv import load_dotenv

def load_config():
    # Find project root (one level up from src/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    env_path = os.path.join(project_root, '.env')
    criteria_path = os.path.join(project_root, 'criteria.json')
    
    # Load from specific path
    load_dotenv(dotenv_path=env_path)
    
    # Load criteria
    criteria = {}
    if os.path.exists(criteria_path):
        with open(criteria_path, 'r') as f:
            criteria = json.load(f)
    
    return {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "MODEL_NAME": os.getenv("MODEL_NAME", "gemini-1.5-flash"),
        "MAX_RETRIES": int(os.getenv("MAX_RETRIES", "3")),
        "CRITERIA": criteria,
    }
