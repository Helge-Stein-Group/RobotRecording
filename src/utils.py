from enum import Enum
from dataclasses import dataclass

import numpy as np


class MemoryType(Enum):
    POINT = 0
    MOVEMENT = 1


class CoordinateSystem(Enum):
    JOINT = 0
    WORLD = 1


@dataclass
class MemoryEntry:
    type: MemoryType
    value: np.ndarray
    coordinate_system: CoordinateSystem

    def serialize(self):
        return {
            "type": self.type.name,
            "value": list(self.value),
            "coordinate_system": self.coordinate_system.name,
        }

    @staticmethod
    def from_dict(entry: dict):
        return MemoryEntry(
            MemoryType[entry["type"]],
            np.array(entry["value"]),
            CoordinateSystem[entry["coordinate_system"]],
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
