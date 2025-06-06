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
def load_cv_schema():
    """Load the CV JSON schema from file"""
    schema_path = Path(__file__).parent / 'cv_schema.json'
    if not schema_path.exists():
        raise FileNotFoundError("CV schema file not found")
    with open(schema_path) as f:
        return json.load(f)

CV_SCHEMA = load_cv_schema()

def ask_local_llm(prompt, system_prompt=None, temperature=0.7):
    """
    Send a prompt to the local LLM and return the response
    """
    url = "http://localhost:1234/v1/chat/completions"
    messages = []
    
    # Add system message if provided
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        # Default system prompt with clear output format instructions
        messages.append({"role": "system", "content": """You are a CV analysis assistant.
            Provide your response in this format:
            {
              "sections": {
                "name of the section": "Your improved CV text here"
              }
            }
            Keep the original professional level and roles."""})
    
    # Add user message
    messages.append({"role": "user", "content": prompt})
    
    # Configure the request payload with optimized settings for Apple Silicon
    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,  # Reduced for faster responses
        "top_p": 0.1,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "stream": False,
        "n_ctx": 2048,      # Reduced context window
        "num_threads": 8    # Optimized for M-series chips
    }
    
    try:
        # Send request to LM Studio
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"LM Studio API Error: Status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()
        
        # Extract content from response
        content = response.json()['choices'][0]['message']['content']
        logger.info(f"Raw LLM response: {content}")
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            # Return the parsed JSON object if it has the correct structure
            if isinstance(data, dict) and 'sections' in data:
                logger.info(f"Successfully parsed JSON with sections: {list(data['sections'].keys())}")
                return data, None
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            
        # If JSON parsing failed, try to clean up the response
        cleaned_content = validate_llm_response(content)
        return cleaned_content, None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        raise

def extract_summary(content):
    """Extract content and suggestions from the plain text response"""
    try:
        # Clean up the content and ensure it's a string
        if not isinstance(content, str):
            content = str(content)
        text = content.strip()
        
        # Initialize result structure
        result = {
            'content': '',
            'suggestions': []
        }
        
        # Simple state machine to parse sections
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if 'CONTENT:' in line.upper():
                current_section = 'content'
                continue
            elif any(x in line.upper() for x in ['IMPROVEMENTS:', 'SUGGESTIONS:']):
                current_section = 'suggestions'
                continue
                
            # Process content based on current section
            if current_section == 'content':
                if result['content']:
                    result['content'] += ' '
                result['content'] += line
            elif current_section == 'suggestions':
                # Clean up formatting
                cleaned = line.lstrip('- *1234567890.)')
                cleaned = cleaned.strip()
                if cleaned and len(cleaned) >= 20:
                    result['suggestions'].append(cleaned)
        
        # If no proper sections were found, use the whole text as content
        if not result['content'] and not result['suggestions']:
            result['content'] = text
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to extract summary: {str(e)}")
        return {'content': content, 'suggestions': []}

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
            
        # Validate each section has content
        for section_name, content in sections.items():
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"Section '{section_name}' must have non-empty string content")
        
        # Add more specific validations as needed
        
        return True, None
    except Exception as e:
        return False, str(e)

def validate_llm_response(content):
    """Validate and clean up the LLM response"""
    try:
        # If it's JSON, try to extract just the summary
        if isinstance(content, str):
            try:
                content = json.loads(content)
                if isinstance(content, dict) and 'sections' in content:
                    content = content['sections'].get('summary', '')
            except json.JSONDecodeError:
                pass  # Not JSON, treat as plain text
                
        # Clean up the text content
        if isinstance(content, str):
            content = content.strip()
            # Remove thinking tags if present
            if '<think>' in content:
                parts = content.split('</think>')
                content = parts[-1].strip() if len(parts) > 1 else content
            return content
        else:
            raise ValueError("Response format not recognized")
    except Exception as e:
        logger.error(f"Error validating response: {e}")
        raise ValueError(f"Invalid response format: {e}")

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

def truncate_messages(messages, max_tokens=2048):
    """Truncate messages to stay within token limit while preserving recent context"""
    # Approximate tokens (rough estimate: 4 chars = 1 token)
    char_limit = max_tokens * 4
    total_chars = 0
    result = []
    
    # Process messages from most recent to oldest
    for msg in reversed(messages):
        content_length = len(msg["content"])
        if total_chars + content_length <= char_limit:
            result.insert(0, msg)
            total_chars += content_length
        else:
            # Truncate the message to fit
            available_chars = char_limit - total_chars
            if available_chars > 100:  # Only keep if we can keep a meaningful chunk
                truncated_msg = msg.copy()
                truncated_msg["content"] = msg["content"][-available_chars:]
                result.insert(0, truncated_msg)
            break
            
    return result if result else [messages[-1]]  # Always keep at least the most recent message
