import base64
import queue
import random
import threading
import time

import numpy as np
import requests
from openai import OpenAI
from starlette.requests import Request

from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.motion.recorded_move import RecordedMoves
from reachy_mini.utils import create_head_pose

# ── Endpoints (see slides 19–21) ─────────────────────────────────────────────
OMNI_BASE  = "http://localhost:8010/v1"          # Nemotron Omni (LLM) — port-forwarded
OMNI_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
TTS_URL    = "http://localhost:8002/speak"        # Qwen3-TTS
VOICE      = ("Calm, clear, friendly lab assistant. Measured, reassuring pace, "
              "speaks precisely like a careful demonstrator.")

SYSTEM = (
    "You are Reachy Mini, a calm and precise hands-free lab assistant guiding a "
    "person through a bench procedure. Their hands are busy, so keep replies short "
    "and clear: 1-2 short sentences, no markdown, no emoji. Stay on the current "
    "procedure; if asked something off-procedure, answer in one short sentence and "
    "steer back. Safety first: if a step is hot or sharp, remind them once, briefly. "
    "You guide and narrate — the person performs each action, never you."
)

# ── The procedure: a fixed state machine the LLM can't drift out of ───────────
# Demo procedure = make a cup of tea. Swap this list to run any other protocol.
TEA_PROTOCOL = [
    "Place a clean mug on the bench in front of you.",
    "Drop one tea bag into the mug.",
    "Carefully pour hot water into the mug, filling to about two centimetres from the top. It is hot — pour slowly.",
    "Let the tea steep for about sixty seconds. Say next when the time is up.",
    "Lift the tea bag out and set it aside on the spoon.",
    "Add milk to taste — a small splash is usual.",
    "Give it a gentle stir with the spoon.",
]
DONE_LINE = "Procedure complete. Your tea is ready — enjoy it. Well done."

# Recorded dances for the little end-of-protocol celebration.
FALLBACK_DANCES = ["happy", "victory", "wake_up", "curious"]


class LabAssistantApp(ReachyMiniApp):
    custom_app_url = "http://0.0.0.0:8042"

    def __init__(self):
        super().__init__()
        self.omni = OpenAI(base_url=OMNI_BASE, api_key="sk-nim")

        # Procedure state.
        self.step = -1                      # -1 = not started yet
        self.history = [{"role": "system", "content": SYSTEM}]
        self.motion_q = queue.Queue()

        # Optional dances library (best-effort — demo still works without it).
        try:
            self.dances = RecordedMoves("pollen-robotics/reachy-mini-dances-library")
            names = None
            for attr in ("names", "keys", "list_moves"):
                fn = getattr(self.dances, attr, None)
                if fn:
                    names = list(fn() if callable(fn) else fn)
                    break
            self._dance_names = names or FALLBACK_DANCES
            print(f"[init] {len(self._dance_names)} dances available")
        except Exception as e:
            print(f"[init] dances unavailable: {e}")
            self.dances, self._dance_names = None, []

        @self.settings_app.post("/chat")
        async def chat(request: Request):
            body = await request.json()
            text = (body.get("text") or "").strip()
            if not text:
                return {"reply": "(no transcript)", "audio_b64": ""}
            print(f"\nuser ▸ {text}")

            reply, motion = self._handle(text)
            print(f"robot ▸ {reply}")

            # Text -> speech.
            try:
                wav = requests.post(
                    TTS_URL, json={"text": reply, "style": VOICE}, timeout=30
                ).content
                audio_b64 = base64.b64encode(wav).decode()
            except Exception as e:
                print(f"(tts failed: {e})")
                audio_b64 = ""

            # Queue motion to play while/after the reply is spoken.
            spoken_secs = max(1.5, len(reply.split()) / 3.0)
            self.motion_q.put(("sway", spoken_secs))
            if motion == "nod":
                self.motion_q.put(("nod", None))
            elif motion == "celebrate" and self._dance_names:
                self.motion_q.put(("dance", random.choice(self._dance_names)))

            return {"reply": reply, "audio_b64": audio_b64}

    # ── Intent routing: protocol nav is deterministic; everything else -> LLM ──
    def _handle(self, text: str):
        """Return (reply_text, motion_tag)."""
        t = text.lower()

        def has(*words):
            return any(w in t for w in words)

        if has("start", "begin", "let's go", "lets go", "first step"):
            self.step = 0
            return (f"Starting the tea procedure. Step one. {self._step_text()}", "nod")

        if self.step == -1:
            # Not started and not a "start" command — let the LLM answer, gently.
            return (self._llm(text), None)

        if has("next", "done", "got it", "finished", "ready", "complete"):
            if self.step >= len(TEA_PROTOCOL) - 1:
                self.step = len(TEA_PROTOCOL)
                return (DONE_LINE, "celebrate")
            self.step += 1
            return (f"Step {self.step + 1}. {self._step_text()}", "nod")

        if has("repeat", "again", "what was that", "say that"):
            return (f"Step {self.step + 1}. {self._step_text()}", "nod")

        if has("back", "previous", "go back", "last step"):
            self.step = max(0, self.step - 1)
            return (f"Going back. Step {self.step + 1}. {self._step_text()}", "nod")

        if has("where", "status", "which step", "what step"):
            n = min(self.step + 1, len(TEA_PROTOCOL))
            return (f"You are on step {n} of {len(TEA_PROTOCOL)}. {self._step_text()}", None)

        # Off-script question — grounded LLM answer.
        return (self._llm(text), None)

    def _step_text(self) -> str:
        if 0 <= self.step < len(TEA_PROTOCOL):
            return TEA_PROTOCOL[self.step]
        return DONE_LINE

    def _llm(self, text: str) -> str:
        # Ground the model with where we are in the procedure.
        ctx = (
            f"Current procedure: making a cup of tea. "
            f"Current step ({min(self.step + 1, len(TEA_PROTOCOL))} of {len(TEA_PROTOCOL)}): "
            f"{self._step_text()}"
        )
        msgs = self.history + [
            {"role": "system", "content": ctx},
            {"role": "user", "content": text},
        ]
        try:
            resp = self.omni.chat.completions.create(
                model=OMNI_MODEL, messages=msgs, max_tokens=600,
            )
            msg = resp.choices[0].message
            reply = (msg.content or "").strip()
            if not reply:  # Nemotron reasoning model sometimes fills only `reasoning`
                rsn = (getattr(msg, "reasoning", None) or "").strip()
                parts = [p.strip() for p in rsn.split(".") if p.strip()]
                reply = (parts[-1] + ".") if parts else "Let's keep going."
        except Exception as e:
            print(f"(llm failed: {e})")
            reply = "I had trouble thinking just now — let's stick with the current step."

        self.history.append({"role": "user", "content": text})
        self.history.append({"role": "assistant", "content": reply})
        return reply

    # ── Motion worker ─────────────────────────────────────────────────────────
    def run(self, mini: ReachyMini, stop_event: threading.Event):
        mini.wake_up()
        print("✅ open http://localhost:8042 — hold SPACE to talk")
        while not stop_event.is_set():
            try:
                kind, p = self.motion_q.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                if kind == "sway":
                    self._sway(mini, duration=p)
                elif kind == "nod":
                    self._nod(mini)
                elif kind == "dance" and p and self.dances:
                    mini.play_move(self.dances.get(p), initial_goto_duration=0.6)
            except Exception as e:
                print(f"(motion '{kind}' failed: {e})")

    def _nod(self, mini: ReachyMini):
        """A clear confirmation nod."""
        for pitch in (15, -10, 0):
            mini.goto_target(head=create_head_pose(pitch=pitch, degrees=True), duration=0.25)

    def _sway(self, mini: ReachyMini, duration: float):
        """Gentle 'listening' sway while the reply is spoken."""
        t0 = time.time()
        while time.time() - t0 < duration:
            t = time.time() - t0
            yaw   = 8 * np.sin(t * 1.2)
            pitch = 3 * np.sin(t * 0.7)
            mini.set_target(head=create_head_pose(yaw=yaw, pitch=pitch, degrees=True))
            time.sleep(0.05)
        mini.goto_target(head=create_head_pose(), duration=0.25)


if __name__ == "__main__":
    app = LabAssistantApp()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
