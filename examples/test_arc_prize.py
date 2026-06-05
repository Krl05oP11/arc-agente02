#!/usr/bin/env python3
"""
Ejemplo: Testear ARC-AGENTE02 en ARC Prize Benchmark

Este script demuestra cómo ejecutar nuestro agente en el benchmark oficial
de ARC Prize 2026.

Requisitos:
    pip install arc-agi

Uso:
    python examples/test_arc_prize.py
"""

import sys
sys.path.insert(0, '/home/carlos/Projects/arc-agente02')

from src.arc_prize_adapter import ArcPrizeAgent, test_connection


def main():
    print("\n" + "="*60)
    print("🎮 ARC PRIZE BENCHMARK TEST")
    print("="*60)

    # 1. Test de conexión
    print("\n📡 1. Verificando conexión a ARC Prize...")
    if not test_connection(game_name="ls20", level_idx=0):
        print("❌ No se pudo conectar. Instalar con: pip install arc-agi")
        return 1

    # 2. Crear agente
    print("\n🤖 2. Creando agente...")
    agent = ArcPrizeAgent(
        game_name="ls20",
        level_idx=0,
        debug=True
    )

    # 3. Ejecutar benchmark
    print("\n⚙️  3. Ejecutando con estrategia aleatoria (demo)...")
    result = agent.run(max_steps=50, strategy="random")

    # 4. Mostrar resultados
    print("\n📊 4. RESULTADOS")
    print("-" * 60)
    print(f"Status:      {result['status']}")
    print(f"Pasos:       {result['steps']}/{50}")
    print(f"Juego:       {result['game']}")
    print(f"Nivel:       {result['level']}")
    print(f"Estrategia:  {result['strategy']}")

    if result['scorecard']:
        print("\n🏆 SCORECARD")
        for key, value in result['scorecard'].items():
            print(f"   {key}: {value}")

    # 5. Summary
    summary = agent.get_summary()
    print("\n📈 RESUMEN")
    print(f"Total pasos:   {summary['total_steps']}")
    print(f"Estado final:  {summary['final_status']}")
    print(f"Acciones:      {summary['actions'][:5]}..." if len(summary['actions']) > 5 else f"Acciones:      {summary['actions']}")

    print("\n" + "="*60)
    print("✅ Test completado")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nInstalar toolkit con:")
        print("   pip install arc-agi")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrumpido por usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
