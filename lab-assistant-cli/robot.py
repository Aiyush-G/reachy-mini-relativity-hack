"""Robot wrapper. Connects to whatever daemon is on localhost — the MuJoCo sim
(`mjpython -m reachy_mini.daemon.app.main --sim`) or a real Reachy Mini Lite
over USB. The same code drives both.

Set REACHY_BACKEND=mock to run without any daemon (prints only) — useful for
the voice/dashboard developers who don't have the sim open.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

BACKEND = os.environ.get("REACHY_BACKEND", "real").lower()

# Antenna poses (radians-ish, matching the SDK quickstart examples).
_PERKED = [0.6, 0.6]
_DROOPED = [-0.5, -0.5]
_NEUTRAL = [0.0, 0.0]


def say(text: str) -> None:
    """Speak aloud. Uses the macOS `say` command during sim dev; falls back to
    print. On the physical robot, swap this for the on-board speaker."""
    print(f"[reachy] {text}")
    if shutil.which("say"):
        subprocess.run(["say", text], check=False)


class Robot:
    def __init__(self) -> None:
        self._mini = None

    def __enter__(self) -> "Robot":
        if BACKEND != "mock":
            from reachy_mini import ReachyMini

            self._mini = ReachyMini().__enter__()
            self._mini.wake_up()
        else:
            print("[reachy] (mock backend — no robot)")
        return self

    def __exit__(self, *exc) -> None:
        if self._mini is not None:
            try:
                self._mini.goto_sleep()
            finally:
                self._mini.__exit__(*exc)

    def _pose(self, **kw):
        from reachy_mini.utils import create_head_pose

        return create_head_pose(mm=True, degrees=True, **kw)

    def _goto(self, *, head=None, antennas=None, duration=0.5, body_yaw=0.0) -> None:
        if self._mini is None:
            return
        self._mini.goto_target(
            head=head, antennas=antennas, duration=duration, body_yaw=body_yaw
        )

    def look_at_workspace(self) -> None:
        """Tilt the head down toward the bench."""
        self._goto(head=self._pose(pitch=20), duration=0.8)

    def express(self, state: str) -> None:
        """Map an emotional state to head/antenna/body motion."""
        if self._mini is None:
            print(f"[reachy] *{state}*")
            return

        if state == "listening":
            self._goto(head=self._pose(pitch=-8), antennas=_PERKED, duration=0.4)
        elif state == "thinking":
            self._goto(antennas=[0.6, -0.6], duration=0.25)
            self._goto(antennas=[-0.6, 0.6], duration=0.25)
            self._goto(antennas=_NEUTRAL, duration=0.25)
        elif state == "confirm":  # a nod
            self._goto(head=self._pose(pitch=18), antennas=[0.3, 0.3], duration=0.3)
            self._goto(head=self._pose(pitch=-4), duration=0.3)
            self._goto(head=self._pose(), duration=0.3)
        elif state == "hazard":  # a wary head shake
            self._goto(head=self._pose(yaw=20), antennas=_DROOPED, duration=0.3)
            self._goto(head=self._pose(yaw=-20), duration=0.3)
            self._goto(head=self._pose(), antennas=_NEUTRAL, duration=0.3)
        elif state == "done":  # celebrate
            self._goto(head=self._pose(z=15, pitch=-10), antennas=_PERKED,
                       duration=0.5, body_yaw=0.2)
            self._goto(antennas=[-0.6, 0.6], duration=0.3, body_yaw=-0.2)
            self._goto(head=self._pose(), antennas=_NEUTRAL, duration=0.5, body_yaw=0.0)
        else:  # idle / unknown
            self._goto(head=self._pose(), antennas=_NEUTRAL, duration=0.5)

    def idle_tick(self) -> None:
        """A small motion to look alive (used while a timer runs)."""
        if self._mini is None:
            return
        self._goto(head=self._pose(roll=4), duration=0.6)
        self._goto(head=self._pose(roll=-4), duration=0.6)
        self._goto(head=self._pose(), duration=0.4)
