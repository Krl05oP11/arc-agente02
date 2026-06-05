"""
Agent Validator - Integración del Agente Real con Test Bench

Permite validar la performance REAL de ARC-AGENTE02 antes de envío
usando problemas de test controlados.
"""

from typing import Dict, List, Callable, Optional, Any
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


class AgentValidator:
    """Validador de performance del agente"""

    def __init__(self, agent_name: str = "ARC-AGENTE02", debug: bool = True):
        """
        Inicializar validador

        Args:
            agent_name: Nombre del agente
            debug: Si True, imprimir logs
        """
        self.agent_name = agent_name
        self.debug = debug
        self.validation_results: List[Dict[str, Any]] = []

    def validate_agent(self, test_suite: 'ARCTestBench',
                      agent_wrapper: Callable) -> Dict[str, Any]:
        """
        Validar agente contra suite de tests

        Args:
            test_suite: Suite de tests ARC
            agent_wrapper: Wrapper del agente real

        Returns:
            Resultados de validación
        """
        print(f"\n🔍 VALIDATING {self.agent_name}")
        print("=" * 70)

        results = test_suite.run_suite(agent_wrapper)

        # Analizar resultados
        analysis = self._analyze_results(results)

        return analysis

    def _analyze_results(self, results) -> Dict[str, Any]:
        """Analizar resultados de tests"""
        passed = sum(1 for r in results if r.success)
        total = len(results)

        analysis = {
            "agent": self.agent_name,
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "avg_time": sum(r.time_elapsed for r in results) / total if total > 0 else 0,
            "by_difficulty": {
                "EASY": len([r for r in results if r.difficulty == "EASY" and r.success]),
                "MEDIUM": len([r for r in results if r.difficulty == "MEDIUM" and r.success]),
                "HARD": len([r for r in results if r.difficulty == "HARD" and r.success]),
            },
            "errors": [r.error for r in results if r.error],
        }

        return analysis

    def generate_validation_report(self, analysis: Dict) -> str:
        """Generar reporte de validación"""
        report = "\n" + "=" * 70 + "\n"
        agent_name = analysis.get('agent', self.agent_name)
        report += f"✅ AGENT VALIDATION REPORT - {agent_name}\n"
        report += "=" * 70 + "\n\n"

        report += "📊 PERFORMANCE METRICS\n"
        report += "-" * 70 + "\n"
        report += f"Total Tests:            {analysis['total_tests']}\n"
        report += f"Passed:                 {analysis['passed']}\n"
        report += f"Failed:                 {analysis['failed']}\n"
        report += f"Success Rate:           {analysis['success_rate']:.1f}%\n"
        report += f"Avg Time per Test:      {analysis['avg_time']:.2f}s\n"

        report += "\n📈 BY DIFFICULTY\n"
        report += "-" * 70 + "\n"
        report += f"EASY:                   {analysis['by_difficulty']['EASY']}\n"
        report += f"MEDIUM:                 {analysis['by_difficulty']['MEDIUM']}\n"
        report += f"HARD:                   {analysis['by_difficulty']['HARD']}\n"

        if analysis.get('errors'):
            report += "\n⚠️  ERRORS\n"
            report += "-" * 70 + "\n"
            for error in analysis['errors']:
                report += f"  • {error}\n"

        report += "\n" + "=" * 70 + "\n"

        # Recomendación
        success_rate = analysis['success_rate']
        if success_rate >= 80:
            report += "✅ READY FOR SUBMISSION\n"
            report += "   Performance is excellent. Proceed with confidence.\n"
        elif success_rate >= 60:
            report += "⚠️  CAUTIOUS PROCEED\n"
            report += "   Performance is acceptable but could be improved.\n"
        elif success_rate >= 40:
            report += "🔴 NEEDS IMPROVEMENT\n"
            report += "   Performance is below recommended threshold.\n"
        else:
            report += "❌ NOT READY\n"
            report += "   Agent needs significant improvement before submission.\n"

        report += "=" * 70 + "\n"

        return report

    def print_recommendation(self, analysis: Dict) -> str:
        """Imprimir recomendación de envío"""
        success_rate = analysis['success_rate']

        print("\n" + "🎯 RECOMMENDATION" + "\n" + "-" * 70)

        if success_rate >= 80:
            print("✅ READY FOR SUBMISSION")
            print("   • Performance exceeds baseline expectations")
            print("   • Confidence level: HIGH")
            print("   • Recommended action: PROCEED TO GITHUB/KAGGLE")
        elif success_rate >= 60:
            print("⚠️  READY WITH CAVEATS")
            print("   • Performance is acceptable")
            print("   • Confidence level: MEDIUM")
            print("   • Recommended action: SUBMIT BUT MONITOR CLOSELY")
        elif success_rate >= 40:
            print("🟡 CONDITIONAL")
            print("   • Performance below ideal")
            print("   • Confidence level: LOW")
            print("   • Recommended action: FIX ISSUES, THEN SUBMIT")
        else:
            print("❌ NOT RECOMMENDED")
            print("   • Performance is insufficient")
            print("   • Confidence level: NONE")
            print("   • Recommended action: MAJOR IMPROVEMENTS NEEDED")

        print("-" * 70 + "\n")


class MockAgentWrapper:
    """Wrapper para testear con agente mock"""

    @staticmethod
    def simple_mock(input_examples, output_examples, test_input):
        """Agente mock simple"""
        if output_examples:
            return output_examples[0]
        return test_input


class RealAgentWrapper:
    """Wrapper para agente real de ARC-AGENTE02"""

    def __init__(self, supervisor=None):
        """
        Inicializar wrapper

        Args:
            supervisor: Instancia de Supervisor de ARC-AGENTE02
        """
        self.supervisor = supervisor or self._get_supervisor()

    def _get_supervisor(self):
        """Obtener supervisor (dummy si no disponible)"""
        try:
            from src.supervisor import create_supervisor
            return create_supervisor(debug=False)
        except ImportError:
            return None

    def predict(self, input_examples, output_examples, test_input):
        """
        Predecir output usando el agente real

        Args:
            input_examples: Grids de entrada
            output_examples: Grids de salida
            test_input: Grid de test

        Returns:
            Output predicho
        """
        if not self.supervisor:
            return None

        try:
            # Crear ejemplo simplificado
            from src.types import Example, WorldState, Door, KeyState

            # Simular un problema ARC basado en los ejemplos
            world = WorldState(
                player_pos=(0, 0),
                walls=set(),
                doors=[Door(position=(5, 5), required_key=KeyState(0, 0, 0))],
                rotators=[],
                refills=[],
                teleporters=[],
                key_state=KeyState(0, 0, 0),
                energy=42
            )

            example = Example(
                input_grid=input_examples[0] if input_examples else test_input,
                solution_path=[(0, 0), (5, 5)],
                world_state=world
            )

            # Ejecutar pipeline
            result = self.supervisor.run([example], test_input, test_world=world)

            if result.success and result.rendered_grid is not None:
                return result.rendered_grid

            return None

        except Exception as e:
            logger.warning(f"Error en agente real: {e}")
            return None


def test_agent_performance():
    """Test de performance del agente (demo)"""
    from src.arc_test_bench import ARCTestBench

    print("\n🚀 AGENT PERFORMANCE VALIDATION")
    print("=" * 70)

    # Crear test bench
    bench = ARCTestBench(num_problems=5, debug=False)

    # Crear validator
    validator = AgentValidator(agent_name="ARC-AGENTE02", debug=True)

    # Test con mock (para demostración)
    print("\n▶️  Testing con Mock Agent...")
    results = bench.run_suite(MockAgentWrapper.simple_mock)

    # Analizar
    analysis = validator._analyze_results(results)

    # Reporte
    report = validator.generate_validation_report(analysis)
    print(report)

    # Recomendación
    validator.print_recommendation(analysis)

    return analysis


if __name__ == "__main__":
    test_agent_performance()
