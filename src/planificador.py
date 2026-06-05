"""
Módulo 4: PLANIFICADOR - StateGraph → Optimal Plan

Implementa A* search para encontrar caminos óptimos en el espacio de estados unificado.

El algoritmo A* minimiza: f(n) = g(n) + h(n)
donde:
  - g(n) = costo real desde start hasta n
  - h(n) = heurística estimada desde n hasta goal
  - f(n) = costo total estimado
"""

from src.types import State, WorldState, Plan
from src.mapeador import StateGraph
import heapq
from typing import List, Tuple, Optional, Dict
import logging
import time

logger = logging.getLogger(__name__)


class AStarPlanner:
    """Planificador A* para búsqueda óptima en espacio de estados"""

    def __init__(self, state_graph: StateGraph, debug: bool = False):
        """
        Inicializar el planificador A*

        Args:
            state_graph: Grafo de transiciones de estados
            debug: Si True, imprimir logs detallados
        """
        self.graph = state_graph
        self.debug = debug
        self.nodes_explored = 0
        self.search_time = 0.0

        if debug:
            logger.setLevel(logging.DEBUG)

    def search(self, start_state: State, goal_key: Tuple[int, int, int],
               max_iterations: int = 100000) -> Optional[Plan]:
        """
        Buscar plan óptimo usando A*

        Args:
            start_state: Estado inicial (posición, llave, energía)
            goal_key: (shape_id, color_id, rotation_id) requerido para puerta
            max_iterations: Límite máximo de iteraciones (seguridad)

        Returns:
            Plan con acciones (lista de posiciones) o None si no encuentra solución
        """
        start_time = time.time()
        self.nodes_explored = 0

        # Priority queue: (f_cost, counter, state)
        # Counter es para mantener orden FIFO cuando f es igual
        counter = 0
        open_set = []
        heapq.heappush(open_set, (0, counter, start_state))
        counter += 1

        # Tracking
        came_from: Dict[State, Optional[State]] = {start_state: None}
        g_score: Dict[State, int] = {start_state: 0}  # Costo real desde start
        f_score: Dict[State, int] = {
            start_state: self.graph.heuristic(start_state, goal_key)
        }

        closed_set = set()

        while open_set and self.nodes_explored < max_iterations:
            self.nodes_explored += 1

            # Obtener nodo con menor f(n)
            f_current, _, current = heapq.heappop(open_set)

            # Convertir state a hashable para closed_set
            current_hash = self._state_hash(current)
            if current_hash in closed_set:
                continue
            closed_set.add(current_hash)

            if self.debug and self.nodes_explored % 100 == 0:
                logger.debug(f"Explored {self.nodes_explored} nodes, "
                            f"open_set size: {len(open_set)}")

            # ¿Es meta?
            if self.graph.is_goal(current):
                self.search_time = time.time() - start_time
                path = self._reconstruct_path(current, came_from)
                if self.debug:
                    logger.debug(f"✓ Found goal in {self.nodes_explored} nodes, "
                                f"{len(path)} steps, {self.search_time:.3f}s")
                return Plan(
                    actions=path,
                    cost=g_score[current],
                    valid=True
                )

            # Explorar vecinos
            neighbors = self.graph.neighbors(current)

            for next_state, move_cost in neighbors:
                next_hash = self._state_hash(next_state)

                if next_hash in closed_set:
                    continue

                # Calcular nuevos costos
                tentative_g = g_score[current] + move_cost
                next_h = self.graph.heuristic(next_state, goal_key)
                tentative_f = tentative_g + next_h

                # ¿Es mejor camino?
                if next_state not in g_score or tentative_g < g_score[next_state]:
                    # Actualizar mejor camino
                    came_from[next_state] = current
                    g_score[next_state] = tentative_g
                    f_score[next_state] = tentative_f

                    # Agregar a open_set si no está
                    heapq.heappush(open_set, (tentative_f, counter, next_state))
                    counter += 1

        # No encontró solución
        self.search_time = time.time() - start_time
        if self.debug:
            logger.warning(f"No solution found after {self.nodes_explored} nodes "
                          f"in {self.search_time:.3f}s")
        return None

    def _reconstruct_path(self, current: State,
                          came_from: Dict[State, Optional[State]]) -> List[Tuple[int, int]]:
        """
        Reconstruir el camino desde start hasta goal

        Args:
            current: Estado actual (goal)
            came_from: Mapping de estado → estado anterior

        Returns:
            Lista de posiciones (camino completo)
        """
        path = [current.position]

        while current in came_from and came_from[current] is not None:
            current = came_from[current]
            path.append(current.position)

        path.reverse()
        return path

    def _state_hash(self, state: State) -> tuple:
        """
        Convertir estado a hashable para tracking

        Args:
            state: Estado a hashear

        Returns:
            Tupla hashable que identifica el estado
        """
        # Usar tupla de atributos clave
        visited_tuple = tuple(sorted(state.visited_rotators)) if state.visited_rotators else ()
        return (
            state.position,
            state.key_shape,
            state.key_color,
            state.key_rotation,
            state.energy,
            visited_tuple
        )

    def get_stats(self) -> Dict[str, any]:
        """Retornar estadísticas de búsqueda"""
        return {
            'nodes_explored': self.nodes_explored,
            'search_time': self.search_time,
            'nodes_per_second': self.nodes_explored / max(self.search_time, 0.001)
        }


class PlanValidator:
    """Validar que un plan es ejecutable"""

    def __init__(self, state_graph: StateGraph, debug: bool = False):
        """
        Inicializar validador

        Args:
            state_graph: Grafo de transiciones
            debug: Si True, imprimir logs
        """
        self.graph = state_graph
        self.debug = debug

    def validate(self, plan: Plan, start_state: State) -> Tuple[bool, Optional[str]]:
        """
        Verificar que un plan es válido y ejecutable

        Args:
            plan: Plan a validar
            start_state: Estado inicial

        Returns:
            Tupla (is_valid, error_message)
        """
        if not plan or not plan.actions:
            return False, "Plan is empty"

        current = start_state

        for i, next_pos in enumerate(plan.actions):
            # Si es el primer paso, debe ser igual a la posición inicial
            if i == 0:
                if next_pos != current.position:
                    return False, f"First position {next_pos} doesn't match start {current.position}"
                continue

            # Verificar que el movimiento es válido
            neighbors = self.graph.neighbors(current)
            found = False

            for next_state, _ in neighbors:
                if next_state.position == next_pos:
                    current = next_state
                    found = True
                    break

            if not found:
                return False, f"Invalid move at step {i}: {current.position} → {next_pos}"

        # Verificar que llegamos a meta
        if not self.graph.is_goal(current):
            return False, f"Plan does not reach goal: final state {current}"

        if self.debug:
            logger.debug(f"✓ Plan validated: {len(plan.actions)} steps, cost {plan.cost}")

        return True, None


def create_planner(state_graph: StateGraph, debug: bool = False) -> AStarPlanner:
    """Factory para crear un planificador A*"""
    return AStarPlanner(state_graph, debug=debug)


def create_validator(state_graph: StateGraph, debug: bool = False) -> PlanValidator:
    """Factory para crear un validador de planes"""
    return PlanValidator(state_graph, debug=debug)
