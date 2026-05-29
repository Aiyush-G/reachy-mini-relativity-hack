"""Reachy Mini lab-assistant — hands-free SOP runner (tea demo).

Run the sim first (separate terminal, venv active):
    mjpython -m reachy_mini.daemon.app.main --sim
Then:
    python main.py

Commands at each step:  [Enter]=next  r=repeat  b=back  q=quit
(The input() call is the seam where voice/STT plugs in later.)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from protocol import Protocol
from robot import Robot, say

STATE_FILE = Path("state.json")


def write_state(**fields) -> None:
    STATE_FILE.write_text(json.dumps(fields, indent=2))


def run_timer(robot: Robot, seconds: int, base_state: dict) -> None:
    say(f"Steeping for {seconds} seconds. I'll let you know when it's ready.")
    for remaining in range(seconds, 0, -1):
        write_state(**base_state, status="steeping", timer_remaining=remaining)
        if remaining == 10:
            say("Ten seconds left.")
        if remaining % 10 == 0:
            robot.idle_tick()
        else:
            time.sleep(1)
    say("Time's up.")
    robot.express("done")


def get_command() -> str:
    raw = input("  [Enter]=next  r=repeat  b=back  q=quit > ").strip().lower()
    return {"": "next", "r": "repeat", "b": "back", "q": "quit"}.get(raw, "next")


def main() -> None:
    protocol = Protocol.load("protocol.yaml")

    with Robot() as robot:
        robot.express("listening")
        group = input("Which lab group is running this protocol? > ").strip() or "Unknown"
        say(f"Welcome, {group}. Today's protocol: {protocol.name}.")

        while not protocol.is_done:
            step = protocol.current
            base = {
                "group": group,
                "protocol": protocol.name,
                "step_index": protocol.index + 1,
                "total_steps": protocol.total,
                "step_text": step.say,
                "hazard": step.hazard,
            }
            write_state(**base, status="running", timer_remaining=None)

            robot.look_at_workspace()
            if step.hazard:
                robot.express("hazard")
                say(step.hazard)
            say(step.say)

            if step.timer_seconds:
                run_timer(robot, step.timer_seconds, base)

            robot.express("listening")
            cmd = get_command()
            write_state(**base, status="running", timer_remaining=None, last_heard=cmd)

            if cmd == "quit":
                say("Stopping the protocol.")
                break
            elif cmd == "repeat":
                continue
            elif cmd == "back":
                protocol.back()
            else:  # next
                robot.express("confirm")
                protocol.advance()

        if protocol.is_done:
            write_state(group=group, protocol=protocol.name,
                        step_index=protocol.total, total_steps=protocol.total,
                        step_text="Complete", hazard=None,
                        status="done", timer_remaining=None)
            robot.express("done")
            say("Protocol complete. Enjoy your tea.")


if __name__ == "__main__":
    main()
