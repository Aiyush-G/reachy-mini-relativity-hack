# Lab Assistant — Runbook

Brev A100 is already launched (named `reachy-workshop`). Local deps + app files
are already created. Follow these phases in order.

## Phase A — A100 services (your Brev shell)  ~15 min

```bash
brev shell reachy-workshop
```

### 1. LLM — Nemotron-3-Nano-Omni on port 8000
Follow the deploy guide and map the host port to 8000. Export your NGC key first:
```bash
export NGC_API_KEY=nvapi-...          # from build.nvidia.com
# docker run ... -p 8000:8000 ...     # exact command from the model's deploy tab:
# build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
```

### 2. TTS — Qwen3-TTS on port 8002
```bash
sudo apt-get update && sudo apt-get install -y sox libsox-dev
pip install -U pip setuptools wheel numpy
pip install qwen-tts fastapi 'uvicorn[standard]' soundfile
# copy server/tts_server.py up to the A100 (or paste it), then:
uvicorn tts_server:app --host 0.0.0.0 --port 8002
```

## Phase B — Port-forward to your laptop  (2 terminals)

```bash
brev port-forward reachy-workshop --port 8010:8000  &   # LLM  (NOTE: 8010 local!)
brev port-forward reachy-workshop --port 8002:8002  &   # TTS
```
⚠️ LLM is on **localhost:8010**, not 8000 — the Reachy daemon owns 8000.

## Phase C — Smoke-test both services (laptop)

```bash
# from the lab_assistant/ folder:
./smoke_test.sh
```

## Phase D — Run it (3 terminals on your laptop)

**Terminal 1 — sim daemon (macOS):**
```bash
mjpython -m reachy_mini.daemon.app.main --sim
```

**Terminal 2 — the app:**
```bash
cd lab_assistant
export HF_TOKEN=hf_...                # for the dances library
../.venv/bin/python main.py           # or: source ../.venv/bin/activate; python main.py
```

**Terminal 3 — browser:** open http://localhost:8042 in **Chrome on macOS**,
hold SPACE, say "start the tea protocol".

## Phase E — Swap to the real robot
Close the MuJoCo window, plug in Reachy Mini Lite (USB), then:
```bash
REACHY_MINI_BACKEND=real ../.venv/bin/python main.py
```

## Demo script
- "Start the tea protocol"
- "next"  (repeat through the steps)
- "repeat" / "back" / "where am I"
- Off-script: "how much milk should I use?", "why does it steep?"

## Troubleshooting
- HTTP 403 on /ws/sdk  -> LLM is on :8000 not :8010, re-do the forward.
- Zombie on 8000:      `lsof -ti:8000 | xargs kill -9`
- (silent) in log      -> Chrome on macOS only; click Allow on mic prompt.
- content: null        -> reasoning model; main.py already falls back to `reasoning`.
- Sim crash / GStreamer-> still in conda base; `conda deactivate` and use the uv venv.
