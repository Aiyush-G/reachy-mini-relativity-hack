"""Data-driven protocol model. Swap protocol.yaml for any lab SOP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Step:
    say: str
    hazard: str | None = None
    timer_seconds: int | None = None
    verify: str | None = None


@dataclass
class Protocol:
    name: str
    steps: list[Step]
    index: int = 0

    @classmethod
    def load(cls, path: str | Path) -> "Protocol":
        data = yaml.safe_load(Path(path).read_text())
        return cls(name=data["protocol"], steps=[Step(**s) for s in data["steps"]])

    @property
    def current(self) -> Step:
        return self.steps[self.index]

    @property
    def total(self) -> int:
        return len(self.steps)

    @property
    def is_done(self) -> bool:
        return self.index >= self.total

    def advance(self) -> None:
        self.index += 1

    def back(self) -> None:
        self.index = max(0, self.index - 1)
