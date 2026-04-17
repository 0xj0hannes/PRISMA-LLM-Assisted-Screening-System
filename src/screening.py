from google import genai
import json
import os
import time
import logging
from typing import List, Dict, Optional
from .models import Record, ScreeningResult, CriterionResult
from .config import load_config

from .prompts import generate_prompt

config = load_config()

# Configure Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/screening.log",
    level=logging.DEBUG, # Set to DEBUG to capture detailed prompts and responses
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ScreeningLogger")

# Configure Gemini Client
api_key = config.get("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

def screen_record(record: Record) -> ScreeningResult:
    model_name = config.get("MODEL_NAME", "gemini-1.5-flash")
    criteria = config.get("CRITERIA", {})
    prompt = generate_prompt(title=record.title, abstract=record.abstract, criteria=criteria)
    
    max_retries = config.get("MAX_RETRIES", 3)
    last_error = ""

    logger.info(f"--- Starting screening for Record ID: {record.id} ---")
    logger.debug(f"[PROMPT SENT]\n{prompt}\n[END PROMPT]")

    attempt = 0
    transient_attempts = 0
    
    while True:
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries} (Transient Retries: {transient_attempts})...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            
            logger.debug(f"[RAW RESPONSE]\n{response.text}\n[END RESPONSE]")
            
            # Parse JSON
            result_json = json.loads(response.text)
            
            parsed_criteria = {}
            for key in criteria.keys():
                c_data = result_json.get(key, {})
                parsed_criteria[key] = CriterionResult(
                    score=c_data.get("score", 0.0),
                    evidences=c_data.get("evidences", []),
                    rationale=c_data.get("rationale", "")
                )
            
            logger.info(f"Record {record.id} mapped successfully. Decision: {result_json.get('decision')}")
            
            return ScreeningResult(
                record_id=record.id,
                decision=result_json.get("decision", "Maybe"),
                criteria=parsed_criteria,
                unmet_criteria=result_json.get("unmet_criteria", ""),
                notes=result_json.get("notes", ""),
                timestamp=str(os.times()), 
                model_version=model_name
            )
            
        except Exception as e:
            last_error = str(e)
            
            # Less noisy logging for known transient errors like 503 and Rate Limits
            is_transient = "503" in last_error or "429" in last_error or "quota" in last_error.lower()
            if is_transient:
                logger.warning(f"Transient API Error on Record {record.id}: {last_error}")
            else:
                logger.error(f"API Error on Attempt {attempt+1}/{max_retries} for Record {record.id}: {last_error}", exc_info=True)
                
            print(f"  API Error: {last_error}. Retrying...")
            
            if is_transient:
                # Wait indefinitely for transient errors, but cap the sleep time backoff
                capped_attempt = min(transient_attempts, 6) # Max 15 * 64 = 960 seconds ~ 16 minutes
                sleep_time = 15 * (2 ** capped_attempt)
                logger.info(f"Sleeping for {sleep_time} seconds before retrying infinitely...")
                time.sleep(sleep_time)
                transient_attempts += 1
                continue
            else:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    attempt += 1
                    continue
                else:
                    break # Give up on persistent non-transient errors (like 404 Model Not Found)
            
    logger.error(f"Failed to screen Record {record.id} after {max_retries} attempts. Last error: {last_error}")
    return ScreeningResult(
        record_id=record.id,
        decision="Maybe",
        notes=f"Failed after {max_retries} attempts. Last error: {last_error}"
    )

def batch_screen(records: List[Record], already_screened: Dict[str, ScreeningResult] = None):
    """
    Screens records using LLM. Returns a generator that yields (record_id, result).
    This allows the caller to save progress incrementally.
    """
    if already_screened is None:
        already_screened = {}
    
    print(f"Screening {len(records)} records...")
    
    for i, record in enumerate(records):
        if record.id in already_screened:
            # Skip if we already have a valid decision (not a failure from previous run)
            existing = already_screened[record.id]
            if "Failed after" not in existing.notes:
                # No need to yield if it's already in already_screened and valid
                continue
        
        print(f"Processing {i}/{len(records)}...")
            
        result = screen_record(record)
        yield record.id, result
        
        # Check for fatal errors that should stop the batch
        if "Quota exceeded" in result.notes or "429" in result.notes:
            print(f"\n[FATAL] API limit reached at record {i}. Stopping batch.")
            break
        if "exhausted" in result.notes.lower():
            print(f"\n[FATAL] Resource exhausted at record {i}. Stopping batch.")
            break
