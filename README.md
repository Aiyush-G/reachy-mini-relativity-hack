# Reachy Mini — Lab Assistant 🌻

A hands-free **lab assistant** for [Reachy Mini](https://pollen-robotics.github.io/reachy_mini/).
It onboards a lab group and then walks a person through a bench procedure **by voice**,
so their hands stay on the bench. Reachy reads each step aloud, waits for a command,
nods to confirm, warns on hazards, and answers off-script questions.

Reachy Mini has no hands — so it doesn't perform the procedure. **You** do the steps;
Reachy runs the protocol. This is the *Code-as-Policy* split: the LLM reasons and talks,
scripted code owns state and motion.

**Demo procedure:** making a cup of tea (premade tea, hot water, milk).

## Two implementations

| Folder | Flavour | Input | Brain / Voice |
|--------|---------|-------|---------------|
| [`lab-assistant/`](lab-assistant/) | Browser app (`ReachyMiniApp` + FastAPI) | Hold-SPACE PTT in Chrome (Web Speech STT) | Nemotron-3-Nano-Omni (LLM) + Qwen3-TTS, self-hosted on a Brev A100 |
| [`lab-assistant-cli/`](lab-assistant-cli/) | Terminal runner | Keyboard (`Enter`/`r`/`b`/`q`) — the seam where voice plugs in | macOS `say`; YAML-driven protocol, no GPU needed |
| [`workout-buddy/`](workout-buddy/) | Workshop example (CrossFit coach) | — | — |

The CLI version adds a **data-driven `protocol.yaml`** (swap it for any SOP),
**hazard warnings**, **antenna gestures**, a **mock backend** for no-robot dev,
and a `state.json` seam for a live dashboard. The browser version adds **real STT/TTS**
and an **LLM** for free-form questions. They share the same Reachy Mini SDK.

## Quick start

Both connect to the same daemon — the MuJoCo sim or a real robot over USB.

```bash
# Terminal 1 — sim daemon (macOS)
mjpython -m reachy_mini.daemon.app.main --sim
```

**Browser app:** see [`lab-assistant/RUNBOOK.md`](lab-assistant/RUNBOOK.md) (needs the Brev A100 services + port-forward), then `python main.py` and open http://localhost:8042.

**CLI app:** see [`lab-assistant-cli/README.md`](lab-assistant-cli/README.md) — `python main.py`, no GPU needed.

Swap sim → real robot with one env var (`REACHY_MINI_BACKEND=real`, or `REACHY_BACKEND=real` for the CLI). Same code, real motors.

## Voice / command vocabulary
`start` · `next` / done · `repeat` · `back` · `where am I` — plus free-form questions
(browser app) answered by the LLM, grounded with the current step.
