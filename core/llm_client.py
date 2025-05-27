import requests

def ask_local_llm(prompt, system_prompt=None, temperature=0.7):
    """
    Sends a prompt to the local LLM via /v1/chat/completions endpoint and returns the response.
    Also returns the full messages list used for the request.
    """
    url = "http://127.0.0.1:1234/v1/chat/completions"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({"role": "system", "content": "You are a helpful assistant."})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": "local-model",  # LM Studio ignores this
        "messages": messages,
        "temperature": temperature,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return content, messages
    except requests.exceptions.RequestException as e:
        return f"Error communicating with local LLM: {e}", messages
    except Exception as e:
        return f"Unexpected error: {e}", messages
