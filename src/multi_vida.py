"""
Módulo integrado: MULTI-VIDA - Manejo de energía limitada y múltiples vidas

Extiende StateGraph para soportar reset de energía cuando llega a cero.
Permite que el planificador use múltiples vidas si es necesario.

Estructura de estado extendido:
  (position, key_shape, key_color, key_rotation, energy, lives, visited_rotators)
"""

from src.types import State, WorldState
from src.mapeador import StateGraph
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ExtendedState:
    """Estado extendido que incluye vidas restantes"""

    def __init__(self, position: Tuple[int, int], key_shape: int, key_color: int,
                 key_rotation: int, energy: int, lives: int = 3,
                 visited_rotators: Optional[set] = None):
        """
        Inicializar estado extendido

        Args:
            position: (row, col)
            key_shape, key_color, key_rotation: Estado de la llave
            energy: Energía actual (0-42)
            lives: Vidas restantes (1-3)
            visited_rotators: Set de rotadores visitados
        """
        self.position = position
        self.key_shape = key_shape
        self.key_color = key_color
        self.key_rotation = key_rotation
        self.energy = energy
        self.lives = lives
        self.visited_rotators = visited_rotators if visited_rotators else set()

    def to_state(self) -> State:
        """Convertir a State base (sin vidas)"""
        return State(
            position=self.position,
            key_shape=self.key_shape,
            key_color=self.key_color,
            key_rotation=self.key_rotation,
            energy=self.energy,
            visited_rotators=self.visited_rotators
        )

    def __eq__(self, other):
        if not isinstance(other, ExtendedState):
            return False
        return (self.position == other.position and
                self.key_shape == other.key_shape and
                self.key_color == other.key_color and
                self.key_rotation == other.key_rotation and
                self.energy == other.energy and
                self.lives == other.lives and
                self.visited_rotators == other.visited_rotators)

    def __hash__(self):
        return hash((self.position, self.key_shape, self.key_color,
                    self.key_rotation, self.energy, self.lives,
                    tuple(sorted(self.visited_rotators))))

    def __repr__(self):
        return (f"ExtState(pos={self.position}, key=({self.key_shape},"
                f"{self.key_color},{self.key_rotation}), energy={self.energy}, "
                f"lives={self.lives})")


class MultiLifeStateGraph(StateGraph):
    """
    StateGraph que soporta múltiples vidas con reset de energía.

    Cuando la energía llega a cero, se permite una transición "RESET" que:
    - Vuelve el jugador a la posición inicial
    - Restaura energía a 42
    - Decrementa vidas en 1
    - Mantiene el estado de la llave (persiste entre vidas)
    """

    def __init__(self, world: WorldState, initial_lives: int = 3, debug: bool = False):
        """
        Inicializar MultiLifeStateGraph

        Args:
            world: Estado del mundo
            initial_lives: Vidas iniciales (típicamente 3)
            debug: Si True, imprimir logs
        """
        super().__init__(world, debug)
        self.initial_lives = initial_lives
        self.initial_position = world.player_pos

        if debug:
            logger.debug(f"MultiLifeStateGraph initialized with {initial_lives} lives")

    def neighbors_with_lives(self, state: ExtendedState) -> List[Tuple[ExtendedState, int]]:
        """
        Generar vecinos incluyendo reset de vida

        Args:
            state: ExtendedState actual

        Returns:
            Lista de (next_state, cost) incluyendo transiciones de reset
        """
        neighbors = []

        # Si energía > 0, permitir movimientos normales
        if state.energy > 0:
            # Obtener vecinos del grafo base
            base_state = state.to_state()
            base_neighbors = super().neighbors(base_state)

            for next_base_state, cost in base_neighbors:
                # Crear ExtendedState manteniendo vidas
                next_extended = ExtendedState(
                    position=next_base_state.position,
                    key_shape=next_base_state.key_shape,
                    key_color=next_base_state.key_color,
                    key_rotation=next_base_state.key_rotation,
                    energy=next_base_state.energy,
                    lives=state.lives,
                    visited_rotators=next_base_state.visited_rotators
                )
                neighbors.append((next_extended, cost))

        # Si energía = 0 y quedan vidas, permitir reset
        if state.energy == 0 and state.lives > 1:
            reset_state = ExtendedState(
                position=self.initial_position,
                key_shape=state.key_shape,  # Mantener key state
                key_color=state.key_color,
                key_rotation=state.key_rotation,
                energy=42,  # Reset energía
                lives=state.lives - 1,  # Usar una vida
                visited_rotators=state.visited_rotators  # Mantener visitados
            )
            neighbors.append((reset_state, 0))  # Reset no cuesta energía de transición

            if self.debug:
                logger.debug(f"Reset transition available: {state.lives-1} lives left")

        return neighbors

    def is_goal_with_lives(self, state: ExtendedState) -> bool:
        """
        Verificar si es goal con extensión multi-vida

        Args:
            state: ExtendedState a verificar

        Returns:
            True si está en puerta con llave correcta y energía > 0
        """
        # Convertir a State base para verificar goal
        base_state = state.to_state()

        # Goal requiere: estar en puerta con llave correcta Y tener energía
        if state.energy <= 0:
            return False

        return super().is_goal(base_state)

    def can_reach_goal(self, start_state: ExtendedState,
                       goal_position: Tuple[int, int]) -> bool:
        """
        Verificar si es posible alcanzar goal desde start (admisibilidad de búsqueda)

        Args:
            start_state: Estado inicial con vidas
            goal_position: Posición de puerta

        Returns:
            True si hay al menos una ruta viable
        """
        # Goal es viable si:
        # 1. Tenemos vidas (pueden no ser suficientes, pero la búsqueda lo determinará)
        # 2. O hay al menos una ruta sin usar energía (imposible pero verificamos)

        if start_state.lives <= 0:
            return False

        return True  # Simplificación: confiamos en que A* determinará viabilidad


def create_multi_vida_graph(world: WorldState, initial_lives: int = 3,
                            debug: bool = False) -> MultiLifeStateGraph:
    """Factory para crear MultiLifeStateGraph"""
    return MultiLifeStateGraph(world, initial_lives, debug)
