"""
Módulo 2: MAPEADOR - WorldState → StateGraph

Construye un grafo de búsqueda donde cada nodo representa un estado completo:
(position, key_state, energy, visited_rotators)

Este grafo es la base para A* pathfinding en Fase 2.
"""

from src.types import State, WorldState
from typing import List, Tuple, Optional, Dict, Set
import logging

logger = logging.getLogger(__name__)


class StateGraph:
    """
    Grafo de búsqueda con nodos de estado unificado.

    Un nodo es: (position, key_shape, key_color, key_rotation, energy, visited_rotators)

    Las aristas representan acciones válidas (movimientos, rotator attacks, etc.)
    """

    def __init__(self, world: WorldState, debug: bool = False):
        """
        Inicializar el StateGraph

        Args:
            world: Estado del mundo (paredes, rotadores, doors, etc.)
            debug: Si True, imprimir logs detallados
        """
        self.world = world
        self.debug = debug

        # Pre-compute lookup tables para acceso rápido
        self._walls = world.walls
        self._rotators_by_pos = {rot.position: rot for rot in world.rotators}
        self._doors = world.doors
        self._refills_by_pos = {pos: True for pos in world.refills}
        self._teleporters = {tp.source: tp.destination for tp in world.teleporters}

        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug(f"StateGraph initialized: walls={len(self._walls)}, "
                        f"rotators={len(self._rotators_by_pos)}, "
                        f"teleporters={len(self._teleporters)}")

    def neighbors(self, state: State) -> List[Tuple[State, int]]:
        """
        Retornar los estados alcanzables desde el estado actual.

        Para cada dirección (UP, DOWN, LEFT, RIGHT):
        1. Calcular next_pos = move(state.pos, direction)
        2. Si es pared → skip
        3. Si es rotador → generar state con key transformada
        4. Si es teleporter → generar state en destination
        5. Si es puerta → si key matches, generar state (permite pasar)
        6. Si es refill → generar state con energy=42
        7. Si es piso normal → generar state

        Cada transición cuesta 1 energía y gasta 1 energía

        Args:
            state: Estado actual

        Returns:
            Lista de (next_state, cost) pares
        """
        neighbors = []

        # Intentar movimiento en 4 direcciones
        for direction, (dr, dc) in [
            ("UP", (-5, 0)),
            ("DOWN", (5, 0)),
            ("LEFT", (0, -5)),
            ("RIGHT", (0, 5)),
        ]:
            next_pos = (state.position[0] + dr, state.position[1] + dc)

            # Validación de límites (grid 64×64)
            if not (0 <= next_pos[0] < 64 and 0 <= next_pos[1] < 64):
                continue

            # Validación de paredes
            if next_pos in self._walls:
                if self.debug:
                    logger.debug(f"  Wall at {next_pos}")
                continue

            # Costo base de energía por movimiento
            energy_cost = 1

            # Verificar el tipo de celda en destination
            next_key_shape = state.key_shape
            next_key_color = state.key_color
            next_key_rotation = state.key_rotation
            next_visited = state.visited_rotators.copy() if state.visited_rotators else set()

            # Caso 1: Rotator (transforma la llave)
            if next_pos in self._rotators_by_pos:
                rotator = self._rotators_by_pos[next_pos]

                if rotator.rotator_type == "SHAPE":
                    next_key_shape = (next_key_shape + 1) % 4  # Asumir 4 formas
                elif rotator.rotator_type == "COLOR":
                    next_key_color = (next_key_color + 1) % 4  # Asumir 4 colores
                elif rotator.rotator_type == "ROT":
                    next_key_rotation = (next_key_rotation + 1) % 4  # 0, 1, 2, 3 = 0°, 90°, 180°, 270°

                # Registrar que visitamos este rotador
                next_visited.add(rotator.rotator_id)

                if self.debug:
                    logger.debug(f"  Rotator {rotator.rotator_id} at {next_pos} "
                                f"transforms key to ({next_key_shape},{next_key_color},{next_key_rotation})")

            # Caso 2: Teleporter (salto instantáneo al destino)
            if next_pos in self._teleporters:
                teleport_dest = self._teleporters[next_pos]
                # Si el destino es pared, no se puede teletransportar
                if teleport_dest not in self._walls:
                    next_pos = teleport_dest
                    if self.debug:
                        logger.debug(f"  Teleporter from {next_pos} to {teleport_dest}")
                else:
                    if self.debug:
                        logger.debug(f"  Teleporter destination {teleport_dest} is wall, skip")
                    continue

            # Caso 3: Refill (restaura energía)
            next_energy = state.energy - energy_cost
            if next_pos in self._refills_by_pos:
                next_energy = 42  # Máxima energía
                if self.debug:
                    logger.debug(f"  Refill at {next_pos}, energy restored to 42")

            # Caso 4: Door (validar key match)
            can_pass_door = True
            for door in self._doors:
                if door.position == next_pos:
                    # Verificar que la llave actual coincide con el requisito
                    required = door.required_key
                    if (next_key_shape != required.shape_id or
                        next_key_color != required.color_id or
                        next_key_rotation != required.rotation_id):
                        can_pass_door = False
                        if self.debug:
                            logger.debug(f"  Door at {next_pos} requires key "
                                        f"({required.shape_id},{required.color_id},{required.rotation_id}) "
                                        f"but have ({next_key_shape},{next_key_color},{next_key_rotation})")
                        break

            if not can_pass_door:
                continue

            # Crear nuevo estado
            next_state = State(
                position=next_pos,
                key_shape=next_key_shape,
                key_color=next_key_color,
                key_rotation=next_key_rotation,
                energy=next_energy,
                visited_rotators=next_visited
            )

            # Validar que tenemos energía para el movimiento
            if next_energy < 0:
                if self.debug:
                    logger.debug(f"  No energy to move to {next_pos}")
                continue

            neighbors.append((next_state, energy_cost))

        return neighbors

    def is_goal(self, state: State) -> bool:
        """
        Verificar si un estado es goal (en puerta con key correcta)

        Args:
            state: Estado a verificar

        Returns:
            True si el estado es goal
        """
        for door in self._doors:
            if state.position == door.position:
                required = door.required_key
                if (state.key_shape == required.shape_id and
                    state.key_color == required.color_id and
                    state.key_rotation == required.rotation_id):
                    return True
        return False

    def heuristic(self, state: State, goal_key: Tuple[int, int, int]) -> int:
        """
        Heurística admisible para A*.

        Combina:
        1. Manhattan distance a la puerta más cercana
        2. Costo estimado para transformar la llave al estado requerido

        Args:
            state: Estado actual
            goal_key: (shape_id, color_id, rotation_id) requerido

        Returns:
            Estimación de costo restante
        """
        # Encontrar puerta más cercana
        min_dist = float('inf')
        for door in self._doors:
            dist = abs(state.position[0] - door.position[0]) + \
                   abs(state.position[1] - door.position[1])
            min_dist = min(min_dist, dist)

        # Normalizar a pasos de 5 celdas
        manhattan_cost = max(1, min_dist // 5)

        # Costo estimado para key transformation
        # Simplificación: asumir que necesitamos 1 step por dimensión diferente
        key_cost = 0
        if state.key_shape != goal_key[0]:
            key_cost += 1
        if state.key_color != goal_key[1]:
            key_cost += 1
        if state.key_rotation != goal_key[2]:
            key_cost += 1

        return manhattan_cost + key_cost


def create_state_graph(world: WorldState, debug: bool = False) -> StateGraph:
    """Factory para crear un StateGraph"""
    return StateGraph(world, debug=debug)
