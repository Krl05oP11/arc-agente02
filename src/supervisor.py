"""
Módulo 5: SUPERVISOR - Orchestrate Full Pipeline

Coordina el pipeline completo:
Perceptor → Inductor → Planificador → Renderizador

Maneja errores en cada etapa y proporciona fallbacks.
"""

from src.perceptor import create_perceptor
from src.inductor_reglas import create_inductor
from src.constrained_planner import create_constrained_planner
from src.mapeador import create_state_graph
from src.planificador import create_planner
from src.renderizador import create_renderizador
from src.types import State, Plan, Example
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
import logging
import time

logger = logging.getLogger(__name__)


class PipelineResult:
    """Resultado del pipeline completo"""

    def __init__(self):
        self.success = False
        self.rule = None
        self.plan = None
        self.rendered_grid = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}
        self.timing: Dict[str, float] = {}

    def __str__(self) -> str:
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        lines = [f"{status}", f"Errors: {len(self.errors)}", f"Warnings: {len(self.warnings)}"]
        return "\n".join(lines)


class Supervisor:
    """Orquestador del pipeline completo"""

    def __init__(self, debug: bool = False):
        """
        Inicializar el supervisor

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)

        # Crear componentes
        self.perceptor = create_perceptor(debug=debug)
        self.inductor = create_inductor(debug=debug)
        self.renderizador = create_renderizador(debug=debug)

        if debug:
            logger.debug("✓ Supervisor initialized")

    def run(self, examples: List[Example], test_grid: np.ndarray,
            test_world: Optional[Any] = None) -> PipelineResult:
        """
        Ejecutar pipeline completo

        Args:
            examples: Ejemplos de entrenamiento
            test_grid: Grid de test a resolver
            test_world: WorldState opcional (si no se puede inferir)

        Returns:
            PipelineResult con resultado completo
        """
        result = PipelineResult()
        start_time = time.time()

        try:
            if not examples:
                raise ValueError("No examples provided")
            # FASE 1: INFERENCE
            if self.debug:
                logger.info("=" * 60)
                logger.info("FASE 1: INFERENCE")
                logger.info("=" * 60)

            # Paso 1: Infer rule from examples
            if self.debug:
                logger.info(f"Inferring rule from {len(examples)} examples...")

            rule = self.inductor.infer_rule(examples)

            if rule is None:
                result.errors.append("Failed to infer rule from examples")
                return result

            result.rule = rule
            result.stats['rule_dsl'] = rule.dsl_program

            if self.debug:
                logger.info(f"✓ Rule inferred: {rule.dsl_program}")

            # FASE 2: PLANNING
            if self.debug:
                logger.info("=" * 60)
                logger.info("FASE 2: PLANNING")
                logger.info("=" * 60)

            # Paso 2: Create world state from test grid
            if test_world is None:
                if self.debug:
                    logger.info("Creating WorldState from test grid...")
                test_world = self.perceptor.parse_grid(test_grid)

            if test_world is None:
                result.errors.append("Failed to parse test grid")
                return result

            if self.debug:
                logger.info(f"✓ WorldState created: {len(test_world.walls)} walls, "
                           f"{len(test_world.rotators)} rotators")

            # Paso 3: Create constrained planner
            if self.debug:
                logger.info("Creating constrained planner...")

            planner = create_constrained_planner(test_world, rule, debug=self.debug)

            # Paso 4: Find initial state and goal
            start_state = State(
                position=test_world.player_pos,
                key_shape=test_world.key_state.shape_id,
                key_color=test_world.key_state.color_id,
                key_rotation=test_world.key_state.rotation_id,
                energy=42
            )

            # Goal key from first door (simplified)
            goal_key = (0, 0, 0)
            if test_world.doors:
                door = test_world.doors[0]
                goal_key = (door.required_key.shape_id,
                           door.required_key.color_id,
                           door.required_key.rotation_id)

            if self.debug:
                logger.info(f"Start: {start_state.position}, Goal key: {goal_key}")

            # Paso 5: Plan
            plan_time_start = time.time()
            plan = planner.plan(start_state, goal_key)
            result.timing['planning'] = time.time() - plan_time_start

            if plan is None or not plan.valid:
                result.errors.append("Planner failed to find valid plan")
                result.warnings.append("Attempting fallback: unconstrained A*")

                # Fallback: Try without constraints
                if self.debug:
                    logger.warning("Attempting fallback with unconstrained A*...")

                fallback_graph = create_state_graph(test_world, debug=self.debug)
                fallback_planner = create_planner(fallback_graph, debug=self.debug)
                plan = fallback_planner.search(start_state, goal_key)

                if plan is None:
                    return result

            result.plan = plan
            result.stats['plan_length'] = len(plan.actions)
            result.stats['plan_cost'] = plan.cost

            if self.debug:
                logger.info(f"✓ Plan found: {len(plan.actions)} steps, cost {plan.cost}")

            # FASE 3: VISUALIZATION
            if self.debug:
                logger.info("=" * 60)
                logger.info("FASE 3: VISUALIZATION")
                logger.info("=" * 60)

            # Paso 6: Render plan
            if self.debug:
                logger.info("Rendering plan...")

            try:
                rendered = self.renderizador.render(plan, test_grid)
                result.rendered_grid = rendered
                result.stats['rendered'] = True

                if self.debug:
                    logger.info("✓ Plan rendered successfully")
            except Exception as e:
                result.warnings.append(f"Rendering failed: {str(e)}")
                result.stats['rendered'] = False

            # SUCCESS
            result.success = True
            result.timing['total'] = time.time() - start_time

            if self.debug:
                logger.info("=" * 60)
                logger.info("✅ PIPELINE COMPLETE")
                logger.info("=" * 60)
                logger.info(f"Total time: {result.timing['total']:.3f}s")

            return result

        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            if self.debug:
                logger.exception("Pipeline error")
        finally:
            # Registrar tiempo total siempre
            result.timing['total'] = time.time() - start_time

        return result

    def validate_result(self, result: PipelineResult) -> Tuple[bool, List[str]]:
        """
        Validar resultado del pipeline

        Args:
            result: PipelineResult a validar

        Returns:
            Tupla (is_valid, issues)
        """
        issues = []

        if not result.success:
            issues.append("Pipeline failed")

        if result.rule is None:
            issues.append("No rule generated")

        if result.plan is None:
            issues.append("No plan generated")

        if result.rendered_grid is None:
            issues.append("Grid not rendered")

        return len(issues) == 0, issues


class SupervisorFactory:
    """Factory para crear supervisores"""

    @staticmethod
    def create_supervisor(debug: bool = False) -> Supervisor:
        """Crear un nuevo supervisor"""
        return Supervisor(debug=debug)

    @staticmethod
    def create_with_defaults() -> Supervisor:
        """Crear supervisor con configuración por defecto"""
        return Supervisor(debug=False)


def create_supervisor(debug: bool = False) -> Supervisor:
    """Factory conveniente para crear supervisor"""
    return Supervisor(debug=debug)
