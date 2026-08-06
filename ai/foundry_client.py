from openai import OpenAI

MODEL_ID = "mistralai-Mistral-7B-Instruct-v0-2-generic-cpu"
BASE_URL = "http://127.0.0.1:51298/v1"

def _build_context_block(ci_name: str | None, ci_environment: str | None, owner_name: str | None) -> str:
        context_lines = []
        if ci_name:
            context_lines.append(f"Affected system: {ci_name}")
        if ci_environment:
            context_lines.append(f"Environment: {ci_environment}")
        if owner_name:
            context_lines.append(f"System owner: {owner_name}")
        return "\n" + "\n".join(context_lines) + "\n" if context_lines else "\n"


def generate_incident_summary(title: str, description: str, ci_name: str | None = None, ci_environment: str | None = None, owner_name: str | None = None) -> str | None:
    try:
        client = OpenAI(base_url=BASE_URL, api_key="not-needed")

        context_block = _build_context_block(ci_name, ci_environment, owner_name)
        
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{
                "role": "user",
                "content": (
                    "You are an IT operations assistant. Write a one-sentence triage summary "
                    "of the incident, in English, focused on business impact.\n"
                    f"{context_block}"
                    f"Title: {title}\nDescription: {description}"
                )
            }]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[foundry_client] ERROR: {e}")
        return None

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

def classify_incident_severity(title: str, description: str, ci_name: str | None = None, ci_environment: str | None = None, owner_name: str | None = None) -> str | None:
    try:
         client = OpenAI(base_url=BASE_URL, api_key="not-needed")
         context_block = _build_context_block(ci_name, ci_environment, owner_name)

         response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{
                 "role": "user",
                 "content": (
                      "You are an IT operations assistant. Classify the severity of this incident "
                      "as exactly one word: LOW, MEDIUM, HIGH, or CRITICAL. Reply this only that word. \n"
                      f"{context_block}"
                      f"Title: {title}\nDescription: {description}"
                 )
            }]
         )
         raw = response.choices[0].message.content.strip().upper()
         return next((s for s in VALID_SEVERITIES if s in raw), None)

    except Exception as e:
         print(f"[foundry_client] ERROR: {e}")
         return None