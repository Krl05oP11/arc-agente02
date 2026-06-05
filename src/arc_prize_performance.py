"""
Performance Testing en ARC Prize Benchmark

Permite testear la performance REAL de ARC-AGENTE02 en benchmarks públicos.
Integra los planes del agente con el toolkit oficial de ARC Prize.

Uso:
    from src.arc_prize_performance import ArcPrizePerformanceTest

    test = ArcPrizePerformanceTest()
    results = test.run_benchmark_suite()
    report = test.generate_report()
"""

from typing import Dict, List, Tuple, Optional, Any
import json
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Métricas de performance del agente"""

    def __init__(self):
        """Inicializar colector de métricas"""
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.total_steps = 0
        self.total_time = 0.0
        self.step_times: List[float] = []
        self.results: List[Dict[str, Any]] = []

    def record_test(self, game: str, level: int, success: bool, steps: int,
                   elapsed_time: float):
        """Registrar resultado de un test"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

        self.total_steps += steps
        self.total_time += elapsed_time
        self.step_times.append(elapsed_time / max(steps, 1))

        self.results.append({
            "game": game,
            "level": level,
            "success": success,
            "steps": steps,
            "time_ms": elapsed_time * 1000,
            "time_per_step_ms": (elapsed_time / max(steps, 1)) * 1000,
        })

    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        avg_step_time = sum(self.step_times) / len(self.step_times) if self.step_times else 0

        return {
            "tests_total": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "success_rate": (self.tests_passed / max(self.tests_run, 1)) * 100,
            "total_steps": self.total_steps,
            "avg_steps_per_test": self.total_steps / max(self.tests_run, 1),
            "total_time_sec": self.total_time,
            "avg_time_per_step_ms": avg_step_time * 1000,
        }

    def __repr__(self):
        summary = self.get_summary()
        return (
            f"PerformanceMetrics(passed={summary['tests_passed']}/{summary['tests_total']}, "
            f"success_rate={summary['success_rate']:.1f}%)"
        )


class ArcPrizePerformanceTest:
    """Suite de tests de performance en ARC Prize"""

    def __init__(self, debug: bool = False):
        """
        Inicializar test suite

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        self.metrics = PerformanceMetrics()
        self._check_toolkit()

    def _check_toolkit(self):
        """Verificar que arc-agi esté instalado"""
        try:
            import arc_agi
            self.arc_agi = arc_agi
            if self.debug:
                logger.info("✓ arc-agi toolkit disponible")
        except ImportError:
            raise ImportError(
                "arc-agi no instalado. Ejecutar: pip install arc-agi"
            )

    def test_single_level(self, game: str, level: int, max_steps: int = 500) -> Dict:
        """
        Testear un nivel específico

        Args:
            game: Nombre del juego
            level: Índice del nivel
            max_steps: Máximo de pasos

        Returns:
            Resultados del test
        """
        try:
            from src.arc_prize_adapter import ArcPrizeAgent

            if self.debug:
                logger.info(f"Testing {game}/{level}...")

            start_time = time.perf_counter()

            # Crear agente
            agent = ArcPrizeAgent(game, level, debug=False)

            # Ejecutar con estrategia random (demo)
            # TODO: Integrar con planes de ARC-AGENTE02
            result = agent.run(max_steps=max_steps, strategy="random")

            elapsed = time.perf_counter() - start_time

            # Registrar métricas
            success = result['status'] in ['WIN', 'COMPLETE']
            self.metrics.record_test(game, level, success, result['steps'], elapsed)

            return {
                "game": game,
                "level": level,
                "success": success,
                "status": result['status'],
                "steps": result['steps'],
                "time_sec": elapsed,
                "scorecard": result['scorecard'],
            }

        except Exception as e:
            logger.error(f"Error testing {game}/{level}: {e}")
            self.metrics.record_test(game, level, False, 0, 0)
            return {
                "game": game,
                "level": level,
                "success": False,
                "status": "ERROR",
                "error": str(e),
            }

    def run_benchmark_suite(self, games: Optional[List[Tuple[str, int]]] = None,
                           max_steps: int = 500) -> List[Dict]:
        """
        Ejecutar suite completa de benchmarks

        Args:
            games: Lista de (game, level) a testear. Si None, usar defaults.
            max_steps: Máximo de pasos por nivel

        Returns:
            Lista de resultados
        """
        if games is None:
            # Benchmarks por defecto
            games = [
                ("ls20", 0),
                ("ls20", 1),
                ("ls20", 2),
            ]

        results = []
        print(f"\n🧪 Ejecutando {len(games)} benchmarks...")
        print("=" * 60)

        for i, (game, level) in enumerate(games, 1):
            print(f"[{i}/{len(games)}] {game}/{level}...", end=" ", flush=True)

            result = self.test_single_level(game, level, max_steps)
            results.append(result)

            status = "✅" if result['success'] else "❌"
            print(f"{status} ({result['steps']} pasos)")

        print("=" * 60)
        return results

    def generate_report(self) -> str:
        """Generar reporte textual"""
        summary = self.metrics.get_summary()

        report = "\n" + "="*70 + "\n"
        report += "📊 ARC PRIZE PERFORMANCE REPORT\n"
        report += "="*70 + "\n\n"

        report += "📈 RESUMEN\n"
        report += "-"*70 + "\n"
        report += f"Tests ejecutados:        {summary['tests_total']}\n"
        report += f"Tests exitosos:          {summary['tests_passed']}\n"
        report += f"Tests fallidos:          {summary['tests_failed']}\n"
        report += f"Tasa de éxito:           {summary['success_rate']:.1f}%\n"

        report += "\n⏱️  TIEMPO\n"
        report += "-"*70 + "\n"
        report += f"Tiempo total:            {summary['total_time_sec']:.2f} seg\n"
        report += f"Promedio por step:       {summary['avg_time_per_step_ms']:.2f} ms\n"

        report += "\n📍 PASOS\n"
        report += "-"*70 + "\n"
        report += f"Total de pasos:          {summary['total_steps']}\n"
        report += f"Promedio por test:       {summary['avg_steps_per_test']:.1f}\n"

        report += "\n📋 RESULTADOS DETALLADOS\n"
        report += "-"*70 + "\n"

        for result in self.metrics.results:
            status = "✅" if result['success'] else "❌"
            report += (f"{status} {result['game']}/{result['level']}: "
                      f"{result['steps']} pasos, {result['time_ms']:.1f} ms\n")

        report += "\n" + "="*70 + "\n"

        return report

    def export_json(self, filepath: str):
        """Exportar resultados a JSON"""
        data = {
            "summary": self.metrics.get_summary(),
            "results": self.metrics.results,
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        if self.debug:
            logger.info(f"Resultados exportados a {filepath}")


class PerformanceComparison:
    """Comparar performance contra baselines"""

    def __init__(self):
        """Inicializar comparador"""
        self.baselines = {
            "random_agent": 10.0,  # % éxito esperado
            "sequential_agent": 15.0,
            "human_average": 85.0,
        }

    def compare(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """
        Comparar performance

        Args:
            metrics: Métricas del agente

        Returns:
            Comparación con baselines
        """
        summary = metrics.get_summary()
        success_rate = summary['success_rate']

        comparison = {
            "agent_success_rate": success_rate,
            "vs_random": success_rate - self.baselines["random_agent"],
            "vs_sequential": success_rate - self.baselines["sequential_agent"],
            "vs_human": success_rate - self.baselines["human_average"],
        }

        return comparison


def quick_performance_test():
    """Test rápido de performance"""
    print("\n🚀 QUICK PERFORMANCE TEST")
    print("="*60)

    try:
        test = ArcPrizePerformanceTest(debug=True)

        # Testear un nivel
        print("\n📍 Testing single level...")
        result = test.test_single_level("ls20", 0, max_steps=100)

        print(f"\n✅ Resultado: {result['status']}")
        print(f"   Pasos: {result['steps']}")
        print(f"   Tiempo: {result['time_sec']:.2f}s")

        # Generar reporte
        report = test.generate_report()
        print(report)

        return True

    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nInstalar con: pip install arc-agi")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    quick_performance_test()
