from openai import OpenAI

MODEL_ID = "mistralai-Mistral-7B-Instruct-v0-2-generic-cpu"
BASE_URL = "http://127.0.0.1:51298/v1"

def generate_incident_summary(title: str, description: str, ci_name: str | None = None, ci_environment: str | None = None, owner_name: str | None = None) -> str | None:
    try:
        client = OpenAI(base_url=BASE_URL, api_key="not-needed")

        context_lines = []
        if ci_name:
            context_lines.append(f"Affected system: {ci_name}")
        if ci_environment:
            context_lines.append(f"Environment: {ci_environment}")
        if owner_name:
            context_lines.append(f"System owner: {owner_name}")
        context_block = ("\n" + "\n".join(context_lines) + "\n" if context_lines else "\n")
        
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
