"""
ARC Integration Bridge - Puente entre ARC-AGENTE02 y ARC Prize

Conecta el sistema completo: agente → plan → ejecución → métricas
"""

import numpy as np
from typing import Optional, Dict, Any
from src.arc_grid_adapter import GridAdapter
from src.arc_plan_executor import PlanExecutor, PlanExecutionMetrics
from src.supervisor import create_supervisor
from src.types import Example, WorldState, Door, KeyState


class ArcIntegrationBridge:
    """Puente de integración ARC-AGENTE02 ↔ ARC Prize"""

    def __init__(self, debug: bool = False):
        """
        Inicializar bridge

        Args:
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.supervisor = create_supervisor(debug=debug)
        self.metrics = PlanExecutionMetrics()
        self.game_history = []

    def solve_level(
        self,
        env,
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """
        Resolver un nivel completo

        Args:
            env: Ambiente de ARC Prize
            max_steps: Máximo número de pasos

        Returns:
            Dict con resultados
        """
        results = {
            "success": False,
            "total_steps": 0,
            "frames_processed": 0,
            "plans_generated": 0,
            "plans_successful": 0,
            "errors": [],
            "history": []
        }

        try:
            # Reset del ambiente
            frame = env.reset()
            if frame is None:
                results["errors"].append("Environment reset failed")
                return results

            # Loop principal
            step_count = 0
            while step_count < max_steps:
                # Obtener grid actual
                grid = frame.frame[0]
                results["frames_processed"] += 1

                # Validar grid
                if not GridAdapter.validate_grid(grid):
                    results["errors"].append(f"Step {step_count}: Invalid grid")
                    break

                # Obtener posición del jugador
                player_pos = GridAdapter.get_player_position(grid)
                if not player_pos:
                    results["errors"].append(f"Step {step_count}: Player not found")
                    break

                # Crear ejemplo para supervisor
                try:
                    walls = GridAdapter.get_walls(grid)
                    doors = GridAdapter.get_doors(grid)

                    world = WorldState(
                        player_pos=player_pos,
                        walls=walls,
                        doors=[Door(position=d, required_key=KeyState(0, 0, 0)) for d in doors],
                        rotators=[],
                        refills=[],
                        teleporters=[],
                        key_state=KeyState(0, 0, 0),
                        energy=42
                    )

                    example = Example(
                        input_grid=grid,
                        solution_path=[player_pos],
                        world_state=world
                    )

                    # Ejecutar supervisor
                    result = self.supervisor.run([example], grid, test_world=world)
                    results["plans_generated"] += 1

                    if result.success and result.plan:
                        # Ejecutar plan
                        results["plans_successful"] += 1

                        # Traducir a acciones
                        actions = PlanExecutor.plan_to_actions(
                            result.plan, player_pos
                        )

                        # Ejecutar acciones
                        from arcengine import GameAction
                        for action_name in actions:
                            try:
                                action = GameAction.from_name(action_name)
                                frame = env.step(action)
                                step_count += 1

                                if frame is None:
                                    results["errors"].append(
                                        f"Step {step_count}: env.step returned None"
                                    )
                                    break

                                # Chequear si ganó
                                if frame.state.name == "GAME_OVER":
                                    results["success"] = True
                                    results["total_steps"] = step_count
                                    results["history"].append({
                                        "step": step_count,
                                        "status": "LEVEL_COMPLETE",
                                        "plan_length": len(actions)
                                    })
                                    return results

                                if step_count >= max_steps:
                                    results["errors"].append("Max steps reached")
                                    break

                            except Exception as e:
                                results["errors"].append(
                                    f"Step {step_count}: {str(e)[:50]}"
                                )
                                break

                    else:
                        # No hay plan
                        results["errors"].append(f"Step {step_count}: No plan generated")
                        break

                except Exception as e:
                    results["errors"].append(f"Step {step_count}: {str(e)[:50]}")
                    break

            results["total_steps"] = step_count

        except Exception as e:
            results["errors"].append(f"Bridge error: {str(e)}")

        return results

    def benchmark_levels(
        self,
        env_factory,
        levels: list,
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """
        Testear múltiples niveles

        Args:
            env_factory: Función que crea ambientes
            levels: Lista de niveles a testear
            max_steps: Máximo de pasos por nivel

        Returns:
            Resultados de benchmark
        """
        benchmark_results = {
            "total_levels": len(levels),
            "passed": 0,
            "failed": 0,
            "levels": [],
            "total_steps": 0,
            "avg_steps": 0.0
        }

        for level in levels:
            try:
                env = env_factory(level)
                if env is None:
                    benchmark_results["levels"].append({
                        "level": level,
                        "success": False,
                        "error": "Failed to create environment"
                    })
                    benchmark_results["failed"] += 1
                    continue

                result = self.solve_level(env, max_steps)

                if result.get("success"):
                    benchmark_results["passed"] += 1
                else:
                    benchmark_results["failed"] += 1

                benchmark_results["levels"].append({
                    "level": level,
                    "success": result.get("success"),
                    "steps": result.get("total_steps"),
                    "errors": len(result.get("errors", []))
                })

                benchmark_results["total_steps"] += result.get("total_steps", 0)

            except Exception as e:
                benchmark_results["levels"].append({
                    "level": level,
                    "success": False,
                    "error": str(e)[:50]
                })
                benchmark_results["failed"] += 1

        if len(levels) > 0:
            benchmark_results["avg_steps"] = (
                benchmark_results["total_steps"] / len(levels)
            )

        return benchmark_results

    def get_report(self) -> str:
        """Generar reporte de integración"""
        report = "\n" + "=" * 70 + "\n"
        report += "🌉 ARC INTEGRATION BRIDGE REPORT\n"
        report += "=" * 70 + "\n\n"

        report += "📊 METRICS\n"
        report += "-" * 70 + "\n"

        metrics = self.metrics.summary()
        report += f"Total Plans:           {metrics['total_plans']}\n"
        report += f"Successful:            {metrics['successful_plans']}\n"
        report += f"Failed:                {metrics['failed_plans']}\n"
        report += f"Success Rate:          {metrics['success_rate']:.1f}%\n"
        report += f"Avg Steps:             {metrics['avg_steps']:.1f}\n"
        report += f"Avg Time:              {metrics['avg_time']:.2f}s\n"

        report += "\n" + "=" * 70 + "\n"

        return report
