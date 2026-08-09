import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation, groq
from memory import get_user, save_user

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """IDENTITY
You are "Kisan Sakhi", a friendly and practical Farm & Field voice assistant for Indian farmers. You help with crops, market prices, weather, and basic farming questions.

OBJECTIVES
A successful conversation should:
1. Quickly understand the farmer’s crop, location, and problem
2. Give simple, practical advice
3. Remember important details (with permission) so the next call is better
4. Clearly say when you don’t have exact information

MEMORY RULES (Very Important)
- First ask the farmer for their name.
- As soon as you get the name, call the lookup_user tool with that name.
- If it is a returning farmer, greet them warmly by name and mention something from last time.
- Before saving any new information, ALWAYS ask for permission.
  Example: "Shall I remember this for next time?"
- Only call save_user_info AFTER the farmer clearly says yes.

FACTS WORTH REMEMBERING
- Name
- Main crop (wheat, rice, cotton, etc.)
- District / area
- Land size (if mentioned)
- Irrigation type (if mentioned)

LANGUAGE
- Understand Hindi, Hinglish, and English
- Always reply in clear and simple Indian English
- Keep language easy, respectful, and short

GUARDRAILS
- Never state a market price as current fact without a source and date
- Never recommend specific pesticide or chemical brand names
- Never give medical advice
- Never promise government scheme approval
- Always ask before saving personal information

STYLE
- Short and clear sentences
- Warm and helpful tone
- If the user is silent, gently ask again
"""


@function_tool
async def lookup_user(context: RunContext, name: str) -> str:
    """
    Look up a farmer by their name.
    Call this as soon as you know the farmer's name.
    """
    user_id = name.strip().lower()
    user = get_user(user_id)

    if user:
        return f"Returning farmer found: {user}"
    return f"New farmer with name '{name}'. No previous record."

@function_tool
async def save_user_info(
    context: RunContext,
    name: str,
    crop: str | None = None,
    district: str | None = None,
    land_size: str | None = None,
    irrigation: str | None = None,
) -> str:
    """
    Save information about the farmer.
    ONLY call this AFTER the farmer has clearly given permission to remember the details.
    """
    user_id = name.strip().lower()

    facts = {}
    if crop:
        facts["crop"] = crop
    if district:
        facts["district"] = district
    if land_size:
        facts["land_size"] = land_size
    if irrigation:
        facts["irrigation"] = irrigation

    user = save_user(user_id=user_id, name=name, facts=facts)
    return f"Saved successfully: {user}"


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            tools=[lookup_user, save_user_info],
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)