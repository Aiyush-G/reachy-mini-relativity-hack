# Sharing the A100 endpoints with a teammate

The Brev A100's service ports (8000 LLM, 8002 TTS) are **firewalled** — you
can't hit the public IP directly. To let a teammate (e.g. Aiyush) run the app
from their own laptop, expose the two services as **public tunnel URLs**, then
they point the app at those URLs via env vars. No Brev CLI needed on their side.

## On the A100 (run in the Brev web console terminal / Open Notebook)

The instance can't be reached by `brev shell` from some machines, but the web
console terminal works. Make sure both services are running first:

- **LLM (Nemotron NIM)** on `:8000` — `docker run ... -p 8000:8000 ...` (NGC key set).
- **TTS (Qwen3-TTS)** on `:8002` — `uvicorn tts_server:app --host 0.0.0.0 --port 8002`.

Then open public tunnels (cloudflared needs no account; gives instant URLs):

```bash
# install cloudflared if needed
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# tunnel the LLM (leave running; prints a https://xxxx.trycloudflare.com URL)
./cloudflared tunnel --url http://localhost:8000 &

# tunnel the TTS (prints a second https://yyyy.trycloudflare.com URL)
./cloudflared tunnel --url http://localhost:8002 &
```

Copy the two `https://*.trycloudflare.com` URLs cloudflared prints.

## Send the teammate these two URLs

- **LLM_URL**  = the tunnel for port 8000
- **TTS_URL**  = the tunnel for port 8002

## On the teammate's laptop

```bash
git clone https://github.com/Aiyush-G/reachy-mini-relativity-hack
cd reachy-mini-relativity-hack/lab-assistant
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install "reachy-mini[mujoco]" openai requests fastapi "uvicorn[standard]" numpy

# Terminal 1 — sim daemon (macOS)
mjpython -m reachy_mini.daemon.app.main --sim

# Terminal 2 — point the app at the tunnel URLs (note the /v1 and /speak suffixes)
export OMNI_BASE="<LLM_URL>/v1"
export TTS_URL="<TTS_URL>/speak"
python main.py
# open http://localhost:8042 in Chrome, hold SPACE
```

## ⚠️ Security / cost
- A `trycloudflare.com` URL is public — anyone with the link can use your GPU
  and rack up cost while it's open. Keep the tunnels short-lived and **`Stop`
  the A100** in the Brev console when you're done.
- For the on-robot test with no GPU at all, use `lab-assistant-cli/` instead.
