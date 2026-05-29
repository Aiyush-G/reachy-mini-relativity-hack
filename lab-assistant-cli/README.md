# lab-assistant-cli

Terminal-driven version of the Reachy Mini lab assistant. No GPU, no LLM —
a data-driven protocol runner with voice output via the macOS `say` command.
The `input()` call in `main.py` is the seam where real STT plugs in later.

## Files
- `protocol.yaml` — the procedure (steps, `hazard`, `timer_seconds`). Swap it for any SOP.
- `protocol.py`  — `Protocol`/`Step` model that loads the YAML.
- `robot.py`     — robot wrapper; antenna/head **expressions** (listening, thinking, confirm, hazard, done) + a `mock` backend.
- `main.py`      — runner: asks the lab group, walks the steps, writes `state.json`.
- `sim_hello.py` — quick sim motion smoke test.

## Run

```bash
# Terminal 1 — sim daemon (macOS); or plug in a real Reachy Mini Lite.
mjpython -m reachy_mini.daemon.app.main --sim

# Terminal 2
python main.py            # connects to the daemon
```

Commands at each step: `Enter` = next · `r` = repeat · `b` = back · `q` = quit.

## Backends (set via env var)
- `REACHY_BACKEND=real` (default) — sim daemon or real robot over USB.
- `REACHY_BACKEND=mock` — no daemon needed; prints motions only. Good for
  developing the voice/dashboard layer without the sim open.

`state.json` is written each step (current group, step, hazard, timer) — a seam
for a live dashboard. It's generated at runtime and git-ignored.
