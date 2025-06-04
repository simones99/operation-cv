import logging
import json
import requests
import os
from pathlib import Path
from jsonschema import validate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load CV schema
SCHEMA_PATH = Path(__file__).parent / "cv_schema.json"
with open(SCHEMA_PATH) as f:
    CV_SCHEMA = json.load(f)

def load_cv_schema():
    """Load the CV JSON schema from file"""
    schema_path = Path(__file__).parent / 'cv_schema.json'
    if not schema_path.exists():
        raise FileNotFoundError("CV schema file not found")
    with open(schema_path) as f:
        return json.load(f)

def ask_local_llm(prompt, system_prompt=None, temperature=0.7, use_schema=True):
    """
    Sends a prompt to the local LLM via /v1/chat/completions endpoint and returns the response.
    Also returns the full messages list used for the request.
    
    Args:
        prompt (str): The main prompt for the LLM
        system_prompt (str, optional): System message to set the context
        temperature (float, optional): Sampling temperature (0-1)
        use_schema (bool, optional): Whether to enforce JSON schema for CV output
    """
    url = "http://127.0.0.1:1234/v1/chat/completions"
    messages = []
    
    # Load schema if needed
    schema = None
    if use_schema:
        try:
            schema = load_cv_schema()
            # Add schema to system prompt
            schema_instruction = """
            You MUST format your response as a JSON object according to this structure:
            {
              "type": "object",
              "sections": {
                "summary": "A clear professional summary",
                "experience": [
                  {
                    "title": "Job title",
                    "company": "Company name",
                    "period": "Employment period",
                    "description": ["Achievement 1", "Achievement 2"]
                  }
                ],
                "education": [
                  {
                    "degree": "Degree name",
                    "institution": "Institution name",
                    "period": "Study period",
                    "details": ["Detail 1", "Detail 2"]
                  }
                ],
                "skills": {
                  "technical": ["Skill 1", "Skill 2"],
                  "soft": ["Skill 1", "Skill 2"]
                }
              }
            }
            
            INSTRUCTIONS:
            1. Return ONLY the JSON object
            2. Use double quotes for strings
            3. Include only sections that are relevant
            4. Keep descriptions clear and concise
            5. DO NOT add any explanatory text
            """
            if system_prompt:
                system_prompt = f"{system_prompt}\n\n{schema_instruction}"
            else:
                system_prompt = schema_instruction
        except Exception as e:
            print(f"Warning: Could not load CV schema: {e}")
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({"role": "system", "content": "You are a helpful assistant."})
    messages.append({"role": "user", "content": prompt})
    
    # Note: Keep payload minimal for LM Studio compatibility
    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }
    try:
        # Add headers for proper API communication
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        
        # Log response for debugging
        if response.status_code != 200:
            logger.error(f"LM Studio API Error: Status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
            
        content = response.json()['choices'][0]['message']['content']
        
        # Validate JSON schema if needed
        if use_schema and schema:
            try:
                # Parse the content as JSON
                if isinstance(content, str):
                    cv_data = json.loads(content)
                else:
                    cv_data = content
                
                # Validate the JSON structure
                is_valid, error_message = validate_cv_json(cv_data, schema)
                if not is_valid:
                    raise ValueError(f"Invalid CV format: {error_message}")
                    
                logger.info("CV JSON validation successful")
                
            except json.JSONDecodeError:
                return f"Error: LLM response is not valid JSON: {content}", messages
            except Exception as e:
                return f"Error: LLM response does not match schema: {e}", messages
        
        return content, messages
    except requests.exceptions.RequestException as e:
        return f"Error communicating with local LLM: {e}", messages
    except Exception as e:
        return f"Unexpected error: {e}", messages

def validate_cv_json(data, schema):
    """Validate CV JSON data against schema"""
    try:
        # Basic structure validation
        if not isinstance(data, dict):
            raise ValueError("Response must be a JSON object")
        
        if 'sections' not in data:
            raise ValueError("Response missing required 'sections' object")
            
        sections = data['sections']
        if not isinstance(sections, dict):
            raise ValueError("'sections' must be an object")
            
        # Required sections validation
        if 'summary' not in sections:
            raise ValueError("CV must include a summary section")
            
        # Validate experience format if present
        if 'experience' in sections:
            if not isinstance(sections['experience'], list):
                raise ValueError("Experience must be an array")
            for exp in sections['experience']:
                if not all(k in exp for k in ['title', 'company', 'period', 'description']):
                    raise ValueError("Experience entries must include title, company, period, and description")
                if not isinstance(exp['description'], list):
                    raise ValueError("Experience description must be an array")
                    
        # Validate education format if present
        if 'education' in sections:
            if not isinstance(sections['education'], list):
                raise ValueError("Education must be an array")
            for edu in sections['education']:
                if not all(k in edu for k in ['degree', 'institution', 'period']):
                    raise ValueError("Education entries must include degree, institution, and period")
                
        # Add more specific validations as needed
        
        return True, None
    except Exception as e:
        return False, str(e)

def validate_llm_response(content):
    """Validate that the LLM response is properly formatted JSON"""
    try:
        if isinstance(content, str):
            content = json.loads(content)
        validate(instance=content, schema=CV_SCHEMA)
        return content
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError("LLM response was not valid JSON")
    except Exception as e:
        logger.error(f"JSON validation error: {e}")
        raise ValueError("LLM response did not match expected schema")

def check_llm_server(url):
    """Check if LM Studio server is running and responding"""
    try:
        response = requests.get(f"{url}/v1/models")
        if response.status_code == 200:
            return True
        logger.error(f"LM Studio server check failed with status {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to LM Studio server: {e}")
        return False

async def get_completion(prompt, system_prompt="", temperature=0.7):
    """Get completion from LM Studio with proper error handling"""
    url = "http://localhost:1234/v1/chat/completions"
    
    if not check_llm_server(url.rsplit("/v1/", 1)[0]):
        raise ConnectionError("LM Studio server is not running or not responding")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }
    try:
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"LM Studio API Error: Status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
            
        content = response.json()['choices'][0]['message']['content']
        
        # Validate the response against our schema
        validated_content = validate_llm_response(content)
        return validated_content
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to LM Studio failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing LLM response: {e}")
        raise
