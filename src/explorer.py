"""
Módulo: EXPLORER - Exploración bajo visibilidad parcial (L7)

Permite al agente:
- Explorar el mundo descubriendo nuevas celdas
- Mantener memoria de lo descubierto
- Identificar fronteras de exploración
- Detectar obstáculos y objetos nuevos
- Replantificar basado en nuevos descubrimientos
"""

from src.types import State, WorldState, Rotator, Door, KeyState
from typing import Set, Tuple, Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExploredArea:
    """Representa el área explorada del mundo"""

    def __init__(self, initial_world: Optional[WorldState] = None):
        """
        Inicializar área explorada

        Args:
            initial_world: Mundo inicial (pueden haber partes no exploradas)
        """
        self.discovered_cells: Set[Tuple[int, int]] = set()
        self.walls: Set[Tuple[int, int]] = set()
        self.rotators: Dict[int, Rotator] = {}
        self.doors: List[Door] = []
        self.refills: Set[Tuple[int, int]] = set()
        self.teleporters: Set[Tuple[int, int]] = set()

        # Registrar datos iniciales si existen
        if initial_world:
            self.walls = set(initial_world.walls)
            for rot in initial_world.rotators:
                self.rotators[rot.rotator_id] = rot
            self.doors = initial_world.doors.copy()
            self.refills = set(initial_world.refills)
            self.teleporters = set(initial_world.teleporters)

            # Marcar como descubiertas
            self.discovered_cells.add(initial_world.player_pos)
            for wall in self.walls:
                self.discovered_cells.add(wall)

    def discover_cell(self, pos: Tuple[int, int], cell_type: str = "floor"):
        """
        Registrar descubrimiento de celda

        Args:
            pos: Posición
            cell_type: "floor", "wall", "rotator", "door", "refill", "teleporter"
        """
        self.discovered_cells.add(pos)

        if cell_type == "wall":
            self.walls.add(pos)
        elif cell_type == "refill":
            self.refills.add(pos)
        elif cell_type == "teleporter":
            self.teleporters.add(pos)

    def discover_rotator(self, rotator: Rotator):
        """Registrar descubrimiento de rotador"""
        self.rotators[rotator.rotator_id] = rotator
        self.discovered_cells.add(rotator.position)

    def discover_door(self, door: Door):
        """Registrar descubrimiento de puerta"""
        if door not in self.doors:
            self.doors.append(door)
        self.discovered_cells.add(door.position)

    def get_unknown_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Obtener celdas adyacentes no exploradas

        Args:
            pos: Posición central

        Returns:
            Lista de posiciones adyacentes no descubiertas
        """
        unknown = []
        row, col = pos

        for dr, dc in [(0, 5), (5, 0), (0, -5), (-5, 0)]:  # Movimiento en grid 5-cell
            nr, nc = row + dr, col + dc

            if 0 <= nr < 64 and 0 <= nc < 64:
                if (nr, nc) not in self.discovered_cells:
                    unknown.append((nr, nc))

        return unknown

    def get_exploration_frontier(self) -> List[Tuple[int, int]]:
        """
        Obtener frontera de exploración (celdas conocidas adyacentes a desconocidas)

        Returns:
            Lista de posiciones en la frontera
        """
        frontier = set()

        for pos in self.discovered_cells:
            neighbors = self.get_unknown_neighbors(pos)
            if neighbors:
                frontier.add(pos)

        return list(frontier)

    def is_cell_explored(self, pos: Tuple[int, int]) -> bool:
        """Verificar si una celda fue explorada"""
        return pos in self.discovered_cells

    def __repr__(self):
        return (f"ExploredArea(discovered={len(self.discovered_cells)}, "
                f"walls={len(self.walls)}, rotators={len(self.rotators)}, "
                f"doors={len(self.doors)})")


class ExplorationStrategy:
    """Estrategia de exploración"""

    BREADTH_FIRST = "breadth_first"  # Expandir frontera uniformemente
    DEPTH_FIRST = "depth_first"      # Ir lo más lejos posible
    GOAL_ORIENTED = "goal_oriented"  # Explorar hacia objetivos conocidos

    def __init__(self, strategy_type: str = BREADTH_FIRST):
        """
        Inicializar estrategia

        Args:
            strategy_type: Tipo de estrategia
        """
        self.strategy = strategy_type

    def choose_next_exploration_target(self, current_pos: Tuple[int, int],
                                      explored_area: ExploredArea,
                                      known_goal: Optional[Tuple[int, int]] = None
                                      ) -> Optional[Tuple[int, int]]:
        """
        Elegir siguiente objetivo de exploración

        Args:
            current_pos: Posición actual
            explored_area: Área explorada
            known_goal: Objetivo conocido (si existe)

        Returns:
            Siguiente posición a explorar
        """
        if self.strategy == self.BREADTH_FIRST:
            return self._breadth_first_target(current_pos, explored_area)
        elif self.strategy == self.DEPTH_FIRST:
            return self._depth_first_target(current_pos, explored_area)
        elif self.strategy == self.GOAL_ORIENTED and known_goal:
            return self._goal_oriented_target(current_pos, explored_area, known_goal)

        return self._breadth_first_target(current_pos, explored_area)

    def _breadth_first_target(self, current_pos: Tuple[int, int],
                             explored_area: ExploredArea) -> Optional[Tuple[int, int]]:
        """BFS: explorar frontera más cercana"""
        frontier = explored_area.get_exploration_frontier()

        if not frontier:
            return None

        # Encontrar frontera más cercana
        min_dist = float('inf')
        best_target = None

        for frontier_pos in frontier:
            dist = abs(current_pos[0] - frontier_pos[0]) + abs(current_pos[1] - frontier_pos[1])
            if dist < min_dist:
                min_dist = dist
                best_target = frontier_pos

        return best_target

    def _depth_first_target(self, current_pos: Tuple[int, int],
                           explored_area: ExploredArea) -> Optional[Tuple[int, int]]:
        """DFS: ir lo más lejos posible"""
        unknown = explored_area.get_unknown_neighbors(current_pos)

        if unknown:
            return unknown[0]  # Tomar el primero

        frontier = explored_area.get_exploration_frontier()
        if frontier:
            return frontier[-1]  # Tomar el más lejano

        return None

    def _goal_oriented_target(self, current_pos: Tuple[int, int],
                             explored_area: ExploredArea,
                             known_goal: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Goal-oriented: explorar hacia el objetivo conocido"""
        # Si ya hemos explorado el objetivo, no hay nada que hacer
        if explored_area.is_cell_explored(known_goal):
            return self._breadth_first_target(current_pos, explored_area)

        # Intentar dirigirse al objetivo
        row, col = current_pos
        goal_row, goal_col = known_goal

        # Movimiento hacia el objetivo
        if row < goal_row:
            next_pos = (row + 5, col)
        elif row > goal_row:
            next_pos = (row - 5, col)
        elif col < goal_col:
            next_pos = (row, col + 5)
        elif col > goal_col:
            next_pos = (row, col - 5)
        else:
            return self._breadth_first_target(current_pos, explored_area)

        if 0 <= next_pos[0] < 64 and 0 <= next_pos[1] < 64:
            return next_pos

        return self._breadth_first_target(current_pos, explored_area)


class Explorer:
    """Sistema de exploración bajo visibilidad parcial"""

    def __init__(self, initial_world: Optional[WorldState] = None,
                 strategy: str = ExplorationStrategy.BREADTH_FIRST,
                 debug: bool = False):
        """
        Inicializar explorador

        Args:
            initial_world: Mundo inicial conocido
            strategy: Estrategia de exploración
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.explored_area = ExploredArea(initial_world)
        self.exploration_strategy = ExplorationStrategy(strategy)
        self.visited_states: Set[Tuple[Tuple[int, int], int, int, int]] = set()

        if debug:
            logger.debug(f"✓ Explorer initialized with {strategy} strategy")

    def update_with_observation(self, position: Tuple[int, int],
                               observation: Dict[str, Any]):
        """
        Actualizar conocimiento con nueva observación

        Args:
            position: Posición donde se hizo la observación
            observation: Dict con información descubierta
                - "cell_type": tipo de celda
                - "rotator": Rotator si hay uno
                - "door": Door si hay una
                - "content": descripción del contenido
        """
        self.explored_area.discover_cell(position, observation.get("cell_type", "floor"))

        if "rotator" in observation:
            self.explored_area.discover_rotator(observation["rotator"])

        if "door" in observation:
            self.explored_area.discover_door(observation["door"])

        if self.debug:
            logger.debug(f"Updated: {position} → {observation}")

    def get_next_exploration_target(self, current_pos: Tuple[int, int],
                                   known_goal: Optional[Tuple[int, int]] = None
                                   ) -> Optional[Tuple[int, int]]:
        """
        Obtener siguiente objetivo de exploración

        Args:
            current_pos: Posición actual
            known_goal: Objetivo conocido (si existe)

        Returns:
            Siguiente posición a explorar
        """
        return self.exploration_strategy.choose_next_exploration_target(
            current_pos, self.explored_area, known_goal
        )

    def is_explored(self, pos: Tuple[int, int]) -> bool:
        """Verificar si una posición fue explorada"""
        return self.explored_area.is_cell_explored(pos)

    def get_exploration_progress(self) -> Dict[str, Any]:
        """
        Obtener progreso de exploración

        Returns:
            Dict con estadísticas
        """
        frontier = self.explored_area.get_exploration_frontier()
        total_grid = 64 * 64

        return {
            'discovered_cells': len(self.explored_area.discovered_cells),
            'total_cells': total_grid,
            'coverage': len(self.explored_area.discovered_cells) / total_grid,
            'frontier_size': len(frontier),
            'walls': len(self.explored_area.walls),
            'rotators': len(self.explored_area.rotators),
            'doors': len(self.explored_area.doors),
        }

    def can_reach_goal(self, current_pos: Tuple[int, int],
                      goal_pos: Tuple[int, int]) -> Optional[bool]:
        """
        Verificar si podemos alcanzar el objetivo

        Returns:
            True si sabemos que es alcanzable
            False si sabemos que es bloqueado
            None si es desconocido
        """
        # Si el objetivo no está explorado, desconocido
        if not self.explored_area.is_cell_explored(goal_pos):
            return None

        # Si es una pared, no es alcanzable
        if goal_pos in self.explored_area.walls:
            return False

        # Si está en área explorada, es potencialmente alcanzable
        return True


def create_explorer(initial_world: Optional[WorldState] = None,
                   strategy: str = ExplorationStrategy.BREADTH_FIRST,
                   debug: bool = False) -> Explorer:
    """Factory para crear explorador"""
    return Explorer(initial_world, strategy, debug)
