"""Connects to the local Reachy Mini simulation and runs a quick motion test.

Run the sim daemon first (in another terminal, with the venv activated):
    mjpython -m reachy_mini.daemon.app.main --sim
Then, in this terminal (venv activated):
    python sim_hello.py
"""

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def main() -> None:
    with ReachyMini() as mini:
        print("Connected to simulation!")

        print("Moving head...")
        mini.goto_target(
            head=create_head_pose(z=20, roll=10, mm=True, degrees=True),
            duration=1.0,
        )

        print("Wiggling antennas...")
        mini.goto_target(antennas=[0.6, -0.6], duration=0.3)
        mini.goto_target(antennas=[-0.6, 0.6], duration=0.3)

        print("Returning to rest.")
        mini.goto_target(head=create_head_pose(), antennas=[0, 0], duration=1.0)


if __name__ == "__main__":
    main()
