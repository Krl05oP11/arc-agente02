"""
Adaptador para ARC Prize Toolkit (arc-agi)

Permite integrar ARC-AGENTE02 con el toolkit oficial de ARC Prize
para testear en los benchmarks públicos.

Uso:
    from src.arc_prize_adapter import ArcPrizeAgent

    agent = ArcPrizeAgent(game_name="ls20", level_idx=0)
    result = agent.run(max_steps=500)
    print(f"Status: {result['status']}, Steps: {result['steps']}")
"""

from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ArcPrizeAdapter:
    """Adaptador entre nuestro sistema y el toolkit de ARC Prize"""

    def __init__(self, debug: bool = False):
        """
        Inicializar adaptador

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        self._check_arc_agi_installed()

    def _check_arc_agi_installed(self):
        """Verificar que arc-agi esté instalado"""
        try:
            import arc_agi
            self.arc_agi = arc_agi
            if self.debug:
                logger.info("✓ arc-agi toolkit encontrado")
        except ImportError:
            raise ImportError(
                "arc-agi toolkit no instalado. Instalar con:\n"
                "  pip install arc-agi\n"
                "o\n"
                "  uv add arc-agi"
            )

    def create_environment(self, game_name: str, level_idx: Optional[int] = None):
        """
        Crear ambiente de ARC Prize

        Args:
            game_name: Nombre del juego (ej: "ls20", "arc-agi-3")
            level_idx: Índice del nivel (opcional)

        Returns:
            Ambiente creado
        """
        try:
            arcade = self.arc_agi.Arcade()

            if level_idx is not None:
                env_id = f"{game_name}/{level_idx}"
            else:
                env_id = game_name

            env = arcade.make(env_id, render_mode="terminal")

            if self.debug:
                logger.info(f"✓ Ambiente creado: {env_id}")

            return env

        except Exception as e:
            logger.error(f"Error creando ambiente: {e}")
            raise

    def step(self, env, action_type: str, data: Optional[Dict] = None):
        """
        Ejecutar una acción en el ambiente

        Args:
            env: Ambiente ARC Prize
            action_type: Tipo de acción (ACTION1, ACTION2, etc)
            data: Datos adicionales (coordenadas, etc)

        Returns:
            Resultado (obs, done, info)
        """
        try:
            from arcengine import GameAction

            # Convertir nombre de acción a enum
            action = getattr(GameAction, action_type)

            # Construir kwargs
            kwargs = {"reasoning": {"thought": f"Action {action_type}"}}
            if data:
                kwargs["data"] = data

            # Ejecutar
            obs = env.step(action, **kwargs)

            if obs is None:
                logger.warning(f"Acción {action_type} falló (retornó None)")
                return None, True, {"error": "action_failed"}

            # Extraer información
            info = {
                "status": obs.get("status", "unknown"),
                "reward": obs.get("reward", 0),
            }

            done = obs.get("status") in ["WIN", "GAME_OVER", "INVALID"]

            return obs, done, info

        except Exception as e:
            logger.error(f"Error ejecutando acción: {e}")
            return None, True, {"error": str(e)}

    def get_scorecard(self, env):
        """
        Obtener scorecard de resultados

        Args:
            env: Ambiente ARC Prize

        Returns:
            Dict con resultados
        """
        try:
            scorecard = env.get_scorecard()
            return scorecard
        except Exception as e:
            logger.warning(f"No se pudo obtener scorecard: {e}")
            return None


class ArcPrizeAgent:
    """Agente que ejecuta en benchmarks de ARC Prize"""

    def __init__(self, game_name: str = "ls20", level_idx: Optional[int] = None,
                 debug: bool = False):
        """
        Inicializar agente para ARC Prize

        Args:
            game_name: Nombre del juego
            level_idx: Nivel a ejecutar
            debug: Si True, imprimir logs
        """
        self.game_name = game_name
        self.level_idx = level_idx
        self.debug = debug
        self.adapter = ArcPrizeAdapter(debug=debug)
        self.env = None
        self.execution_history: List[Dict] = []

    def connect(self):
        """Conectar al ambiente de ARC Prize"""
        try:
            self.env = self.adapter.create_environment(self.game_name, self.level_idx)
            if self.debug:
                logger.info("✓ Conectado a ARC Prize")
            return True
        except Exception as e:
            logger.error(f"Error conectando: {e}")
            return False

    def run(self, max_steps: int = 500, strategy: str = "random") -> Dict[str, Any]:
        """
        Ejecutar agente en benchmark

        Args:
            max_steps: Máximo de pasos
            strategy: Estrategia (random, learned, optimal)

        Returns:
            Dict con resultados
        """
        if not self.connect():
            return {
                "status": "FAILED_CONNECT",
                "steps": 0,
                "reason": "No se pudo conectar a ARC Prize"
            }

        step_count = 0
        result_status = "INCOMPLETE"

        try:
            while step_count < max_steps:
                # Elegir acción según estrategia
                action = self._choose_action(strategy, step_count)

                # Ejecutar
                obs, done, info = self.adapter.step(self.env, action)

                step_count += 1
                self.execution_history.append({
                    "step": step_count,
                    "action": action,
                    "status": info.get("status", "unknown"),
                    "reward": info.get("reward", 0),
                })

                if self.debug:
                    logger.info(
                        f"Step {step_count}: {action} → {info.get('status', 'unknown')}"
                    )

                if done:
                    result_status = info.get("status", "DONE")
                    break

        except KeyboardInterrupt:
            result_status = "INTERRUPTED"
        except Exception as e:
            logger.error(f"Error durante ejecución: {e}")
            result_status = "ERROR"

        # Obtener scorecard
        scorecard = self.adapter.get_scorecard(self.env)

        return {
            "status": result_status,
            "steps": step_count,
            "game": self.game_name,
            "level": self.level_idx,
            "strategy": strategy,
            "history": self.execution_history,
            "scorecard": scorecard,
        }

    def _choose_action(self, strategy: str, step_count: int) -> str:
        """
        Elegir siguiente acción

        Args:
            strategy: Estrategia a usar
            step_count: Número de paso actual

        Returns:
            Nombre de acción (ACTION1, ACTION2, etc)
        """
        if strategy == "random":
            import random
            actions = [f"ACTION{i}" for i in range(1, 13)]  # ACTION1-ACTION12
            return random.choice(actions)

        elif strategy == "sequential":
            # Ciclar a través de acciones disponibles
            action_num = (step_count % 12) + 1
            return f"ACTION{action_num}"

        elif strategy == "learned":
            # Aquí iría lógica aprendida
            return "ACTION1"  # Default

        else:
            return "ACTION1"

    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la ejecución"""
        return {
            "game": self.game_name,
            "level": self.level_idx,
            "total_steps": len(self.execution_history),
            "final_status": self.execution_history[-1]["status"] if self.execution_history else "unknown",
            "actions": [h["action"] for h in self.execution_history],
        }


def test_connection(game_name: str = "ls20", level_idx: int = 0):
    """
    Test rápido de conexión a ARC Prize

    Args:
        game_name: Juego a probar
        level_idx: Nivel a probar
    """
    print(f"\n🔌 Testeando conexión a ARC Prize...")
    print(f"   Juego: {game_name}, Nivel: {level_idx}")

    try:
        agent = ArcPrizeAgent(game_name, level_idx, debug=True)

        if agent.connect():
            print("✅ Conexión exitosa")
            return True
        else:
            print("❌ Conexión falló")
            return False

    except ImportError as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    # Test de conexión
    test_connection()
