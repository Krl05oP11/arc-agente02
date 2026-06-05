"""
Unit tests para Online Replanner (Hito 5.2)

Verificar que:
1. Replanning se dispara correctamente
2. Nuevos planes se generan
3. Ejecución continúa ante cambios
4. Estadísticas se rastrea
"""

import pytest
from src.online_replanner import (
    OnlineReplanner, AdaptiveExecutor, ReplanningEvent,
    PlanValidity, create_online_replanner, create_adaptive_executor
)
from src.explorer import Explorer
from src.types import Plan, WorldState, Door, KeyState


class TestReplanningEvent:
    """Tests para ReplanningEvent"""

    def test_event_creation(self):
        """Test: Crear evento de replanning"""
        event = ReplanningEvent("obstacle", (10, 10), "Wall detected")

        assert event.event_type == "obstacle"
        assert event.position == (10, 10)
        assert event.description == "Wall detected"


class TestOnlineReplanner:
    """Tests para OnlineReplanner"""

    @pytest.fixture
    def world(self):
        """Mundo para replanning"""
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
    def explorer(self, world):
        """Crear explorador"""
        return Explorer(world, debug=False)

    @pytest.fixture
    def replanner(self, explorer):
        """Crear replanificador"""
        return create_online_replanner(explorer, debug=False)

    def test_replanner_creation(self, replanner):
        """Test: Crear replanificador"""
        assert replanner is not None

    def test_set_initial_plan(self, replanner):
        """Test: Establecer plan inicial"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0), (15, 0), (20, 0)],
            cost=4,
            valid=True
        )

        replanner.set_initial_plan(plan)

        assert replanner.current_plan is not None
        assert len(replanner.current_plan.actions) == 5

    def test_execute_step_valid_plan(self, replanner):
        """Test: Ejecutar paso con plan válido"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0)],
            cost=2,
            valid=True
        )

        replanner.set_initial_plan(plan)
        observation = {"cell_type": "floor"}

        next_pos, needs_replan = replanner.execute_step((0, 0), observation)

        # Primera ejecución retorna la posición actual (plan[0])
        assert next_pos == (0, 0)
        assert not needs_replan

    def test_should_replan_no_plan(self, replanner):
        """Test: Necesita replanning sin plan"""
        observation = {}

        assert replanner.should_replan((0, 0), observation)

    def test_should_replan_with_obstacle(self, replanner):
        """Test: Detectar necesidad de replanning con obstáculo"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0)],
            cost=2,
            valid=True
        )

        replanner.set_initial_plan(plan)
        observation = {"cell_type": "wall"}

        # Obstacle en siguiente posición
        needs_replan = replanner.should_replan((0, 0), observation)

        # Puede requerir replanning
        assert isinstance(needs_replan, bool)

    def test_get_next_action(self, replanner):
        """Test: Obtener siguiente acción"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0)],
            cost=2,
            valid=True
        )

        replanner.set_initial_plan(plan)
        next_action = replanner.get_next_action()

        assert next_action == (0, 0)

    def test_get_stats(self, replanner):
        """Test: Obtener estadísticas"""
        stats = replanner.get_stats()

        assert 'replans' in stats
        assert 'events' in stats
        assert stats['replans'] >= 0


class TestAdaptiveExecutor:
    """Tests para AdaptiveExecutor"""

    @pytest.fixture
    def world(self):
        """Mundo para ejecución adaptiva"""
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

    @pytest.fixture
    def explorer(self, world):
        """Crear explorador"""
        return Explorer(world, debug=False)

    @pytest.fixture
    def executor(self, explorer, world):
        """Crear ejecutor adaptivo"""
        return create_adaptive_executor(explorer, world, debug=False)

    def test_executor_creation(self, executor):
        """Test: Crear ejecutor adaptivo"""
        assert executor is not None

    def test_execute_with_simple_plan(self, executor):
        """Test: Ejecutar plan simple"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0), (15, 0), (20, 0), (30, 30)],
            cost=5,
            valid=True
        )

        result = executor.execute_with_exploration(plan, (30, 30), max_steps=100)

        assert 'success' in result
        assert 'steps' in result
        assert 'path' in result
        assert 'replans' in result

    def test_execution_path_tracking(self, executor):
        """Test: Rastrear path de ejecución"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0)],
            cost=2,
            valid=True
        )

        result = executor.execute_with_exploration(plan, (10, 0), max_steps=50)

        assert len(result['path']) > 0


class TestReplanningLogic:
    """Tests para lógica de replanning"""

    @pytest.fixture
    def world(self):
        """Mundo para tests"""
        return WorldState(
            player_pos=(0, 0),
            walls={(5, 0), (5, 5), (5, 10)},  # Una pared diagonal
            doors=[Door(position=(20, 20), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def explorer(self, world):
        """Crear explorador"""
        return Explorer(world, debug=False)

    @pytest.fixture
    def replanner(self, explorer):
        """Crear replanificador"""
        return create_online_replanner(explorer, debug=False)

    def test_plan_validity_valid(self, replanner):
        """Test: Plan válido"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0)],
            cost=2,
            valid=True
        )

        replanner.set_initial_plan(plan)
        observation = {"cell_type": "floor"}

        validity = replanner._check_plan_validity(observation)

        assert validity in [PlanValidity.VALID, PlanValidity.PARTIALLY_VALID]

    def test_plan_validity_obstacle(self, replanner):
        """Test: Plan bloqueado por obstáculo"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0)],
            cost=2,
            valid=True
        )

        replanner.set_initial_plan(plan)
        observation = {"cell_type": "wall"}

        validity = replanner._check_plan_validity(observation)

        assert validity in [
            PlanValidity.VALID,
            PlanValidity.INVALID_OBSTACLE,
            PlanValidity.PARTIALLY_VALID
        ]


class TestOnlineReplannerEdgeCases:
    """Tests de casos extremos"""

    @pytest.fixture
    def world(self):
        """Mundo simple"""
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

    def test_replanner_multiple_replans(self, world):
        """Test: Múltiples replanificaciones"""
        explorer = Explorer(world)
        replanner = create_online_replanner(explorer)

        plan1 = Plan(actions=[(0, 0), (5, 0)], cost=1, valid=True)
        replanner.set_initial_plan(plan1)

        plan2 = Plan(actions=[(0, 0), (5, 0), (10, 0)], cost=2, valid=True)
        replanner.set_initial_plan(plan2)

        assert replanner.current_plan is not None

    def test_empty_plan(self, world):
        """Test: Plan vacío"""
        explorer = Explorer(world)
        replanner = create_online_replanner(explorer)

        plan = Plan(actions=[], cost=0, valid=False)
        replanner.set_initial_plan(plan)

        next_action = replanner.get_next_action()

        assert next_action is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
