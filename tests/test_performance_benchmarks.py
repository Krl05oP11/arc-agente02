"""
Performance Benchmarking Suite (Hito 6.2)

Establece líneas base y valida performance:
1. Módulo por módulo
2. Pipeline completo
3. Casos de uso
4. Bajo diferentes cargas
"""

import pytest
import numpy as np
import time
from src.supervisor import create_supervisor
from src.explorer import create_explorer, ExplorationStrategy
from src.online_replanner import create_online_replanner
from src.experience_learner import create_learning_agent, Experience
from src.mapeador import create_state_graph
from src.planificador import create_planner
from src.pattern_database import get_pattern_database
from src.renderizador import create_renderizador
from src.types import (
    WorldState, Door, KeyState, State, Plan
)


class PerformanceBenchmark:
    """Ejecutor de benchmarks"""

    def __init__(self, name: str, iterations: int = 3):
        self.name = name
        self.iterations = iterations
        self.times = []

    def measure(self, func, *args, **kwargs):
        """Medir tiempo de ejecución"""
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            self.times.append(elapsed)
        return result

    def get_stats(self):
        """Obtener estadísticas"""
        if not self.times:
            return None

        avg = sum(self.times) / len(self.times)
        min_t = min(self.times)
        max_t = max(self.times)

        return {
            'name': self.name,
            'avg_ms': avg * 1000,
            'min_ms': min_t * 1000,
            'max_ms': max_t * 1000,
            'iterations': self.iterations
        }


class TestModulePerformance:
    """Tests de performance de módulos individuales"""

    @pytest.fixture
    def world(self):
        """Mundo de test"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(30, 30), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    def test_perceptor_performance(self):
        """Benchmark: Perceptor (grid parsing)"""
        from src.perceptor import create_perceptor

        bench = PerformanceBenchmark("Perceptor", iterations=5)
        perceptor = create_perceptor(debug=False)
        grid = np.full((64, 64), 3, dtype=np.int8)

        bench.measure(perceptor.parse_grid, grid)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 100  # < 100ms target

    def test_inductor_performance(self):
        """Benchmark: Inductor (rule inference)"""
        from src.inductor_reglas import create_inductor
        from src.types import Example

        bench = PerformanceBenchmark("Inductor", iterations=3)
        inductor = create_inductor(debug=False)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        example = Example(
            input_grid=np.full((64, 64), 3, dtype=np.int8),
            solution_path=[(0, 0), (5, 0), (10, 0), (10, 10)],
            world_state=world
        )

        bench.measure(inductor.infer_rule, [example])

        stats = bench.get_stats()
        assert stats['avg_ms'] < 200  # < 200ms target

    def test_stategraph_performance(self, world):
        """Benchmark: StateGraph (neighbors generation)"""
        bench = PerformanceBenchmark("StateGraph", iterations=10)
        graph = create_state_graph(world, debug=False)

        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        bench.measure(graph.neighbors, state)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 10  # < 10ms target

    def test_planner_performance(self, world):
        """Benchmark: Planner (A* search)"""
        bench = PerformanceBenchmark("Planner", iterations=3)
        graph = create_state_graph(world, debug=False)
        planner = create_planner(graph, debug=False)

        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        bench.measure(planner.search, start, (0, 0, 0))

        stats = bench.get_stats()
        assert stats['avg_ms'] < 100  # < 100ms target

    def test_pattern_db_performance(self):
        """Benchmark: Pattern Database (lookup)"""
        bench = PerformanceBenchmark("PatternDB", iterations=100)
        db = get_pattern_database()

        # lookup expects tuples: (shape, color, rot)
        from_key = (0, 0, 0)
        to_key = (1, 1, 1)

        bench.measure(db.lookup, from_key, to_key)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 1  # < 1ms target

    def test_renderizador_performance(self):
        """Benchmark: Renderizador (visualization)"""
        bench = PerformanceBenchmark("Renderizador", iterations=5)
        renderer = create_renderizador(debug=False)

        plan = Plan(
            actions=[(i, i) for i in range(20)],
            cost=19,
            valid=True
        )
        grid = np.full((64, 64), 3, dtype=np.int8)

        bench.measure(renderer.render, plan, grid)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 50  # < 50ms target

    def test_explorer_performance(self):
        """Benchmark: Explorer (discovery update)"""
        bench = PerformanceBenchmark("Explorer", iterations=100)
        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )
        explorer = create_explorer(world)

        observation = {"cell_type": "floor"}

        bench.measure(explorer.update_with_observation, (10, 10), observation)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 5  # < 5ms target

    def test_learner_performance(self):
        """Benchmark: Learning Agent (experience recording)"""
        bench = PerformanceBenchmark("LearningAgent", iterations=100)
        agent = create_learning_agent()

        exp = Experience("wall", (10, 10), "obstacle")

        bench.measure(agent.learn_from_experience, exp)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 5  # < 5ms target


class TestPipelinePerformance:
    """Tests de performance del pipeline completo"""

    def test_full_pipeline_performance(self):
        """Benchmark: Pipeline completo"""
        from src.types import Example

        bench = PerformanceBenchmark("FullPipeline", iterations=1)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        example = Example(
            input_grid=np.full((64, 64), 3, dtype=np.int8),
            solution_path=[(0, 0), (5, 0), (10, 0), (15, 0), (20, 20)],
            world_state=world
        )

        supervisor = create_supervisor(debug=False)

        bench.measure(
            supervisor.run,
            [example],
            np.full((64, 64), 3, dtype=np.int8),
            test_world=world
        )

        stats = bench.get_stats()
        assert stats['avg_ms'] < 5000  # < 5 seconds target

    def test_exploration_performance(self):
        """Benchmark: Exploración completa"""
        bench = PerformanceBenchmark("FullExploration", iterations=1)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        explorer = create_explorer(world)

        def explore():
            for i in range(0, 64, 5):
                for j in range(0, 64, 5):
                    explorer.update_with_observation(
                        (i, j),
                        {"cell_type": "floor"}
                    )

        bench.measure(explore)

        stats = bench.get_stats()
        assert stats['avg_ms'] < 1000  # < 1 second target


class TestMemoryUsage:
    """Tests de uso de memoria"""

    def test_experience_memory_growth(self):
        """Benchmark: Crecimiento de memoria con experiencias"""
        agent = create_learning_agent(max_experiences=1000)

        for i in range(500):
            agent.learn_from_experience(
                Experience("wall" if i % 2 == 0 else "floor", (i % 64, i // 64), "obstacle")
            )

        # No debería crecer indefinidamente
        assert len(agent.memory.experiences) <= 500

    def test_explorer_memory_growth(self):
        """Benchmark: Crecimiento de memoria del explorador"""
        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        explorer = create_explorer(world)

        # Explorar todo
        for i in range(0, 64):
            for j in range(0, 64):
                explorer.update_with_observation((i, j), {"cell_type": "floor"})

        # Memoria debería ser razonable (~4096 celdas)
        assert len(explorer.explored_area.discovered_cells) <= 4096


class TestScalability:
    """Tests de escalabilidad"""

    def test_large_world_exploration(self):
        """Test: Exploración de mundo grande"""
        world = WorldState(
            player_pos=(0, 0),
            walls={(i, i) for i in range(0, 64, 2)},
            doors=[Door(position=(63, 63), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        explorer = create_explorer(world)

        start = time.perf_counter()

        # Exploración intensiva
        for i in range(0, 64, 2):
            for j in range(0, 64, 2):
                explorer.update_with_observation((i, j), {"cell_type": "floor"})

        elapsed = time.perf_counter() - start

        # Debería ser < 500ms
        assert elapsed < 0.5

    def test_many_replans(self):
        """Test: Múltiples replanificaciones"""
        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(30, 30), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        explorer = create_explorer(world)
        replanner = create_online_replanner(explorer)

        start = time.perf_counter()

        # Múltiples replanificaciones
        for i in range(10):
            plan = Plan(
                actions=[(j*2, 0) for j in range(15)],
                cost=14,
                valid=True
            )
            replanner.set_initial_plan(plan)

        elapsed = time.perf_counter() - start

        # Debería ser rápido
        assert elapsed < 1.0


class PerformanceReport:
    """Generador de reportes de performance"""

    @staticmethod
    def generate_summary(benchmarks):
        """Generar resumen de benchmarks"""
        report = "\n=== PERFORMANCE REPORT ===\n"

        for benchmark in benchmarks:
            stats = benchmark.get_stats()
            if stats:
                report += f"\n{stats['name']}:\n"
                report += f"  Average: {stats['avg_ms']:.2f}ms\n"
                report += f"  Min: {stats['min_ms']:.2f}ms\n"
                report += f"  Max: {stats['max_ms']:.2f}ms\n"

        return report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
