from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np


class MemoryType(Enum):
    POINT = 0
    MOVEMENT = 1


class MotionType(Enum):
    JOINT = 0
    LINEAR = 1


@dataclass
class MemoryEntry:
    type: MemoryType
    value: np.ndarray  # [x, y, z, r] for POINTS, [j1, j2, j3, j4] for MOVEMENTS
    motion_type: MotionType
    valid: bool = True

    def serialize(self):
        return {
            "Type": self.type.name,
            "Value": [float(el) for el in list(self.value)],
            "Motion Type": self.motion_type.name,
            "Valid": self.valid,
        }

    @staticmethod
    def from_dict(entry: dict):
        return MemoryEntry(
            MemoryType[entry["Type"]],
            np.array(entry["Value"]),
            MotionType[entry["Motion Type"]],
            entry["Valid"],
        )


@dataclass
class FeedEntry:
    timestamp: datetime
    message: str
    source: str

    def serialize(self):
        return {
            "Timestamp": self.timestamp.strftime("%H:%M:%ST%d.%m.%Y"),
            "Message": self.message,
            "Source": self.source,
        }

    @staticmethod
    def from_dict(entry: dict):
        return FeedEntry(
            datetime.strptime(entry["Timestamp"], "%H:%M:%ST%d.%m.%Y"),
            entry["Message"],
            entry["Source"],
        )


@dataclass
class Keymap:
    cross_pressed: callable
    square_pressed: callable
    triangle_pressed: callable
    circle_pressed: callable
    r1_changed: callable
    l1_changed: callable
    r2_changed: callable
    l2_changed: callable
    left_joystick_changed: callable
    right_joystick_changed: callable
    dpad_up: callable
    dpad_down: callable
    dpad_left: callable
    dpad_right: callable
