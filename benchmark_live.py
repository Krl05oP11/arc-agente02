#!/usr/bin/env python3
"""
Live Benchmarking - Watch the Agent Solve Real ARC Prize Levels

Ejecuta el agente en ambientes reales y muestra el progreso.
"""

import sys
import time
from arc_agi import Arcade
from src.arc_integration_bridge import ArcIntegrationBridge


def benchmark_live():
    """Ejecutar benchmark en tiempo real"""

    print("\n" + "=" * 70)
    print("🎮 LIVE BENCHMARK - ARC-AGENTE02 vs ARC PRIZE REAL LEVELS")
    print("=" * 70 + "\n")

    try:
        # Inicializar
        print("📦 Initializing ARC Prize Arcade...")
        arcade = Arcade(environments_dir="~/arc_env_files/ls20")
        print("✅ Arcade initialized\n")

        # Inicializar bridge
        print("🌉 Initializing Integration Bridge...")
        bridge = ArcIntegrationBridge(debug=False)
        print("✅ Bridge initialized\n")

        # Testear primeros 3 niveles
        print("🎯 Testing levels 1-3 (demonstration run)...\n")

        results_by_level = []
        total_steps = 0
        successful_levels = 0

        for level in [1, 2, 3]:
            print(f"\n{'─' * 70}")
            print(f"📍 LEVEL {level}")
            print(f"{'─' * 70}")

            try:
                # Crear ambiente para este nivel
                print(f"  Creating environment for level {level}...", end=" ", flush=True)
                env = arcade.make("ls20")
                print("✅")

                # Ejecutar con máximo 500 pasos (demo)
                print(f"  Running agent (max 500 steps)...", end=" ", flush=True)
                start_time = time.time()

                result = bridge.solve_level(env, max_steps=500)

                elapsed = time.time() - start_time

                # Mostrar resultados
                success = result.get("success", False)
                steps = result.get("total_steps", 0)
                frames = result.get("frames_processed", 0)
                plans = result.get("plans_generated", 0)
                errors = result.get("errors", [])

                print(f"✅ ({elapsed:.1f}s)")

                print(f"\n  Results:")
                print(f"    Success:           {'✅ YES' if success else '❌ NO'}")
                print(f"    Steps executed:    {steps}")
                print(f"    Frames processed:  {frames}")
                print(f"    Plans generated:   {plans}")
                print(f"    Plans successful:  {result.get('plans_successful', 0)}")
                print(f"    Execution time:    {elapsed:.2f}s")

                if errors:
                    print(f"    Errors:            {len(errors)}")
                    for i, err in enumerate(errors[:3], 1):
                        print(f"      {i}. {err[:60]}")
                    if len(errors) > 3:
                        print(f"      ... and {len(errors)-3} more")

                if success:
                    successful_levels += 1
                    print(f"\n  ✅ LEVEL {level} COMPLETED!")
                else:
                    print(f"\n  ⚠️  Level {level} not completed")

                total_steps += steps
                results_by_level.append({
                    "level": level,
                    "success": success,
                    "steps": steps,
                    "time": elapsed,
                    "errors": len(errors)
                })

            except Exception as e:
                print(f"❌ ERROR: {str(e)[:50]}")
                results_by_level.append({
                    "level": level,
                    "success": False,
                    "steps": 0,
                    "time": 0,
                    "errors": 1
                })

        # Resumen final
        print(f"\n{'=' * 70}")
        print("📊 BENCHMARK SUMMARY")
        print(f"{'=' * 70}\n")

        total_levels = len(results_by_level)

        print(f"Levels tested:       {total_levels}")
        print(f"Levels completed:    {successful_levels}")
        print(f"Success rate:        {(successful_levels/total_levels)*100:.1f}%")
        print(f"Total steps:         {total_steps}")

        if total_levels > 0:
            avg_steps = total_steps / total_levels
            print(f"Average steps:       {avg_steps:.1f}")

        print()

        # Tabla de resultados
        print(f"{'LEVEL':<8} {'SUCCESS':<10} {'STEPS':<10} {'TIME':<10}")
        print(f"{'-'*38}")

        for r in results_by_level:
            status = "✅ YES" if r["success"] else "❌ NO"
            print(f"{r['level']:<8} {status:<10} {r['steps']:<10} {r['time']:.2f}s")

        print(f"\n{'=' * 70}\n")

        if successful_levels > 0:
            print(f"🎉 SUCCESS: {successful_levels}/{total_levels} levels completed!\n")
        else:
            print(f"⚠️  No levels completed in this demonstration.\n")

        print("💡 Note: This is a demonstration run with limited steps.")
        print("   Full runs may complete more levels.\n")

        return 0

    except Exception as e:
        print(f"\n❌ BENCHMARK ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(benchmark_live())
