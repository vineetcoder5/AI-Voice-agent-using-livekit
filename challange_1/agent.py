from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv
import json
import os
from typing import Any
from datetime import datetime

from livekit import rtc, api
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    function_tool,
    RunContext,
    get_job_context,
    cli,
    WorkerOptions,
    RoomInputOptions,
)
from livekit.plugins import (
    deepgram,
    cartesia,
    silero,
    noise_cancellation,  # noqa: F401
)
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.plugins import google

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")


class OutboundCaller(Agent):
    def __init__(
        self,
        *,
        name: str,
        amount_due: str,
        due_date: str,
        summary: str,
        today: str,
        dial_info: dict[str, Any],
        
    ):
        super().__init__(
            instructions = f"""
You are an joe working for sbi Bank to remind customers about their unpaid bills.
You are currently speaking to {name}, who owes ${amount_due}. The due date was {due_date}. 
Today is {today}, and you are making a follow-up call to the customer.

Be polite, professional, and empathetic. answer queries, and handle resistance gently.

Here is the summary of the past conversation made by a human agent:
{summary}

You can:
- Log a complaint using log_complaint.
- Reschedule a callback using reschedule_call.
- End the call using end_call.
""")
        self.participant: rtc.RemoteParticipant | None = None

        self.dial_info = dial_info
        self.transcript_log: list[str] = [] # for logging events like complaints/reschedules


    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    async def hangup(self):
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        logger.info(f"ending the call for {self.participant.identity}")

        # let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await self.hangup()

    @function_tool()
    async def log_complaint(self, ctx: RunContext, reason: str):
        log_entry = f"[Complaint] {self.participant.identity}: {reason}"
        logger.info(log_entry)
        self.transcript_log.append(log_entry)
        return "I'm sorry to hear that. I've logged your concern."

    
    @function_tool()
    async def reschedule_call(self, ctx: RunContext, date: str):
        log_entry = f"[Reschedule] {self.participant.identity} requested callback on {date}"
        logger.info(log_entry)
        self.transcript_log.append(log_entry)
        return f"No problem. I’ll mark your preferred call-back date as {date}."

    

async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()

    dial_info = json.loads(ctx.job.metadata)
    participant_identity = phone_number = dial_info["phone_number"]

    # look up the user's phone number and appointment details
    agent = OutboundCaller(
        name="Jack",
        amount_due="125.0 dollar",
        due_date="May 25, 2025",
        summary = "No past conversation",
        today = str(datetime.now().strftime("%B %d, %Y")),
        dial_info=dial_info,
    )

    session = AgentSession(
        turn_detection=EnglishModel(),
        vad=silero.VAD.load(),
        stt=deepgram.STT(),                
        tts=cartesia.TTS(
            model="sonic-2",
            voice="bf0a246a-8642-498a-9950-80c35e9276b5",
            language="en"
        ), # Optional: or use google.TTS() cartesia.TTS(),                 
        llm=google.LLM(
            model="gemini-2.5-flash-preview-04-17",
            temperature=0.8,
        )
    )
    # ✅ Save transcript at shutdown
    def write_transcript():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/transcript_{ctx.room.name}_{timestamp}.json"
        full_transcript = {
            "transcript": session.history.to_dict(),
            "custom_log": agent.transcript_log,
        }
        os.makedirs("logs", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(full_transcript, f, indent=2)
        logger.info(f"Transcript saved to {filename}")

    ctx.add_shutdown_callback(write_transcript)

    # start the session first before dialing, to ensure that when the user picks up
    # the agent does not miss anything the user says
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                # enable Krisp background voice and noise removal
                noise_cancellation=noise_cancellation.BVCTelephony(),
            ),
        )
    )

    # `create_sip_participant` starts dialing the user
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=participant_identity,
                # function blocks until user answers the call, or if the call fails
                wait_until_answered=True,
            )
        )

        # wait for the agent session start and participant join
        await session_started
        participant = await ctx.wait_for_participant(identity=participant_identity)
        logger.info(f"participant joined: {participant.identity}")

        agent.set_participant(participant)

    except api.TwirpError as e:
        logger.error(
            f"error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-caller",
        )
    )
