"""
Centralized prompt templates for LLM screening.
"""
from typing import Dict, Any
import json

SCREENING_PROMPT_TEMPLATE = """
You are a high-sensitivity screening assistant for an academic systematic review.
Your task is to evaluate if the following research paper meets the inclusion criteria.

**Paper Details**
Title: {title}
Abstract: {abstract}

{criteria_descriptions}
**Instructions**
1. Evaluate the inclusion criteria strictly and separately.
2. Favor precision over high sensitivity. Do NOT assume relevance without explicit evidence.
3. If the paper does NOT explicitly meet ALL the required inclusion criteria, output "Exclude".
4. "Maybe" should ONLY be used if the abstract is highly ambiguous but suggests strong potential evidence for the criteria.
5. If the decision is "Exclude" or "Maybe", specify which inclusion criteria are not met in the "unmet_criteria" field (e.g. "IC2", "IC2+IC3", or "None").

**Output Format (JSON)**
Respond ONLY with a valid JSON object matching this schema:
{json_schema}
"""

def generate_prompt(title: str, abstract: str, criteria: Dict[str, Any]) -> str:
    """
    Generates the final prompt string dynamically based on the provided criteria.
    """
    criteria_sections = []
    schema_criteria_fields = {}
    
    for key, c in criteria.items():
        section = f"**{key}: {c.get('name')}**\n"
        section += f"- Definition: {c.get('definition')}\n"
        section += f"- Signals: {c.get('signals')}\n"
        section += f"- Negative Indicators: {c.get('negative_indicators')}\n"
        criteria_sections.append(section)
        
        schema_criteria_fields[key] = {
            "score": "float (0.0 to 1.0)",
            "evidences": ["list of quoted keywords/phrases"],
            "rationale": "explanation"
        }
        
    criteria_descriptions = "\n".join(criteria_sections)
    
    schema = {
        "decision": "Include | Exclude | Maybe",
        "unmet_criteria": f"e.g., {'+'.join(criteria.keys())} or None",
        "notes": "Any ambiguities or edge cases"
    }
    schema.update(schema_criteria_fields)
    
    json_schema = json.dumps(schema, indent=2)
    # Removing the quotes from instructions so the LLM doesn't just output strings for objects
    json_schema = json_schema.replace('"Include | Exclude | Maybe"', '"Include" | "Exclude" | "Maybe"')
    json_schema = json_schema.replace('"float (0.0 to 1.0)"', 'float (0.0 to 1.0)')
    json_schema = json_schema.replace('"[list of quoted keywords/phrases]"', '["list of quoted keywords/phrases"]')
    json_schema = json_schema.replace('"explanation"', '"explanation string"')
    
    return SCREENING_PROMPT_TEMPLATE.format(
        title=title,
        abstract=abstract,
        criteria_descriptions=criteria_descriptions,
        json_schema=json_schema
    )
