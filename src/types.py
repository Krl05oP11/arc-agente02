"""Tipos y estructuras de datos compartidas"""

from dataclasses import dataclass, field
from typing import Set, List, Tuple, Optional, Dict, Any
import numpy as np


@dataclass
class KeyState:
    """Estado de la llave: forma, color, rotación"""
    shape_id: int
    color_id: int
    rotation_id: int

    def __hash__(self):
        return hash((self.shape_id, self.color_id, self.rotation_id))

    def __eq__(self, other):
        if not isinstance(other, KeyState):
            return False
        return (self.shape_id == other.shape_id and
                self.color_id == other.color_id and
                self.rotation_id == other.rotation_id)


@dataclass
class Door:
    """Puerta de salida"""
    position: Tuple[int, int]
    required_key: KeyState


@dataclass
class Rotator:
    """Rotador que transforma la llave"""
    position: Tuple[int, int]
    rotator_type: str  # 'SHAPE', 'COLOR', 'ROT'
    rotator_id: int    # ID único


@dataclass
class Teleporter:
    """Teletransportador"""
    source: Tuple[int, int]
    destination: Tuple[int, int]


@dataclass
class WorldState:
    """Estado del mundo (parsed from grid)"""
    player_pos: Tuple[int, int]
    walls: Set[Tuple[int, int]]
    doors: List[Door]
    rotators: List[Rotator]
    refills: List[Tuple[int, int]]
    teleporters: List[Teleporter]
    key_state: KeyState
    energy: int = 42


@dataclass
class State:
    """Estado unificado para búsqueda A*"""
    position: Tuple[int, int]
    key_shape: int
    key_color: int
    key_rotation: int
    energy: int
    visited_rotators: Set[int] = field(default_factory=set)

    def __hash__(self):
        return hash((self.position, self.key_shape, self.key_color,
                     self.key_rotation, self.energy))

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return (self.position == other.position and
                self.key_shape == other.key_shape and
                self.key_color == other.key_color and
                self.key_rotation == other.key_rotation and
                self.energy == other.energy)

    def __lt__(self, other):
        """Para PriorityQueue"""
        return self.energy > other.energy  # Inverted: higher energy = lower priority


@dataclass
class Plan:
    """Plan de solución"""
    actions: List[Tuple[int, int]]  # Secuencia de posiciones
    cost: int  # Energía total gastada
    valid: bool  # ¿Satisface la regla?


@dataclass
class Rule:
    """Regla de juego inferida"""
    dsl_program: str  # Descripción legible
    constraint_list: List[str] = field(default_factory=list)
    rotator_order: List[int] = field(default_factory=list)
    prerequisites: Dict[Any, Set[Any]] = field(default_factory=dict)


@dataclass
class Example:
    """Ejemplo de entrenamiento"""
    input_grid: np.ndarray
    solution_path: List[Tuple[int, int]]
    world_state: Optional[WorldState] = None


class Solution:
    """Solución final"""
    def __init__(self, output_grid: np.ndarray, plan: Plan, rule: Rule):
        self.output_grid = output_grid
        self.plan = plan
        self.rule = rule

    def is_valid(self) -> bool:
        return self.plan.valid
