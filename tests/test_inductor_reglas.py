"""
Unit tests para el Inductor de Reglas (Hito 1.2)

Verificar que el Inductor puede:
1. Extraer secuencias de rotadores de caminos
2. Inferir reglas simples ("shortest_path", "visit_rotators_in_order")
3. Validar reglas contra ejemplos
"""

import pytest
from src.inductor_reglas import (
    InductorReglas, create_inductor, DSLProgram, RuleType
)
from src.types import Example, WorldState, Rotator, Door, KeyState
import numpy as np


class TestDSLProgram:
    """Tests para el DSL Program"""

    def test_shortest_path_dsl(self):
        """Test: DSL para shortest_path"""
        dsl = DSLProgram(RuleType.SHORTEST_PATH, {})
        assert "shortest_path" in str(dsl)

    def test_visit_rotators_dsl(self):
        """Test: DSL para visit_rotators_in_order"""
        dsl = DSLProgram(RuleType.VISIT_ROTATORS, {'rotator_order': [1, 2, 3]})
        assert "visit_rotators_in_order" in str(dsl)
        assert "→" in str(dsl)

    def test_dsl_to_rule(self):
        """Test: Convertir DSL a Rule"""
        dsl = DSLProgram(RuleType.SHORTEST_PATH, {})
        rule = dsl.to_rule()

        assert rule is not None
        assert rule.dsl_program == "shortest_path(start, door)"


class TestInductorBasic:
    """Tests básicos del Inductor"""

    @pytest.fixture
    def inductor(self):
        """Crear un Inductor para tests"""
        return create_inductor(debug=False)

    @pytest.fixture
    def example_shortest_path(self):
        """Ejemplo de camino más corto sin rotadores"""
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
        path = [(0, 0), (1, 0), (2, 0), (10, 0), (10, 10)]
        example = Example(
            input_grid=grid,
            solution_path=path,
            world_state=world
        )
        return example

    @pytest.fixture
    def example_with_rotators(self):
        """Ejemplo con rotadores a visitar"""
        grid = np.full((64, 64), 3, dtype=np.int8)

        # Crear 2 rotadores
        rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        rot2 = Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 10), required_key=KeyState(0, 0, 0))],
            rotators=[rot1, rot2],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        # Camino que visita rot1, luego rot2, luego puerta
        path = [(0, 0), (5, 5), (10, 5), (20, 10)]
        example = Example(
            input_grid=grid,
            solution_path=path,
            world_state=world
        )
        return example

    def test_inductor_creation(self, inductor):
        """Test: Crear un Inductor"""
        assert inductor is not None
        assert isinstance(inductor, InductorReglas)

    def test_extract_rotator_sequence_empty(self, inductor, example_shortest_path):
        """Test: Extraer secuencia vacía (sin rotadores)"""
        seq = inductor.extract_rotator_sequence(example_shortest_path)
        assert seq == []

    def test_extract_rotator_sequence_with_rotators(self, inductor, example_with_rotators):
        """Test: Extraer secuencia con rotadores"""
        seq = inductor.extract_rotator_sequence(example_with_rotators)
        assert len(seq) == 2
        assert seq[0] == 101
        assert seq[1] == 102

    def test_infer_shortest_path(self, inductor, example_shortest_path):
        """Test: Inferir regla shortest_path"""
        rule = inductor.infer_rule([example_shortest_path])

        assert rule is not None
        assert "shortest_path" in rule.dsl_program

    def test_infer_visit_rotators_in_order(self, inductor, example_with_rotators):
        """Test: Inferir regla visit_rotators_in_order"""
        rule = inductor.infer_rule([example_with_rotators])

        assert rule is not None
        assert "visit_rotators_in_order" in rule.dsl_program
        assert rule.rotator_order == [101, 102]


class TestInductorMultipleExamples:
    """Tests con múltiples ejemplos"""

    @pytest.fixture
    def inductor(self):
        return create_inductor(debug=False)

    @pytest.fixture
    def consistent_examples(self):
        """Múltiples ejemplos con el mismo patrón"""
        examples = []

        for ex_idx in range(2):
            grid = np.full((64, 64), 3, dtype=np.int8)

            rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
            rot2 = Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102)

            world = WorldState(
                player_pos=(0, 0),
                walls=set(),
                doors=[Door(position=(20, 10), required_key=KeyState(0, 0, 0))],
                rotators=[rot1, rot2],
                refills=[],
                teleporters=[],
                key_state=KeyState(0, 0, 0),
                energy=42
            )

            # Ambos ejemplos visitan los rotadores en el mismo orden
            path = [(0, 0), (5, 5), (10, 5), (20, 10)]
            example = Example(
                input_grid=grid,
                solution_path=path,
                world_state=world
            )
            examples.append(example)

        return examples

    def test_infer_multiple_consistent(self, inductor, consistent_examples):
        """Test: Inferir regla de múltiples ejemplos consistentes"""
        rule = inductor.infer_rule(consistent_examples)

        assert rule is not None
        assert "visit_rotators_in_order" in rule.dsl_program
        # Ambos ejemplos son idénticos
        assert rule.rotator_order == [101, 102]


class TestInductorValidation:
    """Tests para validación de reglas"""

    @pytest.fixture
    def inductor(self):
        return create_inductor(debug=False)

    def test_validate_rule_basic(self, inductor):
        """Test: Validar regla básica"""
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
            solution_path=[(0, 0), (10, 10)],
            world_state=world
        )

        rule = inductor.infer_rule([example])
        assert inductor.validate_rule(rule, [example])


class TestInductorEdgeCases:
    """Tests de casos extremos"""

    @pytest.fixture
    def inductor(self):
        return create_inductor(debug=False)

    def test_infer_empty_examples(self, inductor):
        """Test: Inferir de lista vacía"""
        rule = inductor.infer_rule([])
        assert rule is None

    def test_infer_none_examples(self, inductor):
        """Test: Inferir de None"""
        rule = inductor.infer_rule(None)
        assert rule is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
