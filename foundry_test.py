from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:53519/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="mistralai-Mistral-7B-Instruct-v0-2-generic-cpu",
    messages=[{"role": "user", "content": "Sammanfatta kort: Betalnings-API:t svarar med 500-fel på checkout, påverkar alla kunder."}]
)

print(response.choices[0].message.content)