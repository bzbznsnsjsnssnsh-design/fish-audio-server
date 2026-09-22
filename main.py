import os
import io
from typing import Dict

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


app = FastAPI(
    title="Fish Audio TTS Server",
    version="1.0.0"
)


# ============================================================
# Voice Mapping
# الاسم -> Fish Audio reference_id
#
# ضع reference_id الحقيقي لكل صوت هنا.
# ============================================================

VOICE_MAPPING: Dict[str, str] = {
    "dan dan": "9f0fe09892994681aaa9d6bc54c2151a",
    "marcus": "79b3cb6f45a04df098319f3a1e345cb5",
    "bria": "b2cfa58f804543b5930cb944cb9df098",
    "alex": "6d7f99ee3ad64860b299e52504b2bdf9",

    # باقي الأصوات
    "scott": "9f0fe09892994681aaa9d6bc54c2151a",
    "shelby": "9f0fe09892994681aaa9d6bc54c2151a",
    "wade": "9f0fe09892994681aaa9d6bc54c2151a",
    "greg": "9f0fe09892994681aaa9d6bc54c2151a",
    "dan": "9f0fe09892994681aaa9d6bc54c2151a",
    "aaron": "9f0fe09892994681aaa9d6bc54c2151a",
    "serena": "9f0fe09892994681aaa9d6bc54c2151a",
    "djano": "9f0fe09892994681aaa9d6bc54c2151a",
    "knightley": "9f0fe09892994681aaa9d6bc54c2151a",
    "victoria": "9f0fe09892994681aaa9d6bc54c2151a",
    "ella": "9f0fe09892994681aaa9d6bc54c2151a",
    "oswald": "9f0fe09892994681aaa9d6bc54c2151a",
    "natasha": "9f0fe09892994681aaa9d6bc54c2151a",
    "ashton": "9f0fe09892994681aaa9d6bc54c2151a",
    "myra": "9f0fe09892994681aaa9d6bc54c2151a",
    "scarlett": "9f0fe09892994681aaa9d6bc54c2151a",
    "derrick": "9f0fe09892994681aaa9d6bc54c2151a",
    "ed": "9f0fe09892994681aaa9d6bc54c2151a",
    "mark": "9f0fe09892994681aaa9d6bc54c2151a",
    "reginald": "9f0fe09892994681aaa9d6bc54c2151a",
    "sally": "9f0fe09892994681aaa9d6bc54c2151a",
    "patricia": "9f0fe09892994681aaa9d6bc54c2151a",
    "cali": "9f0fe09892994681aaa9d6bc54c2151a",
    "johnny": "9f0fe09892994681aaa9d6bc54c2151a",
    "erika": "9f0fe09892994681aaa9d6bc54c2151a",
    "suzie": "9f0fe09892994681aaa9d6bc54c2151a",
    "blake": "9f0fe09892994681aaa9d6bc54c2151a",
    "ethan": "9f0fe09892994681aaa9d6bc54c2151a",
    "bella": "9f0fe09892994681aaa9d6bc54c2151a",
    "josha": "9f0fe09892994681aaa9d6bc54c2151a",
    "drew dickens": "9f0fe09892994681aaa9d6bc54c2151a",
    "catherine": "9f0fe09892994681aaa9d6bc54c2151a",
    "janiah": "9f0fe09892994681aaa9d6bc54c2151a",
    "erika biondi": "9f0fe09892994681aaa9d6bc54c2151a",
    "eve": "9f0fe09892994681aaa9d6bc54c2151a",
    "justine": "9f0fe09892994681aaa9d6bc54c2151a",
}


class GenerateRequest(BaseModel):
    text: str
    voice: str


# ============================================================
# Fish Audio API
# ============================================================

FISH_API_URL = "https://api.fish.audio/v1/tts"


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Fish Audio TTS",
        "voices": len(VOICE_MAPPING)
    }


@app.get("/voices")
async def voices():
    return {
        "voices": list(VOICE_MAPPING.keys())
    }


@app.post("/generate")
async def generate_audio(request: GenerateRequest):

    # --------------------------------------------------------
    # النص
    # --------------------------------------------------------

    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty."
        )

    # --------------------------------------------------------
    # اسم الصوت - غير حساس لحالة الأحرف
    # --------------------------------------------------------

    voice_name = request.voice.strip().lower()

    if voice_name not in VOICE_MAPPING:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unknown voice",
                "voice": request.voice,
                "available_voices": list(VOICE_MAPPING.keys())
            }
        )

    reference_id = VOICE_MAPPING[voice_name]

    # --------------------------------------------------------
    # API Key
    # --------------------------------------------------------

    api_key = os.getenv("FISH_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="FISH_API_KEY is not configured."
        )

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",

        # Fish Audio free developer model
        "model": "s2.1-pro-free",

        "Accept": "audio/mpeg",
    }

    # --------------------------------------------------------
    # Request body
    # --------------------------------------------------------

    payload = {
        "text": text,
        "reference_id": reference_id,
        "format": "mp3",
    }

    # --------------------------------------------------------
    # Call Fish Audio
    # --------------------------------------------------------

    try:

        timeout = httpx.Timeout(
            connect=10.0,
            read=120.0,
            write=30.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:

            response = await client.post(
                FISH_API_URL,
                headers=headers,
                json=payload,
            )

    except httpx.TimeoutException:

        raise HTTPException(
            status_code=504,
            detail="Fish Audio request timed out."
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Fish Audio connection failed: {str(exc)}"
        )

    # --------------------------------------------------------
    # Fish Audio error
    # --------------------------------------------------------

    if response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail={
                "error": "Fish Audio API error",
                "status_code": response.status_code,
                "response": response.text[:1000],
            }
        )

    # --------------------------------------------------------
    # Audio
    # --------------------------------------------------------

    audio_data = response.content

    if not audio_data:

        raise HTTPException(
            status_code=502,
            detail="Fish Audio returned empty audio."
        )

    # --------------------------------------------------------
    # Return MP3 directly
    # --------------------------------------------------------

    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="speech.mp3"',
            "Cache-Control": "no-cache",
        },
    )


# ============================================================
# Local / Render
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv("PORT", "8000")
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
  )
