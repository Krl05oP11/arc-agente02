"""
Unit tests para el Supervisor (Hito 3.2)

Verificar que:
1. Pipeline completo funciona end-to-end
2. Errores se manejan correctamente
3. Fallbacks funcionan cuando algo falla
4. Resultados son validados
"""

import pytest
import numpy as np
from src.supervisor import Supervisor, create_supervisor, PipelineResult
from src.types import Example, WorldState, Door, KeyState, Rotator
from src.inductor_reglas import DSLProgram, RuleType


class TestSupervisorBasic:
    """Tests básicos del Supervisor"""

    @pytest.fixture
    def supervisor(self):
        """Crear supervisor para tests"""
        return create_supervisor(debug=False)

    def test_supervisor_creation(self, supervisor):
        """Test: Crear supervisor"""
        assert supervisor is not None
        assert isinstance(supervisor, Supervisor)

    def test_pipeline_result_creation(self):
        """Test: Crear PipelineResult"""
        result = PipelineResult()

        assert not result.success
        assert result.rule is None
        assert result.plan is None
        assert len(result.errors) == 0

    def test_pipeline_result_string(self):
        """Test: String representation de PipelineResult"""
        result = PipelineResult()
        result.success = True

        str_repr = str(result)
        assert "SUCCESS" in str_repr


class TestSupervisorPipeline:
    """Tests de pipeline completo"""

    @pytest.fixture
    def supervisor(self):
        return create_supervisor(debug=False)

    @pytest.fixture
    def simple_example(self):
        """Ejemplo simple: shortest path"""
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
        return example

    def test_pipeline_simple_shortest_path(self, supervisor, simple_example):
        """Test: Pipeline completo para shortest_path"""
        test_grid = np.full((64, 64), 3, dtype=np.int8)

        # Pasar el test_world del ejemplo para asegurar consistencia
        result = supervisor.run([simple_example], test_grid, test_world=simple_example.world_state)

        assert result is not None
        assert result.success, f"Pipeline failed: {result.errors}"
        assert result.rule is not None
        assert "shortest_path" in result.rule.dsl_program
        assert result.plan is not None
        assert result.rendered_grid is not None

    def test_pipeline_with_rotators(self, supervisor):
        """Test: Pipeline con rotadores"""
        rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        rot2 = Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(1, 1, 0))],
            rotators=[rot1, rot2],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        example = Example(
            input_grid=np.full((64, 64), 3, dtype=np.int8),
            solution_path=[(0, 0), (5, 5), (10, 5), (20, 20)],
            world_state=world
        )

        test_grid = np.full((64, 64), 3, dtype=np.int8)

        result = supervisor.run([example], test_grid, test_world=world)

        assert result.success
        assert result.plan is not None
        assert len(result.plan.actions) > 0


class TestSupervisorValidation:
    """Tests para validación de resultados"""

    @pytest.fixture
    def supervisor(self):
        return create_supervisor(debug=False)

    def test_validate_successful_result(self, supervisor):
        """Test: Validar resultado exitoso"""
        result = PipelineResult()
        result.success = True
        result.rule = "mock_rule"
        result.plan = "mock_plan"
        result.rendered_grid = np.zeros((64, 64))

        is_valid, issues = supervisor.validate_result(result)
        assert is_valid
        assert len(issues) == 0

    def test_validate_failed_result(self, supervisor):
        """Test: Validar resultado fallido"""
        result = PipelineResult()
        result.success = False

        is_valid, issues = supervisor.validate_result(result)
        assert not is_valid
        assert len(issues) > 0


class TestSupervisorErrorHandling:
    """Tests para manejo de errores"""

    @pytest.fixture
    def supervisor(self):
        return create_supervisor(debug=False)

    def test_empty_examples_list(self, supervisor):
        """Test: Manejar lista vacía de ejemplos"""
        test_grid = np.full((64, 64), 3, dtype=np.int8)

        result = supervisor.run([], test_grid)

        assert not result.success
        assert len(result.errors) > 0

    def test_invalid_grid_size(self, supervisor):
        """Test: Manejar grid con tamaño incorrecto"""
        example = Example(
            input_grid=np.full((64, 64), 3, dtype=np.int8),
            solution_path=[(0, 0), (10, 10)],
            world_state=None
        )

        bad_grid = np.zeros((32, 32), dtype=np.int8)

        result = supervisor.run([example], bad_grid)

        assert not result.success or len(result.errors) > 0

    def test_pipeline_timing(self, supervisor):
        """Test: Registrar tiempos de ejecución"""
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

        result = supervisor.run([example], grid)

        assert 'total' in result.timing
        assert result.timing['total'] > 0


class TestSupervisorIntegration:
    """Tests de integración de fases"""

    @pytest.fixture
    def supervisor(self):
        return create_supervisor(debug=False)

    def test_inference_to_planning_flow(self, supervisor):
        """Test: Flujo de Fase 1 a Fase 2"""
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
            solution_path=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            world_state=world
        )

        test_grid = np.full((64, 64), 3, dtype=np.int8)

        result = supervisor.run([example], test_grid)

        # Verificar que Fase 1 generó regla
        assert result.rule is not None

        # Verificar que Fase 2 generó plan basado en la regla
        if result.success:
            assert result.plan is not None

    def test_planning_to_visualization_flow(self, supervisor):
        """Test: Flujo de Fase 2 a Fase 3"""
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
            solution_path=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            world_state=world
        )

        test_grid = np.full((64, 64), 3, dtype=np.int8)

        result = supervisor.run([example], test_grid)

        if result.success:
            # Verificar que plan fue renderizado
            assert result.rendered_grid is not None
            assert result.rendered_grid.shape == test_grid.shape


class TestSupervisorStats:
    """Tests para recolección de estadísticas"""

    @pytest.fixture
    def supervisor(self):
        return create_supervisor(debug=False)

    def test_stats_collection(self, supervisor):
        """Test: Recolectar estadísticas del pipeline"""
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
            solution_path=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            world_state=world
        )

        test_grid = np.full((64, 64), 3, dtype=np.int8)

        result = supervisor.run([example], test_grid)

        assert len(result.stats) > 0
        if result.success:
            assert 'rule_dsl' in result.stats
            assert 'plan_length' in result.stats
            assert 'rendered' in result.stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
