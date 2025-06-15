import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load Gemini API key
genai.configure(api_key="AIzaSyBde52tEU_6WvxswVmuiepXr1ozZ7BR2BI")

def build_regeneration_prompt(original_prompt, conversation, eval_result):
    eval_text = json.dumps(eval_result, indent=2)
    conv_text = "\n".join([f"{turn['role'].capitalize()}: {turn['message']}" for turn in conversation])

    return f"""
You are a Prompt Improvement Assistant for conversational LLM agents.

Below is a prompt that was originally given to an LLM to simulate a debt collection agent.

----------------------------
Original Prompt:
{original_prompt}

----------------------------
The conversation it generated:
{conv_text}

----------------------------
Evaluation of the conversation:
{eval_text}

----------------------------

Please generate a new improved version of the **prompt** that fixes the weaknesses shown in the evaluation.

For example, if the evaluation says `"is_repeating": "yes"`, improve the prompt to encourage the agent not to repeat itself.

DO NOT regenerate the conversation — only generate a **new, better prompt**.

Also note: This is only *one example conversation*. Your improved prompt should work more generally.

Only return the new improved prompt.
"""

def generate_new_prompt(input_file):
    # with open(input_file, "r", encoding="utf-8") as f:
    #     data = json.load(f)
    data = input_file

    original_prompt = data["prompt"]
    conversation = data["conversation"]
    eval_result = data["eval"][0]

    regen_prompt = build_regeneration_prompt(original_prompt, conversation, eval_result)

    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
    response = model.generate_content(regen_prompt)

    return response.text.strip()

