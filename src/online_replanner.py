"""
Módulo: ONLINE REPLANNER - Replanning en tiempo real

Permite al agente:
- Detectar cambios en el mundo durante ejecución
- Invalidar planes cuando hay nuevos obstáculos
- Replanificar automáticamente
- Mantener progreso hacia objetivo
- Adaptar estrategia según descubrimientos
"""

from src.types import State, Plan, WorldState
from src.explorer import Explorer, ExploredArea
from src.planificador import AStarPlanner
from src.mapeador import StateGraph
from typing import Optional, Tuple, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class PlanValidity:
    """Estado de validez de un plan"""

    VALID = "valid"
    INVALID_OBSTACLE = "invalid_obstacle"
    INVALID_NEW_ROUTE = "invalid_new_route"
    PARTIALLY_VALID = "partially_valid"


class ReplanningEvent:
    """Evento que requiere replanning"""

    def __init__(self, event_type: str, position: Tuple[int, int],
                 description: str):
        """
        Inicializar evento

        Args:
            event_type: Tipo de evento
            position: Posición donde ocurrió
            description: Descripción del evento
        """
        self.event_type = event_type
        self.position = position
        self.description = description

    def __repr__(self):
        return f"ReplanningEvent({self.event_type} @ {self.position})"


class OnlineReplanner:
    """Replanificador online para ambiente dinámico"""

    def __init__(self, explorer: Explorer, debug: bool = False):
        """
        Inicializar replanificador

        Args:
            explorer: Explorador con memoria del mundo
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.explorer = explorer
        self.current_plan: Optional[Plan] = None
        self.plan_step = 0
        self.replan_count = 0
        self.events: List[ReplanningEvent] = []

        if debug:
            logger.debug("✓ OnlineReplanner initialized")

    def set_initial_plan(self, plan: Plan):
        """
        Establecer plan inicial

        Args:
            plan: Plan a ejecutar
        """
        self.current_plan = plan
        self.plan_step = 0

        if self.debug:
            logger.debug(f"Set initial plan: {len(plan.actions)} steps")

    def execute_step(self, current_position: Tuple[int, int],
                    observation: Dict[str, Any]) -> Tuple[Optional[Tuple[int, int]], bool]:
        """
        Ejecutar un paso del plan

        Args:
            current_position: Posición actual
            observation: Observación del mundo actual

        Returns:
            Tupla (next_position, needs_replan)
                - next_position: Siguiente posición a ir (None si error)
                - needs_replan: True si se necesita replanificar
        """
        # Actualizar explorer con observación
        self.explorer.update_with_observation(current_position, observation)

        # Si no hay plan, necesitamos uno
        if not self.current_plan:
            return None, True

        # Verificar si plan sigue siendo válido
        validity = self._check_plan_validity(observation)

        if validity == PlanValidity.VALID:
            # Plan sigue siendo válido, continuar
            if self.plan_step < len(self.current_plan.actions):
                next_pos = self.current_plan.actions[self.plan_step]
                self.plan_step += 1
                return next_pos, False
            else:
                # Plan completado
                return None, False

        else:
            # Plan inválido, necesitar replanning
            event = ReplanningEvent(
                "plan_invalid",
                current_position,
                f"Validity: {validity}"
            )
            self.events.append(event)

            if self.debug:
                logger.warning(f"Plan invalidated: {validity}")

            return None, True

    def should_replan(self, current_position: Tuple[int, int],
                     observation: Dict[str, Any]) -> bool:
        """
        Determinar si se necesita replanificar

        Args:
            current_position: Posición actual
            observation: Observación actual

        Returns:
            True si se necesita replanificar
        """
        # Caso 1: No hay plan
        if not self.current_plan:
            return True

        # Caso 2: Plan completado
        if self.plan_step >= len(self.current_plan.actions):
            return True

        # Caso 3: Nuevo obstáculo
        if observation.get("cell_type") == "wall":
            # Verificar si esta pared bloquea el plan
            next_step = self.current_plan.actions[self.plan_step] if self.plan_step < len(self.current_plan.actions) else None
            if next_step and next_step == current_position:
                return True

        # Caso 4: Nuevo rotador descubierto
        if "rotator" in observation:
            return True

        return False

    def replan(self, current_position: Tuple[int, int],
              goal_position: Tuple[int, int],
              world_state: WorldState) -> Optional[Plan]:
        """
        Replanificar desde posición actual

        Args:
            current_position: Posición actual
            goal_position: Objetivo
            world_state: Estado del mundo

        Returns:
            Nuevo plan o None si no es posible
        """
        self.replan_count += 1

        if self.debug:
            logger.info(f"Replan #{self.replan_count} from {current_position}")

        # Crear estado actual
        start_state = State(
            position=current_position,
            key_shape=world_state.key_state.shape_id,
            key_color=world_state.key_state.color_id,
            key_rotation=world_state.key_state.rotation_id,
            energy=world_state.energy
        )

        try:
            # Crear grafo de estado con mundo conocido
            graph = StateGraph(world_state, debug=self.debug)
            planner = AStarPlanner(graph, debug=self.debug)

            # Buscar plan
            goal_key = (
                world_state.doors[0].required_key.shape_id if world_state.doors else 0,
                world_state.doors[0].required_key.color_id if world_state.doors else 0,
                world_state.doors[0].required_key.rotation_id if world_state.doors else 0
            )

            plan = planner.search(start_state, goal_key)

            if plan:
                self.set_initial_plan(plan)
                if self.debug:
                    logger.info(f"✓ Replan successful: {len(plan.actions)} steps")
                return plan
            else:
                if self.debug:
                    logger.warning("Replan failed: No path found")
                return None

        except Exception as e:
            if self.debug:
                logger.error(f"Replan error: {e}")
            return None

    def _check_plan_validity(self, current_observation: Dict[str, Any]) -> str:
        """
        Verificar si el plan sigue siendo válido

        Args:
            current_observation: Observación actual

        Returns:
            Código de validez
        """
        if not self.current_plan:
            return PlanValidity.INVALID_NEW_ROUTE

        # Si el siguiente paso es un muro, plan inválido
        if self.plan_step < len(self.current_plan.actions):
            next_pos = self.current_plan.actions[self.plan_step]

            if current_observation.get("cell_type") == "wall":
                return PlanValidity.INVALID_OBSTACLE

        # Si nuevos rotadores, considerar replanning
        if "rotator" in current_observation:
            return PlanValidity.PARTIALLY_VALID

        return PlanValidity.VALID

    def get_next_action(self) -> Optional[Tuple[int, int]]:
        """
        Obtener siguiente acción del plan actual

        Returns:
            Siguiente posición o None
        """
        if not self.current_plan or self.plan_step >= len(self.current_plan.actions):
            return None

        return self.current_plan.actions[self.plan_step]

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de replanning

        Returns:
            Dict con stats
        """
        return {
            'replans': self.replan_count,
            'events': len(self.events),
            'plan_steps_completed': self.plan_step,
            'current_plan_length': len(self.current_plan.actions) if self.current_plan else 0,
        }


class AdaptiveExecutor:
    """Ejecutor adaptivo que coordina exploración y replanning"""

    def __init__(self, explorer: Explorer, world: WorldState, debug: bool = False):
        """
        Inicializar ejecutor adaptivo

        Args:
            explorer: Explorador
            world: Mundo inicial
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.explorer = explorer
        self.replanner = OnlineReplanner(explorer, debug)
        self.world = world
        self.execution_history: List[Tuple[int, int]] = []

        if debug:
            logger.debug("✓ AdaptiveExecutor initialized")

    def execute_with_exploration(self, initial_plan: Plan,
                                goal_position: Tuple[int, int],
                                max_steps: int = 500) -> Dict[str, Any]:
        """
        Ejecutar plan con exploración adaptiva

        Args:
            initial_plan: Plan inicial
            goal_position: Objetivo
            max_steps: Máximo de pasos

        Returns:
            Dict con resultado de ejecución
        """
        self.replanner.set_initial_plan(initial_plan)
        current_pos = self.world.player_pos
        step_count = 0
        success = False

        while step_count < max_steps:
            self.execution_history.append(current_pos)

            # Simular observación en posición actual
            observation = self._get_observation(current_pos)

            # Ejecutar paso
            next_pos, needs_replan = self.replanner.execute_step(current_pos, observation)

            if needs_replan or not next_pos:
                # Necesitar replanning
                plan = self.replanner.replan(current_pos, goal_position, self.world)

                if not plan:
                    if self.debug:
                        logger.warning("Cannot replan: Goal unreachable")
                    break

                next_pos = self.replanner.get_next_action()

            # Verificar si llegamos al objetivo
            if next_pos and next_pos == goal_position:
                success = True
                self.execution_history.append(next_pos)
                break

            if next_pos:
                current_pos = next_pos
            else:
                break

            step_count += 1

        return {
            'success': success,
            'steps': step_count,
            'path': self.execution_history,
            'replans': self.replanner.replan_count,
            'events': len(self.replanner.events),
        }

    def _get_observation(self, position: Tuple[int, int]) -> Dict[str, Any]:
        """
        Obtener observación en posición

        Args:
            position: Posición actual

        Returns:
            Observación (simulada)
        """
        # Simplificación: asumir piso conocido
        return {"cell_type": "floor", "content": "visited"}


def create_online_replanner(explorer: Explorer, debug: bool = False) -> OnlineReplanner:
    """Factory para crear replanificador online"""
    return OnlineReplanner(explorer, debug)


def create_adaptive_executor(explorer: Explorer, world: WorldState,
                            debug: bool = False) -> AdaptiveExecutor:
    """Factory para crear ejecutor adaptivo"""
    return AdaptiveExecutor(explorer, world, debug)
