import logging
import asyncio
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
import json
from persona import create_defaulter_prompt
from validate import evaluate_conversation
from self_correct import generate_new_prompt

from livekit.agents import Agent, AgentSession, function_tool, RunContext
from livekit.plugins import google

# # Load environment variables from .env.local
# load_dotenv(dotenv_path=".env.local")

# Configure logging
logger = logging.getLogger("call-simulation")
logger.setLevel(logging.INFO)


# -------------------------
# Agent 1: Outbound Caller (Bank Representative)
# -------------------------
class OutboundCaller(Agent):
    def __init__(self, *, prompt: str,name: str, amount_due: str, due_date: str, summary: str, today: str):
        instructions = prompt.format(name=name, amount_due=amount_due,due_date=due_date,today=today,summary=summary)
        super().__init__(instructions=instructions)
        self.call_ended = False
        self.transcript_log: list[dict] = []

    async def hangup(self):
        self.call_ended = True
        return "end"

    @function_tool()
    async def end_call(self, ctx: RunContext):
        logger.info("[Agent] Ending the call via function tool.")
        self.call_ended = True
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        await self.hangup()

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        logger.info("[Agent] Answering machine detected via function tool.")
        self.call_ended = True
        await self.hangup()

    @function_tool()
    async def log_complaint(self, ctx: RunContext, reason: str):
        log_entry = f"[Complaint] : {reason}"
        logger.info(log_entry)
        self.transcript_log.append({"role": "agent", "message": log_entry})
        return "I'm sorry to hear that. I've logged your concern."

    @function_tool()
    async def reschedule_call(self, ctx: RunContext, date: str):
        log_entry = f"[Reschedule] Requested callback on {date}"
        logger.info(log_entry)
        self.transcript_log.append({"role": "agent", "message": log_entry})
        return f"No problem. I’ll mark your preferred call-back date as {date}."

# -------------------------
# Agent 2: Human-like Simulator
# -------------------------
class HumanLikeAgent(Agent):
    def __init__(self,*,prompt:str):
        super().__init__(
            instructions=prompt+""" 
You can:
- End the call using end_call.
"""
        )
        self.call_ended = False
        self.transcript_log: list[dict] = []
        

    async def hangup(self):
        self.call_ended = True
        return "end"

    @function_tool()
    async def end_call(self, ctx: RunContext):
        logger.info("[User] Ending the call via function tool.")
        self.call_ended = True
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        await self.hangup()

async def run_call_flow(prompt, defaulter_prompt, name, amount_due, due_date):
    # Initialize Agent Sessions per attempt
    session_bot = AgentSession(
        llm=google.LLM(
            model="gemini-2.5-flash-preview-04-17",
            temperature=0.8,
            api_key="AIzaSyAZJlb3q44HSCvNPIt7vqYBEQ5zP6h5O_4"
        )
    )
    session_human = AgentSession(
        llm=google.LLM(
            model="gemini-2.5-flash-preview-04-17",
            temperature=0.8,
            api_key="AIzaSyBde52tEU_6WvxswVmuiepXr1ozZ7BR2BI"
        )
    )

    # Instantiate Agents with fresh state
    bank_agent = OutboundCaller(
        prompt=prompt,
        name=name,
        amount_due=amount_due,
        due_date=due_date,
        summary="No past conversation",
        today=datetime.now().strftime("%B %d, %Y"),
    )
    human_agent = HumanLikeAgent(prompt=defaulter_prompt)

    await session_bot.start(agent=bank_agent)
    await session_human.start(agent=human_agent)

    conversation = []
    user_input = "Hello"

    # run back-and-forth until one ends
    while not (bank_agent.call_ended or human_agent.call_ended):
        # bank agent speaks
        resp_bot = await session_bot.generate_reply(user_input=user_input)
        bot_msg = resp_bot.chat_message.content[0]
        logger.info(f"Agent replied: {bot_msg}")
        conversation.append({"role": "agent", "message": bot_msg})
        if bank_agent.call_ended or human_agent.call_ended:
            break

        # human agent replies
        resp_usr = await session_human.generate_reply(user_input=bot_msg)
        user_msg = resp_usr.chat_message.content[0]
        logger.info(f"User replied: {user_msg}")
        conversation.append({"role": "user", "message": user_msg})
        if bank_agent.call_ended or human_agent.call_ended:
            break

        user_input = user_msg
        time.sleep(1)

    # Evaluate after conversation ends
    transcript = {"prompt": prompt, "conversation": conversation}
    eval_results = evaluate_conversation(transcript)
    return conversation, eval_results

async def main():
    base_prompt = """
You are Joe, working for SBI Bank, calling customers to remind them about unpaid bills.

You're speaking with {name}, who owes ${amount_due}. The due date was {due_date}, and today is {today}.
You're making a follow-up call. Be polite, professional, and empathetic. Handle resistance gently.

Conversation history:
{summary}

You can:
- Log a complaint using log_complaint.
- Reschedule a callback using reschedule_call.
- End the call using end_call.
"""

    name = input("Enter defaulter's name (e.g., Sania Gupta): ").strip()
    amount_due = input("Enter amount due (e.g., 125.50): ").strip()
    due_date = input("Enter due date (e.g., May 25, 2025): ").strip()
    personality = input("Enter personality traits (e.g., emotional, defensive, anxious): ").strip()

    defaulter_prompt = create_defaulter_prompt(name, amount_due, due_date, personality)

    attempt = 0
    max_retries = 3

    while attempt < max_retries:
        attempt += 1
        print(f"\n--- Starting call attempt #{attempt} ---")
        conversation, eval_results = await run_call_flow(
            prompt=base_prompt,
            defaulter_prompt=defaulter_prompt,
            name=name,
            amount_due=amount_due,
            due_date=due_date
        )

        # Check evaluation for success criteria
        success = False
        for obj in eval_results:
            if (obj.get("is_repeating") == "no" and
                obj.get("is_negotiating_enough") == "yes" and
                obj.get("is_irrelevant") == "no"):
                success = True
                break

        if success:
            print("Call flow met all success criteria.")
            break
        else:
            print("Call flow did not meet criteria. Generating new prompt and retrying...")
            # Generate improved prompt
            base_prompt = generate_new_prompt({"prompt": base_prompt, "conversation": conversation, "eval": eval_results})

    # Save final transcript
    final_data = {"prompt": base_prompt, "conversation": conversation, "eval": eval_results}
    with open("transcript.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)
    logger.info("\nTranscript saved to transcript.json")

if __name__ == "__main__":
    asyncio.run(main())