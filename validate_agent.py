#!/usr/bin/env python3
"""
Complete Agent Validation Script

Ejecuta validación completa del agente y genera reporte de decisión
"""

import sys
from src.arc_test_bench import ARCTestBench
from src.agent_validator import AgentValidator, RealAgentWrapper, MockAgentWrapper
import json
from datetime import datetime


def print_header(title):
    """Imprimir header formateado"""
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75 + "\n")


def validate_with_mock():
    """Validar con agente mock (rápido)"""
    print_header("1️⃣ MOCK AGENT VALIDATION (Testing Infrastructure)")

    bench = ARCTestBench(num_problems=5, debug=False)

    print(f"✓ {len(bench.problems)} test problems cargados:\n")
    for i, p in enumerate(bench.problems, 1):
        print(f"  {i}. {p}")

    print("\n▶️  Ejecutando tests con Mock Agent...\n")
    results = bench.run_suite(MockAgentWrapper.simple_mock)

    print(bench.generate_report())

    validator = AgentValidator(agent_name="Mock Agent (Baseline)", debug=False)
    analysis = bench.get_analysis()
    analysis['agent'] = validator.agent_name

    print(validator.generate_validation_report(analysis))

    return analysis


def validate_with_real_agent():
    """Validar con agente real"""
    print_header("2️⃣ REAL AGENT VALIDATION (ARC-AGENTE02)")

    bench = ARCTestBench(num_problems=5, debug=False)

    print(f"✓ {len(bench.problems)} test problems cargados")
    print("✓ Inicializando agente real ARC-AGENTE02...\n")

    # Crear wrapper del agente real
    try:
        agent = RealAgentWrapper()
        if agent.supervisor is None:
            print("⚠️  Warning: No se pudo cargar supervisor")
            print("   Usando Mock Agent como fallback\n")
            agent = MockAgentWrapper()
            use_mock = True
        else:
            print("✓ Agente real cargado\n")
            use_mock = False
    except Exception as e:
        print(f"⚠️  Error cargando agente real: {e}")
        print("   Usando Mock Agent como fallback\n")
        agent = MockAgentWrapper()
        use_mock = True

    print("▶️  Ejecutando tests...\n")

    if use_mock:
        results = bench.run_suite(MockAgentWrapper.simple_mock)
    else:
        results = bench.run_suite(agent.predict)

    print(bench.generate_report())

    validator = AgentValidator(agent_name="ARC-AGENTE02 (Real)", debug=False)
    analysis = bench.get_analysis()
    analysis['agent'] = validator.agent_name
    analysis['is_mock'] = use_mock

    print(validator.generate_validation_report(analysis))

    return analysis


def compare_results(mock_analysis, real_analysis):
    """Comparar resultados entre mock y real"""
    print_header("3️⃣ COMPARATIVE ANALYSIS")

    mock_rate = mock_analysis.get('success_rate', 0)
    real_rate = real_analysis.get('success_rate', 0)
    diff = real_rate - mock_rate

    print("📊 Success Rate Comparison:\n")
    print(f"  Mock Agent:          {mock_rate:.1f}%")
    print(f"  Real Agent:          {real_rate:.1f}%")
    print(f"  Difference:          {diff:+.1f}%\n")

    if real_rate > mock_rate:
        print(f"✅ Real agent performs BETTER than mock (+{diff:.1f}%)")
    elif real_rate < mock_rate:
        print(f"⚠️  Real agent performs WORSE than mock ({diff:.1f}%)")
    else:
        print("≈ Same performance")

    print("\n📈 By Difficulty:\n")
    print("  Level    | Mock | Real | Δ")
    print("  ---------|------|------|----")
    for level in ['EASY', 'MEDIUM', 'HARD']:
        mock_count = 0
        real_count = real_analysis.get('by_difficulty', {}).get(level, 0)
        print(f"  {level:8} | {mock_count:4d} | {real_count:4d} | {real_count-mock_count:+d}")


def generate_decision_report(mock_analysis, real_analysis):
    """Generar reporte de decisión final"""
    print_header("4️⃣ FINAL DECISION REPORT")

    real_rate = real_analysis.get('success_rate', 0)
    is_mock = real_analysis.get('is_mock', False)

    print("📋 VALIDATION SUMMARY\n")
    print(f"  Timestamp:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Agent Tested:       {'Mock Agent' if is_mock else 'ARC-AGENTE02 (Real)'}")
    print(f"  Tests Run:          {real_analysis.get('total_tests', 0)}")
    print(f"  Tests Passed:       {real_analysis.get('passed', 0)}")
    print(f"  Success Rate:       {real_rate:.1f}%")
    print(f"  Avg Time/Test:      {real_analysis.get('avg_time', 0):.2f}s\n")

    print("=" * 75)
    print("🎯 RECOMMENDATION\n")

    if real_rate >= 80:
        print("✅ READY FOR SUBMISSION")
        print("   ├─ Performance exceeds baseline")
        print("   ├─ Confidence level: HIGH")
        print("   └─ Action: PROCEED TO GITHUB → KAGGLE\n")
        decision = "PROCEED"

    elif real_rate >= 60:
        print("⚠️  CAUTIOUS PROCEED")
        print("   ├─ Performance is acceptable")
        print("   ├─ Confidence level: MEDIUM")
        print("   └─ Action: SUBMIT BUT MONITOR CLOSELY\n")
        decision = "PROCEED_WITH_CAUTION"

    elif real_rate >= 40:
        print("🟡 CONDITIONAL")
        print("   ├─ Performance below ideal")
        print("   ├─ Confidence level: LOW")
        print("   └─ Action: FIX ISSUES, THEN SUBMIT\n")
        decision = "NEEDS_IMPROVEMENT"

    else:
        print("❌ NOT RECOMMENDED")
        print("   ├─ Performance insufficient")
        print("   ├─ Confidence level: NONE")
        print("   └─ Action: MAJOR IMPROVEMENTS NEEDED\n")
        decision = "HOLD"

    print("=" * 75 + "\n")

    return decision


def save_validation_results(mock_analysis, real_analysis, decision):
    """Guardar resultados de validación a archivo"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "mock_analysis": mock_analysis,
        "real_analysis": real_analysis,
        "decision": decision,
        "recommendation": {
            "PROCEED": "Ready for GitHub/Kaggle submission",
            "PROCEED_WITH_CAUTION": "Proceed but monitor performance",
            "NEEDS_IMPROVEMENT": "Fix issues before submission",
            "HOLD": "Major rework required",
        }.get(decision, "Unknown"),
    }

    with open('/tmp/validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("✓ Resultados guardados en: /tmp/validation_results.json\n")

    return results


def main():
    """Ejecutar validación completa"""
    print("\n")
    print("╔" + "=" * 73 + "╗")
    print("║" + " " * 15 + "🔍 ARC-AGENTE02 VALIDATION SUITE" + " " * 25 + "║")
    print("║" + " " * 11 + "Complete Performance Assessment Before Submission" + " " * 15 + "║")
    print("╚" + "=" * 73 + "╝")

    try:
        # Paso 1: Validar con Mock
        mock_analysis = validate_with_mock()

        # Paso 2: Validar con Real
        real_analysis = validate_with_real_agent()

        # Paso 3: Comparar
        compare_results(mock_analysis, real_analysis)

        # Paso 4: Decisión Final
        decision = generate_decision_report(mock_analysis, real_analysis)

        # Guardar resultados
        results = save_validation_results(mock_analysis, real_analysis, decision)

        # Summary
        print("📊 NEXT STEPS:\n")
        if decision == "PROCEED":
            print("1. ✅ Push to GitHub:")
            print("   ./push_to_github.sh\n")
            print("2. ✅ Join Kaggle competition:")
            print("   https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3\n")
            print("3. ✅ Create Notebook and submit")

        elif decision == "PROCEED_WITH_CAUTION":
            print("1. ⚠️  Monitor results closely if submitting")
            print("2. ⚠️  Be prepared to debug and iterate")
            print("3. ✅ Push to GitHub when ready")

        else:
            print("1. 🔧 Debug and improve the agent")
            print("2. 🔧 Run validation again")
            print("3. ⚠️  Only proceed when success rate ≥ 60%")

        print("\n" + "=" * 75 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
