import asyncio
import os
from livekit import api
from dotenv import load_dotenv

load_dotenv(".env.local")

async def make_outbound_call():
    livekit_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    room_name = "kisan-sakhi-outbound-call"
    phone_number = "+919755110658"
    trunk_id = "ST_QZrfFAvjJ8uK"

    # Create room + dispatch agent
    await livekit_api.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="",
            room=room_name,
            metadata=phone_number,
        )
    )

    # Create SIP participant (makes the phone ring)
    await livekit_api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity="kisan-sakhi-caller",
            participant_name="Kisan Sakhi",
            wait_until_answered=True,
        )
    )

    print("Call initiated!")
    await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(make_outbound_call())