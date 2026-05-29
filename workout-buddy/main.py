import base64, queue, random, threading, time
import numpy as np, requests
from openai import OpenAI
from starlette.requests import Request
from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.motion.recorded_move import RecordedMoves
from reachy_mini.utils import create_head_pose

OMNI_BASE  = "http://localhost:8010/v1"
OMNI_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
TTS_URL    = "http://localhost:8002/speak"
COACH      = "Speak like a hyped CrossFit coach."

SYSTEM = ("You are Reachy Mini — a hyped CrossFit coach in a 6-inch robot body. "
          "Reply in 1–2 short energetic sentences. No emoji, no markdown.")

DANCE_NAMES = ["happy","sad","robot","victory","disco","curious","sleepy","wake_up","surprise"]


class WorkoutBuddyApp(ReachyMiniApp):
    custom_app_url = "http://0.0.0.0:8042"

    def __init__(self):
        super().__init__()
        self.omni = OpenAI(base_url=OMNI_BASE, api_key="sk-nim")
        try:
            self.dances = RecordedMoves("pollen-robotics/reachy-mini-dances-library")
            for attr in ("names","keys","list_moves"):
                fn = getattr(self.dances, attr, None)
                if fn:
                    self._dance_names = list(fn() if callable(fn) else fn); break
            else:
                self._dance_names = DANCE_NAMES
            print(f"[init] {len(self._dance_names)} dances available")
        except Exception as e:
            print(f"[init] dances unavailable: {e}")
            self.dances, self._dance_names = None, []

        self.history  = [{"role": "system", "content": SYSTEM}]
        self.motion_q = queue.Queue()

        @self.settings_app.post("/chat")
        async def chat(request: Request):
            body = await request.json()
            text = (body.get("text") or "").strip()
            if not text:
                return {"reply": "(no transcript)", "audio_b64": ""}
            print(f"\nuser ▸ {text}")
            self.history.append({"role":"user", "content": text})
            reply = self._llm_text()
            print(f"robot ▸ {reply}")

            wav = requests.post(TTS_URL,
                json={"text": reply, "style": COACH}, timeout=30).content

            # Programmed motion: slow head sway while speaking, then a random dance.
            spoken_secs = max(1.5, len(reply.split()) / 3.0)
            self.motion_q.put(("sway", spoken_secs))
            if self._dance_names:
                self.motion_q.put(("dance", random.choice(self._dance_names)))

            return {"reply": reply, "audio_b64": base64.b64encode(wav).decode()}

    def _llm_text(self) -> str:
        resp = self.omni.chat.completions.create(
            model=OMNI_MODEL, messages=self.history, max_tokens=600,
        )
        msg = resp.choices[0].message
        text = (msg.content or "").strip()
        if not text:                               # Nemotron sometimes only fills `reasoning`
            rsn = (getattr(msg, "reasoning", None) or "").strip()
            parts = [p.strip() for p in rsn.split(".") if p.strip()]
            text = (parts[-1] + ".") if parts else "Let's go!"
        self.history.append({"role":"assistant", "content": text})
        return text

    def run(self, mini: ReachyMini, stop_event: threading.Event):
        mini.wake_up()
        print("✅ open http://localhost:8042 — hold SPACE to talk")
        while not stop_event.is_set():
            try: kind, p = self.motion_q.get(timeout=0.1)
            except queue.Empty: continue
            try:
                if kind == "sway":
                    self._sway_head(mini, duration=p)
                elif kind == "dance" and p and self.dances:
                    mini.play_move(self.dances.get(p), initial_goto_duration=0.6)
            except Exception as e:
                print(f"(motion '{kind}' failed: {e})")

    def _sway_head(self, mini: ReachyMini, duration: float):
        """Slow head sway while the reply is being spoken."""
        t0 = time.time()
        while time.time() - t0 < duration:
            t = time.time() - t0
            yaw   = 10 * np.sin(t * 1.2)
            pitch = 4  * np.sin(t * 0.7)
            mini.set_target(head=create_head_pose(yaw=yaw, pitch=pitch, degrees=True))
            time.sleep(0.05)
        mini.goto_target(head=create_head_pose(), duration=0.25)


if __name__ == "__main__":
    app = WorkoutBuddyApp()
    try:    app.wrapped_run()
    except KeyboardInterrupt: app.stop()