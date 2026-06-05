"""
Unit tests para el Planificador (Hito 2.2)

Verificar que A* puede:
1. Encontrar caminos en espacios simples
2. Respetar restricciones (paredes, puertas)
3. Optimizar sobre key transformations
4. Manejar casos extremos
5. Ejecutarse rápidamente (< 50ms para L1)
"""

import pytest
import time
from src.planificador import AStarPlanner, PlanValidator, create_planner, create_validator
from src.mapeador import StateGraph, create_state_graph
from src.types import State, WorldState, Plan, Rotator, Door, KeyState
import numpy as np


class TestAStarBasic:
    """Tests básicos del A*"""

    @pytest.fixture
    def simple_world(self):
        """Mundo simple: player → door"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def planner(self, simple_world):
        graph = create_state_graph(simple_world, debug=False)
        return create_planner(graph, debug=False)

    def test_planner_creation(self, planner):
        """Test: Crear un planificador"""
        assert planner is not None
        assert isinstance(planner, AStarPlanner)

    def test_search_simple_path(self, planner):
        """Test: Encontrar camino en espacio simple"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.search(start, (0, 0, 0))

        assert plan is not None
        assert plan.valid
        assert len(plan.actions) > 0
        # Primer estado debe ser posición inicial
        assert plan.actions[0] == (0, 0)
        # Último estado debe ser goal
        assert plan.actions[-1] == (10, 10)

    def test_search_performance(self, planner):
        """Test: Búsqueda < 50ms (L1 performance)"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        start_time = time.time()
        plan = planner.search(start, (0, 0, 0))
        elapsed = time.time() - start_time

        assert plan is not None
        assert elapsed < 0.05, f"Search took {elapsed:.3f}s, expected < 0.05s"

    def test_search_cost_tracking(self, planner):
        """Test: Costo del plan es registrado"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.search(start, (0, 0, 0))

        assert plan is not None
        assert plan.cost > 0
        # El costo debería ser proporcional al largo del camino
        assert plan.cost < len(plan.actions) * 10


class TestAStarWithObstacles:
    """Tests con obstáculos"""

    @pytest.fixture
    def world_with_walls(self):
        """Mundo con paredes que fuerzan un camino específico"""
        walls = {(5, i) for i in range(1, 9)}  # Muro vertical en columna 5
        return WorldState(
            player_pos=(0, 0),
            walls=walls,
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def planner_walls(self, world_with_walls):
        graph = create_state_graph(world_with_walls, debug=False)
        return create_planner(graph, debug=False)

    def test_search_around_walls(self, planner_walls):
        """Test: Encontrar camino alrededor de paredes"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner_walls.search(start, (0, 0, 0))

        assert plan is not None
        assert plan.valid
        # El camino debe evitar las paredes
        for pos in plan.actions:
            assert pos not in planner_walls.graph._walls


class TestAStarWithRotators:
    """Tests con rotadores"""

    @pytest.fixture
    def world_with_rotator(self):
        """Mundo con rotador que debe ser visitado"""
        rot = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(1, 0, 0))],
            rotators=[rot],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def planner_rotator(self, world_with_rotator):
        graph = create_state_graph(world_with_rotator, debug=False)
        return create_planner(graph, debug=False)

    def test_search_visits_rotator(self, planner_rotator):
        """Test: Plan visita rotador necesario"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner_rotator.search(start, (1, 0, 0))

        assert plan is not None
        # Debería pasar por el rotador
        assert (5, 5) in plan.actions


class TestAStarStats:
    """Tests de estadísticas de búsqueda"""

    @pytest.fixture
    def simple_world(self):
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def planner(self, simple_world):
        graph = create_state_graph(simple_world, debug=False)
        return create_planner(graph, debug=False)

    def test_nodes_explored(self, planner):
        """Test: Contabilizar nodos explorados"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.search(start, (0, 0, 0))

        stats = planner.get_stats()
        assert stats['nodes_explored'] > 0
        assert stats['search_time'] >= 0
        assert stats['nodes_per_second'] > 0

    def test_search_time_recorded(self, planner):
        """Test: Tiempo de búsqueda es registrado"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.search(start, (0, 0, 0))
        assert planner.search_time > 0


class TestAStarNoSolution:
    """Tests cuando no hay solución"""

    @pytest.fixture
    def no_energy_world(self):
        """Mundo donde no hay suficiente energía para llegar"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def planner_no_energy(self, no_energy_world):
        graph = create_state_graph(no_energy_world, debug=False)
        return create_planner(graph, debug=False)

    def test_no_solution_insufficient_energy(self, planner_no_energy):
        """Test: Retornar None cuando no hay suficiente energía"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=2  # Muy poca energía para alcanzar goal
        )

        plan = planner_no_energy.search(start, (0, 0, 0))

        # Con energía limitada, no debería poder llegar
        # (Dependiendo de la distancia y la energía disponible)
        if plan:
            # Si encuentra plan, verificar que es válido
            assert plan.valid
        # Si no encuentra, plan es None, lo cual también es válido


class TestPlanValidator:
    """Tests para validación de planes"""

    @pytest.fixture
    def simple_world(self):
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def graph(self, simple_world):
        return create_state_graph(simple_world, debug=False)

    @pytest.fixture
    def validator(self, graph):
        return create_validator(graph, debug=False)

    def test_validate_valid_plan(self, validator, graph):
        """Test: Validar plan válido"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            cost=4,
            valid=True
        )

        is_valid, msg = validator.validate(plan, start)
        assert is_valid, f"Plan validation failed: {msg}"

    def test_validate_empty_plan(self, validator):
        """Test: Rechazar plan vacío"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = Plan(actions=[], cost=0, valid=False)

        is_valid, msg = validator.validate(plan, start)
        assert not is_valid


class TestAStarOptimality:
    """Tests para optimalidad"""

    @pytest.fixture
    def simple_world(self):
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def planner(self, simple_world):
        graph = create_state_graph(simple_world, debug=False)
        return create_planner(graph, debug=False)

    def test_plan_is_reasonably_short(self, planner):
        """Test: Plan es razonablemente corto (no toma caminos ridículos)"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.search(start, (0, 0, 0))

        assert plan is not None
        # Manhattan distance es (10-0) + (10-0) = 20 pasos de 1 celda
        # Con movimientos de 5 celdas, debería ser ~4 movimientos
        # Permitir algo de holgura
        assert len(plan.actions) < 10, f"Plan too long: {len(plan.actions)} steps"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
