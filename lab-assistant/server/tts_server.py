# Runs ON THE A100 (inside `brev shell`). Serves Qwen3-TTS on port 8002.
# Install first:
#   sudo apt-get update && sudo apt-get install -y sox libsox-dev
#   pip install -U pip setuptools wheel numpy
#   pip install qwen-tts fastapi 'uvicorn[standard]' soundfile
# Run:
#   uvicorn tts_server:app --host 0.0.0.0 --port 8002
import io
import torch
import soundfile as sf
from fastapi import FastAPI, Response
from pydantic import BaseModel
from qwen_tts import Qwen3TTSModel

tts = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    device_map="cuda:0", dtype=torch.bfloat16,
)

# Lab-assistant default voice — calm and precise.
DEFAULT_STYLE = ("Calm, clear, friendly lab assistant. Measured, reassuring pace, "
                 "speaks precisely like a careful demonstrator.")
app = FastAPI()


class Req(BaseModel):
    text: str
    style: str = DEFAULT_STYLE


@app.post("/speak")
def speak(r: Req):
    wavs, sr = tts.generate_voice_design(
        text=r.text, language="English", instruct=r.style,
    )
    audio = wavs[0]
    if hasattr(audio, "cpu"):            # VoiceDesign -> ndarray, Base -> tensor
        audio = audio.cpu().numpy()
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return Response(buf.getvalue(), media_type="audio/wav")
