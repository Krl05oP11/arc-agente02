"""
Plan Executor - Traduce planes a acciones de ARC Prize

Convierte planes del agente a GameActions para ARC Prize.
"""

from typing import List, Optional, Tuple
from src.arc_grid_adapter import GridAdapter


class PlanExecutor:
    """Ejecuta planes del agente en ARC Prize"""

    @staticmethod
    def plan_to_actions(plan, current_position: Tuple[int, int]) -> List[str]:
        """
        Traducir plan a lista de GameActions

        Args:
            plan: Plan object con actions [(row, col), ...]
            current_position: (row, col) posición actual

        Returns:
            Lista de nombres de acciones: ["ACTION1", "ACTION2", ...]
        """
        if not plan or not plan.actions:
            return []

        actions = []
        current_pos = current_position

        for target_pos in plan.actions:
            # Traducir posición a acción
            action = GridAdapter.grid_position_to_game_action(
                current_pos, target_pos
            )
            if action:
                actions.append(action)
                current_pos = target_pos

        return actions

    @staticmethod
    def execute_plan(env, plan, current_position: Tuple[int, int]) -> dict:
        """
        Ejecutar plan en ambiente ARC Prize

        Args:
            env: Ambiente de ARC Prize
            plan: Plan a ejecutar
            current_position: (row, col) posición inicial

        Returns:
            Dict con resultados:
            {
                "success": bool,
                "steps": int,
                "final_position": (row, col),
                "errors": [list of errors]
            }
        """
        if not plan:
            return {
                "success": False,
                "steps": 0,
                "final_position": current_position,
                "errors": ["No plan provided"]
            }

        actions = PlanExecutor.plan_to_actions(plan, current_position)
        errors = []
        current_pos = current_position

        try:
            for i, action_name in enumerate(actions):
                try:
                    # Ejecutar acción en ARC Prize
                    from arcengine import GameAction
                    action = GameAction.from_name(action_name)
                    frame = env.step(action)

                    if frame is None:
                        errors.append(f"Step {i}: Environment returned None")
                        break

                    # Actualizar posición
                    grid = frame.frame[0]
                    new_pos = GridAdapter.get_player_position(grid)
                    if new_pos:
                        current_pos = new_pos
                    else:
                        errors.append(f"Step {i}: Could not find player position")

                except Exception as e:
                    errors.append(f"Step {i}: {str(e)}")
                    break

            return {
                "success": len(errors) == 0,
                "steps": len(actions),
                "final_position": current_pos,
                "errors": errors
            }

        except Exception as e:
            return {
                "success": False,
                "steps": len(actions),
                "final_position": current_pos,
                "errors": [str(e)]
            }

    @staticmethod
    def validate_plan(plan) -> Tuple[bool, str]:
        """
        Validar que plan sea ejecutable

        Args:
            plan: Plan a validar

        Returns:
            (valid: bool, message: str)
        """
        if plan is None:
            return False, "Plan is None"

        if not hasattr(plan, 'actions'):
            return False, "Plan missing 'actions' attribute"

        if not isinstance(plan.actions, list):
            return False, "Plan.actions is not a list"

        if len(plan.actions) == 0:
            return False, "Plan.actions is empty"

        # Validar que cada acción sea una tupla (row, col)
        for i, action in enumerate(plan.actions):
            if not isinstance(action, (tuple, list)) or len(action) != 2:
                return False, f"Action {i} is not (row, col) format"

            if not all(isinstance(x, (int, float)) for x in action):
                return False, f"Action {i} contains non-numeric values"

        return True, "Plan is valid"

    @staticmethod
    def estimate_steps(plan) -> int:
        """
        Estimar número de pasos del plan

        Args:
            plan: Plan

        Returns:
            Número estimado de pasos
        """
        if not plan or not plan.actions:
            return 0

        return len(plan.actions)

    @staticmethod
    def estimate_time(plan) -> float:
        """
        Estimar tiempo de ejecución

        Asumir ~100ms por paso

        Args:
            plan: Plan

        Returns:
            Tiempo estimado en segundos
        """
        if not plan or not plan.actions:
            return 0.0

        return len(plan.actions) * 0.1


class PlanExecutionMetrics:
    """Métricas de ejecución de planes"""

    def __init__(self):
        self.total_plans = 0
        self.successful_plans = 0
        self.failed_plans = 0
        self.total_steps = 0
        self.total_time = 0.0

    def record_execution(self, result: dict, execution_time: float):
        """Registrar ejecución de plan"""
        self.total_plans += 1

        if result.get("success"):
            self.successful_plans += 1
        else:
            self.failed_plans += 1

        self.total_steps += result.get("steps", 0)
        self.total_time += execution_time

    def get_success_rate(self) -> float:
        """Obtener tasa de éxito"""
        if self.total_plans == 0:
            return 0.0
        return (self.successful_plans / self.total_plans) * 100

    def get_avg_steps(self) -> float:
        """Obtener promedio de pasos"""
        if self.total_plans == 0:
            return 0.0
        return self.total_steps / self.total_plans

    def get_avg_time(self) -> float:
        """Obtener promedio de tiempo"""
        if self.total_plans == 0:
            return 0.0
        return self.total_time / self.total_plans

    def summary(self) -> dict:
        """Obtener resumen de métricas"""
        return {
            "total_plans": self.total_plans,
            "successful_plans": self.successful_plans,
            "failed_plans": self.failed_plans,
            "success_rate": self.get_success_rate(),
            "avg_steps": self.get_avg_steps(),
            "avg_time": self.get_avg_time(),
            "total_steps": self.total_steps,
            "total_time": self.total_time,
        }
