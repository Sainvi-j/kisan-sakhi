import logging
import asyncio
from dotenv import load_dotenv
from livekit import rtc, api
from memory import get_user, save_user, create_escalation, get_open_escalations
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
import aiohttp
from requests import session

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """IDENTITY
You are "Kisan Sakhi", a friendly and practical Farm & Field voice assistant for Indian farmers. You help with crops, market prices, weather, and basic farming questions.

OBJECTIVES
A successful conversation should:
1. Quickly understand the farmer’s crop, location, and problem
2. Give simple, practical advice
3. Remember important details (with permission)
4. Use real weather and price data when needed
5. Ask for human help when the problem is serious or data is missing
6. Clearly say when you don’t have exact information

MEMORY RULES (Very Important)
- First ask the farmer for their name.
- As soon as you get the name, call the lookup_user tool with that name.
- If it is a returning farmer, greet them warmly by name and mention something from last time.
- Before saving any new information, ALWAYS ask for permission.
  Example: "Shall I remember this for next time?"
- Only call save_user_info AFTER the farmer clearly says yes.

WEATHER TOOL
- Whenever the farmer asks about weather, rain, temperature, humidity, or whether it is good for sowing/spraying/harvesting, call the get_weather tool.
- Always use the district you already know from memory if available.
- If you don’t know the district, ask for it first.
- After getting the weather, explain it in simple words that a farmer can understand.
- Always mention that the data is current / recent.

MARKET PRICE TOOL
- When the farmer asks about crop prices, mandi rates, or selling price, call the get_market_price tool.
- Always clearly say that the prices are approximate.
- If you know the farmer's district from memory, pass it to the tool.

HUMAN HELP (Escalation Rules)
You must call the create_escalation tool in these two situations only:

1. The farmer reports a serious crop problem  
   Examples: crop is dying, heavy pest attack, unknown disease, sudden large loss

2. Important data is missing or unreliable  
   Examples: weather service failed, market price not available, and the farmer urgently needs accurate information

Before creating any escalation:
- Clearly tell the farmer what information you want to share
- Ask for permission: "Shall I create a help request for a human expert?"
- Only call the tool if the farmer says yes

When you create the escalation:
- Give the farmer the Reference ID
- Tell them a human will review it (do not promise immediate reply)
- Keep the summary short and useful

FACTS WORTH REMEMBERING
- Name
- Main crop (wheat, rice, cotton, etc.)
- District / area
- Land size (if mentioned)
- Irrigation type (if mentioned)

LANGUAGE
- Always reply in clear and simple Indian English
- Understand Hindi, Hinglish, and English
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

@function_tool
async def get_weather(
    context: RunContext,
    district: str,
    state: str = "Madhya Pradesh",
) -> str:
    """
    Get the current weather and short forecast for a district in India.
    Use this whenever the farmer asks about weather, rain, temperature, or if it's good for farming activities.
    
    Args:
        district: Name of the district (e.g. Bhopal, Indore, Jaipur)
        state: Name of the state (default is Madhya Pradesh)
    """
    try:
        # First get coordinates using Open-Meteo geocoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": f"{district}, {state}, India",
            "count": 1,
            "language": "en",
            "format": "json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(geo_url, params=params) as resp:
                if resp.status != 200:
                    return "Sorry, I could not find that district right now. Please try again later."
                
                geo_data = await resp.json()
                if not geo_data.get("results"):
                    return f"I could not find the location {district}. Please check the district name."

                lat = geo_data["results"][0]["latitude"]
                lon = geo_data["results"][0]["longitude"]
                place_name = geo_data["results"][0]["name"]

            # Now get weather
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "Asia/Kolkata",
                "forecast_days": 3
            }

            async with session.get(weather_url, params=weather_params) as resp:
                if resp.status != 200:
                    return "Weather service is temporarily unavailable. Please try again in some time."

                data = await resp.json()
                current = data["current"]
                daily = data["daily"]

                # Simple weather code mapping
                weather_codes = {
                    0: "Clear sky",
                    1: "Mainly clear",
                    2: "Partly cloudy",
                    3: "Overcast",
                    45: "Foggy",
                    61: "Light rain",
                    63: "Moderate rain",
                    65: "Heavy rain",
                    80: "Rain showers",
                    95: "Thunderstorm"
                }
                condition = weather_codes.get(current["weather_code"], "Unknown conditions")

                result = (
                    f"Current weather in {place_name}: {condition}. "
                    f"Temperature is {current['temperature_2m']}°C with humidity {current['relative_humidity_2m']}%. "
                    f"Wind speed is {current['wind_speed_10m']} km/h. "
                    f"Today's maximum will be around {daily['temperature_2m_max'][0]}°C and minimum {daily['temperature_2m_min'][0]}°C. "
                    f"Expected rainfall today: {daily['precipitation_sum'][0]} mm."
                )
                return result

    except Exception as e:
        return "I'm having trouble fetching the weather right now. Please try again after some time."

@function_tool
async def get_market_price(
    context: RunContext,
    crop: str,
    district: str = None,
) -> str:
    """
    Get approximate market price for a crop.
    Use this when the farmer asks about mandi rates, selling price, or current price of any crop.
    Understands both English and Hindi crop names.
    
    Args:
        crop: Name of the crop in English or Hindi (e.g. wheat, gehun, rice, chawal, mustard, sarson)
        district: Optional district name
    """
    # Bigger price list (approximate ₹ per quintal)
    price_data = {
        # English + Hindi mappings
        "wheat": {"min": 2200, "max": 2450, "avg": 2320, "hindi": "gehun"},
        "gehun": {"min": 2200, "max": 2450, "avg": 2320, "hindi": "gehun"},
        "rice": {"min": 2800, "max": 3200, "avg": 3000, "hindi": "chawal"},
        "chawal": {"min": 2800, "max": 3200, "avg": 3000, "hindi": "chawal"},
        "paddy": {"min": 2100, "max": 2350, "avg": 2220, "hindi": "dhan"},
        "dhan": {"min": 2100, "max": 2350, "avg": 2220, "hindi": "dhan"},
        "mustard": {"min": 5200, "max": 5800, "avg": 5500, "hindi": "sarson"},
        "sarson": {"min": 5200, "max": 5800, "avg": 5500, "hindi": "sarson"},
        "cotton": {"min": 6500, "max": 7200, "avg": 6800, "hindi": "kapas"},
        "kapas": {"min": 6500, "max": 7200, "avg": 6800, "hindi": "kapas"},
        "soybean": {"min": 4200, "max": 4700, "avg": 4450, "hindi": "soyabean"},
        "soyabean": {"min": 4200, "max": 4700, "avg": 4450, "hindi": "soyabean"},
        "maize": {"min": 1800, "max": 2100, "avg": 1950, "hindi": "makka"},
        "makka": {"min": 1800, "max": 2100, "avg": 1950, "hindi": "makka"},
        "onion": {"min": 1200, "max": 1800, "avg": 1500, "hindi": "pyaz"},
        "pyaz": {"min": 1200, "max": 1800, "avg": 1500, "hindi": "pyaz"},
        "potato": {"min": 900, "max": 1400, "avg": 1100, "hindi": "aloo"},
        "aloo": {"min": 900, "max": 1400, "avg": 1100, "hindi": "aloo"},
        "tomato": {"min": 800, "max": 1600, "avg": 1200, "hindi": "tamatar"},
        "tamatar": {"min": 800, "max": 1600, "avg": 1200, "hindi": "tamatar"},
        "chilli": {"min": 8000, "max": 12000, "avg": 10000, "hindi": "mirch"},
        "mirch": {"min": 8000, "max": 12000, "avg": 10000, "hindi": "mirch"},
        "turmeric": {"min": 7000, "max": 9000, "avg": 8000, "hindi": "haldi"},
        "haldi": {"min": 7000, "max": 9000, "avg": 8000, "hindi": "haldi"},
        "groundnut": {"min": 5500, "max": 6200, "avg": 5800, "hindi": "moongfali"},
        "moongfali": {"min": 5500, "max": 6200, "avg": 5800, "hindi": "moongfali"},
        "gram": {"min": 4800, "max": 5400, "avg": 5100, "hindi": "chana"},
        "chana": {"min": 4800, "max": 5400, "avg": 5100, "hindi": "chana"},
        "moong": {"min": 7000, "max": 8000, "avg": 7500, "hindi": "moong"},
        "arhar": {"min": 6500, "max": 7500, "avg": 7000, "hindi": "arhar"},
        "tur": {"min": 6500, "max": 7500, "avg": 7000, "hindi": "arhar"},
    }

    crop_key = crop.strip().lower()

    if crop_key not in price_data:
        return (
            f"I don't have price data for {crop} right now. "
            "Please check your local mandi or eNAM for accurate rates."
        )

    data = price_data[crop_key]
    location_text = f" in {district}" if district else ""

    result = (
        f"Approximate market price for {crop}{location_text}: "
        f"around ₹{data['avg']} per quintal. "
        f"Usually ranges between ₹{data['min']} to ₹{data['max']}. "
        f"Note: These are approximate rates. For exact today's price, please check your local mandi or eNAM."
    )
    return result

@function_tool
async def create_escalation(
    context: RunContext,
    name: str,
    reason: str,
    summary: str,
    urgency: str = "medium",
) -> str:
    """
    Create a request for human help.
    Use this ONLY when:
    1. The farmer reports a serious crop problem (disease, heavy pests, crop dying)
    2. Important data (weather or market price) is missing or unreliable and the farmer needs accurate help urgently.
    
    ALWAYS ask for permission before calling this tool.
    """
    user_id = name.strip().lower()
    reference_id = create_escalation(
        user_id=user_id,
        name=name,
        reason=reason,
        summary=summary,
        urgency=urgency,
    )
    return f"Escalation created successfully. Reference ID: {reference_id}"
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            tools=[lookup_user, save_user_info, get_weather, get_market_price, create_escalation],
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

    # Get the phone number from metadata
    phone_number = ctx.job.metadata
    print(f"Going to call: {phone_number}")

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-3.6-flash"),
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

    print("Waiting for SIP participant...")

    # Wait specifically for the phone participant
    participant = await ctx.wait_for_participant(identity="kisan-sakhi-caller")
    print(f"SIP participant joined: {participant.identity}")

    # Extra wait for media to stabilize
    await asyncio.sleep(3)

    print("Speaking greeting now...")
    await session.say(
        "Namaste, this is Kisan Sakhi calling. "
        "I am your farming assistant. "
        "I am calling about your farm. "
        "You can say stop anytime if you don't want this call."
    )
    print("Greeting finished")

if __name__ == "__main__":
    cli.run_app(server)