import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Load Gemini API key

genai.configure(api_key="AIzaSyBde52tEU_6WvxswVmuiepXr1ozZ7BR2BI")

def extract_first_valid_json(text):
    # Regex to find all curly-braced blocks
    candidate_jsons = re.findall(r'\{.*?\}', text, re.DOTALL)

    for candidate in candidate_jsons:
        try:
            obj = json.loads(candidate)
            return [obj]  # Return the first valid JSON object in a list
        except json.JSONDecodeError:
            continue

    return []

def evaluate_conversation(conversation):
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    conversation = conversation["conversation"]

    formatted_conv = "\n".join(
        [f"{turn['role'].capitalize()}: {turn['message']}" for turn in conversation]
    )

    prompt = f"""
You are an expert LLM conversation evaluator.

Given the following conversation between a debt collection agent ("agent") and a customer ("user"), analyze only the agent's messages and evaluate the following three things:

1. Is the bot (agent) repeating itself?
2. Is the bot negotiating enough?
3. Is the bot giving irrelevant responses?

Reply in **JSON format**, exactly like this:
{{
  "is_repeating": "yes" or "no",
  "is_negotiating_enough": "yes" or "no",
  "is_irrelevant": "yes" or "no"
}}

Conversation:
{formatted_conv}
"""

    response = model.generate_content(prompt)

    answer = extract_first_valid_json(response.text)
    if answer!=[]:
        return answer
    else:
        return []

