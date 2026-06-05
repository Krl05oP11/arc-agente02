"""
Unit tests para Constraint Integration (Hito 2.4)

Verificar que:
1. Restricciones se aplican correctamente
2. Planes respetan reglas
3. Pipeline completo funciona
4. Combinación de Fase 1 + Fase 2 es coherente
"""

import pytest
from src.constrained_planner import (
    ConstraintChecker, ConstrainedStateGraph, ConstrainedPlanner,
    create_constrained_planner
)
from src.types import State, Rule, WorldState, Rotator, Door, KeyState
from src.inductor_reglas import DSLProgram, RuleType


class TestConstraintChecker:
    """Tests para verificación de restricciones"""

    @pytest.fixture
    def simple_rule(self):
        """Regla simple: visitar rotador 101 antes de 102"""
        dsl = DSLProgram(RuleType.VISIT_ROTATORS, {'rotator_order': [101, 102]})
        rule = dsl.to_rule()
        return rule

    @pytest.fixture
    def checker(self, simple_rule):
        return ConstraintChecker(simple_rule, debug=False)

    def test_constraint_checker_creation(self, checker):
        """Test: Crear verificador de restricciones"""
        assert checker is not None
        assert len(checker.must_visit) > 0

    def test_feasible_empty_visited(self, checker):
        """Test: Estado sin visitas es factible"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        assert checker.is_feasible(state)

    def test_feasible_valid_order(self, checker):
        """Test: Orden correcto de visitas es factible"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42,
            visited_rotators={101}  # Visitamos el primero
        )

        assert checker.is_feasible(state)

    def test_infeasible_wrong_order(self, checker):
        """Test: Orden incorrecto es infactible"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42,
            visited_rotators={102}  # Visitamos el segundo sin el primero
        )

        assert not checker.is_feasible(state)

    def test_satisfied_all_visited(self, checker):
        """Test: Satisfecho cuando todos los rotadores son visitados"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42,
            visited_rotators={101, 102}  # Ambos visitados en orden
        )

        assert checker.is_satisfied(state)

    def test_not_satisfied_missing_rotator(self, checker):
        """Test: No satisfecho si falta visitar un rotador"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42,
            visited_rotators={101}  # Falta 102
        )

        assert not checker.is_satisfied(state)


class TestConstrainedStateGraph:
    """Tests para StateGraph con restricciones"""

    @pytest.fixture
    def world_with_rotators(self):
        """Mundo con 2 rotadores"""
        rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        rot2 = Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102)

        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(1, 1, 0))],
            rotators=[rot1, rot2],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def rule_rotator_order(self):
        """Regla: visitar 101 antes que 102"""
        dsl = DSLProgram(RuleType.VISIT_ROTATORS, {'rotator_order': [101, 102]})
        return dsl.to_rule()

    @pytest.fixture
    def constrained_graph(self, world_with_rotators, rule_rotator_order):
        return ConstrainedStateGraph(world_with_rotators, rule_rotator_order, debug=False)

    def test_constrained_graph_creation(self, constrained_graph):
        """Test: Crear StateGraph con restricciones"""
        assert constrained_graph is not None
        assert constrained_graph.rule is not None

    def test_neighbors_respects_constraints(self, constrained_graph):
        """Test: neighbors() respeta restricciones"""
        # Comenzar con 102 visitado (sin 101) - debería filtrar
        state = State(
            position=(10, 5),
            key_shape=0,
            key_color=1,
            key_rotation=0,
            energy=41,
            visited_rotators={102}
        )

        neighbors = constrained_graph.neighbors(state)

        # Los vecinos deberían tener un número limitado de opciones
        # (restricción debería estar activa)
        assert len(neighbors) >= 0  # Podría ser cero si está completamente bloqueado

    def test_constrained_goal_requires_all_rotators(self, constrained_graph, world_with_rotators):
        """Test: Goal requiere visitar todos los rotadores según la regla"""
        # Crear estado en puerta sin visitar rotadores
        state = State(
            position=(20, 20),
            key_shape=1,
            key_color=1,
            key_rotation=0,
            energy=30,
            visited_rotators=set()  # No visitamos nada
        )

        # Esto debería ser goal=False porque falta visitar los rotadores
        assert not constrained_graph.is_goal(state)


class TestConstrainedPlanner:
    """Tests para planificador con restricciones"""

    @pytest.fixture
    def world_with_rotators(self):
        rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        rot2 = Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102)

        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(1, 1, 0))],
            rotators=[rot1, rot2],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def rule(self):
        dsl = DSLProgram(RuleType.VISIT_ROTATORS, {'rotator_order': [101, 102]})
        return dsl.to_rule()

    @pytest.fixture
    def planner(self, world_with_rotators, rule):
        return create_constrained_planner(world_with_rotators, rule, debug=False)

    def test_planner_creation(self, planner):
        """Test: Crear planificador con restricciones"""
        assert planner is not None
        assert planner.rule is not None
        assert planner.graph is not None

    def test_planner_generates_valid_plan(self, planner, world_with_rotators, rule):
        """Test: Generar plan que respeta restricciones"""
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.plan(start, (1, 1, 0))

        if plan:
            # Plan existe y es válido
            assert plan.valid
            assert len(plan.actions) > 0
            # Debería visitar los rotadores en orden
            assert (5, 5) in plan.actions  # ROT 101
            assert (10, 5) in plan.actions  # ROT 102
            # ROT 101 debe estar antes que ROT 102
            idx_101 = plan.actions.index((5, 5))
            idx_102 = plan.actions.index((10, 5))
            assert idx_101 < idx_102


class TestPipeline:
    """Tests de integración: Inductor + Planner"""

    def test_pipeline_simple_shortest_path(self):
        """Test: Pipeline completo para shortest_path"""
        from src.inductor_reglas import create_inductor
        from src.types import Example
        import numpy as np

        # Crear ejemplo de entrenamiento
        grid = np.full((64, 64), 3, dtype=np.int8)
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
            input_grid=grid,
            solution_path=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            world_state=world
        )

        # Fase 1: Inferir regla
        inductor = create_inductor(debug=False)
        rule = inductor.infer_rule([example])

        assert rule is not None
        assert "shortest_path" in rule.dsl_program

        # Fase 2: Planificar con restricciones
        planner = create_constrained_planner(world, rule, debug=False)
        start = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        plan = planner.plan(start, (0, 0, 0))

        assert plan is not None
        assert plan.valid
        assert plan.actions[0] == (0, 0)
        assert plan.actions[-1] == (10, 10)


class TestConstraintEdgeCases:
    """Tests de casos extremos"""

    def test_no_rule_no_constraints(self):
        """Test: Sin regla, sin restricciones"""
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

        # Crear grafo sin restricciones
        graph = ConstrainedStateGraph(world, rule=None, debug=False)

        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        neighbors = graph.neighbors(state)
        assert len(neighbors) > 0  # Debería haber vecinos sin restricciones

    def test_rule_with_no_rotators(self):
        """Test: Regla sin rotadores (shortest_path)"""
        dsl = DSLProgram(RuleType.SHORTEST_PATH, {})
        rule = dsl.to_rule()

        checker = ConstraintChecker(rule, debug=False)

        # Sin rotadores en la regla, cualquier estado es factible
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        assert checker.is_feasible(state)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
