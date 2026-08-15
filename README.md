# Kisan Sakhi – Farm & Field Voice Agent

**Kisan Sakhi** is a voice AI assistant built for Indian farmers as part of the **10 Days of Voice Agents – #VoiceForBharat** challenge by Murf AI.

It helps farmers with:
- Weather information
- Approximate market prices
- Crop-related advice
- Remembering returning farmers
- Escalating serious problems to a human
- Handing complex crop issues to a specialist agent

Powered by **Murf Falcon** (fastest TTS), LiveKit, Deepgram, and Groq/Gemini.

---

## Track
**Farm & Field**

## Who is it for?
Indian farmers who prefer speaking instead of using complex apps. Voice is more accessible for people with limited literacy or smartphone experience.

---

## Features Built During the Challenge

| Feature | Description |
|---------|-------------|
| **Personality & Guardrails** | Clear role, objectives, and safety rules |
| **Memory** | Remembers farmer name, crop, district across calls |
| **Weather Tool** | Live weather using Open-Meteo |
| **Market Price Tool** | Approximate prices for major crops (English + Hindi names) |
| **Outbound Calling** | Can place real phone calls via Twilio + LiveKit SIP |
| **Human Escalation** | Creates help requests with Reference ID for serious problems |
| **Call Analytics Dashboard** | Shows Total / Successful / Failed calls |
| **Agent Handoff** | Hands over serious crop problems to a Crop Problem Specialist |

---

## Data Sources

- **Weather**: Live data from [Open-Meteo](https://open-meteo.com)
- **Market Prices**: Approximate local sample data (not live mandi API). Always cross-check with local mandi or [eNAM](https://enam.gov.in)

---

## Tech Stack

- **TTS**: Murf Falcon (`Anisha` voice)
- **STT**: Deepgram Nova-3
- **LLM**: Groq / Google Gemini
- **Transport**: LiveKit
- **Frontend**: Next.js
- **Database**: SQLite (for memory, escalations, call logs)

---S

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/Sainvi-j/kisan-sakhi.git
cd kisan-sakhi
```

### 2. Set up environment variables

Copy the example files and add your keys:

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

Required keys:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY` or Groq key

> Never commit real API keys.

### 3. Install dependencies

```bash
# Backend
cd backend
uv sync
uv run python src/agent.py download-files

# Frontend
cd ../frontend
pnpm install
```

### 4. Run the app

**Terminal 1 – Backend**
```bash
cd backend
uv run python src/agent.py dev
```

**Terminal 2 – Frontend**
```bash
cd frontend
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) and start talking.

---

## Project Structure

```
kisan-sakhi/
├── backend/
│   ├── src/
│   │   ├── agent.py          # Main agent + Crop Specialist + tools
│   │   └── memory.py         # User memory, escalations, call logs
│   ├── dashboard.py          # Simple analytics dashboard
│   └── make_call.py          # Outbound call script
├── frontend/                 # Next.js voice UI
└── README.md
```

---

## Important Notes

- Market prices are **approximate**. Always verify with local mandi.
- Outbound calling requires a Twilio account + verified numbers (trial limitations apply).
- The escalation and call analytics features use a local SQLite database.

---

## What I Would Improve Next

- Connect to real live mandi price APIs
- Better Hindi / regional language support
- Automatic outbound alerts based on weather thresholds
- Proper production deployment with monitoring


## Links

- [Murf API Docs](https://murf.ai/api/docs)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Docs](https://docs.livekit.io)
- [Deepgram Docs](https://developers.deepgram.com)
- [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
- [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
- [Murf Discord](https://discord.gg/FbKAy96Sz7)
- [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---
Built with ❤️ for Indian farmers during the Murf AI VoiceForBharat challenge.

## License

MIT
