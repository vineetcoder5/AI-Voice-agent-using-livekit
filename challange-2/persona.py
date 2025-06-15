import google.generativeai as genai

genai.configure(api_key="AIzaSyBde52tEU_6WvxswVmuiepXr1ozZ7BR2BI")

def create_defaulter_prompt(name, amount_due, due_date, personality_desc):
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

    full_instruction = f"""
You are a human named {name}, who has defaulted on a loan of ₹{amount_due}, due since {due_date}.

You must behave and respond in a realistic conversation with a debt collection agent. 
Your personality traits and behavior are described as: {personality_desc}.

Generate a **detailed system prompt** that can be used to instruct an LLM to fully impersonate this person in a back-and-forth conversation. 
This prompt should guide the LLM to:
- Emulate the tone, speaking style, and emotional behavior of the defaulter.
- Mention relevant personal background if needed to justify behavior.
- Offer realistic excuses or reasons for late payment.
- Possibly negotiate, avoid, or become emotional during the conversation.
- Respond in a way that’s consistent with the personality traits.

Make sure the output is written in **prompt format**, not just a description.
"""

    response = model.generate_content(full_instruction)
    return response.text