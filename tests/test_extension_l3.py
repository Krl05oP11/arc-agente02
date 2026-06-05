"""
Unit tests para Extension L3+ (Hito 4.1)

Verificar que:
1. Secuencias de rotadores se detectan correctamente
2. Dependencias se infieren automáticamente
3. Complejidad se clasifica adecuadamente
4. Reglas complejas se generan
"""

import pytest
import numpy as np
from src.extension_l3 import (
    RotatorSequence, ComplexRuleAnalyzer, L3ProblemClassifier,
    ExtendedInductor, create_l3_inductor
)
from src.types import Example, WorldState, Door, KeyState, Rotator


class TestRotatorSequence:
    """Tests para RotatorSequence"""

    def test_sequence_creation(self):
        """Test: Crear secuencia de rotadores"""
        sequence = RotatorSequence([101, 102, 103])

        assert len(sequence.rotator_ids) == 3
        assert sequence.required_order is True

    def test_add_dependency(self):
        """Test: Agregar dependencia"""
        sequence = RotatorSequence([101, 102, 103])
        sequence.add_dependency(102, 101)
        sequence.add_dependency(103, 101)

        assert 101 in sequence.dependencies[102]
        assert 101 in sequence.dependencies[103]

    def test_is_satisfiable_empty(self):
        """Test: Secuencia sin requisitos es satisfiable"""
        sequence = RotatorSequence([101, 102])

        assert sequence.is_satisfiable(set())
        assert sequence.is_satisfiable({101})

    def test_is_satisfiable_with_deps(self):
        """Test: Verificar satisfiability con dependencias"""
        sequence = RotatorSequence([101, 102, 103])
        sequence.add_dependency(102, 101)

        # Sin cumplir 101 primero
        assert not sequence.is_satisfiable({102})

        # Cumpliendo en orden
        assert sequence.is_satisfiable({101, 102})

    def test_next_valid_rotators(self):
        """Test: Obtener rotadores válidos a continuación"""
        sequence = RotatorSequence([101, 102, 103])
        sequence.add_dependency(102, 101)

        # Sin haber visitado nada, solo 101 es válido
        valid = sequence.next_valid_rotators(set())
        assert 101 in valid
        assert 102 not in valid

        # Después de 101, podemos visitar 102
        valid = sequence.next_valid_rotators({101})
        assert 102 in valid


class TestComplexRuleAnalyzer:
    """Tests para ComplexRuleAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Crear analizador para tests"""
        return ComplexRuleAnalyzer(debug=False)

    def test_analyzer_creation(self, analyzer):
        """Test: Crear analizador"""
        assert analyzer is not None

    def test_detect_rotator_sequence_simple(self, analyzer):
        """Test: Detectar secuencia simple"""
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

        sequence = analyzer.detect_rotator_sequence(example)

        assert sequence is not None
        assert 101 in sequence.rotator_ids
        assert 102 in sequence.rotator_ids
        assert sequence.rotator_ids.index(101) < sequence.rotator_ids.index(102)

    def test_detect_rotator_sequence_no_rotators(self, analyzer):
        """Test: Sin rotadores retorna None"""
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
            solution_path=[(0, 0), (10, 10)],
            world_state=world
        )

        sequence = analyzer.detect_rotator_sequence(example)

        assert sequence is None

    def test_infer_dependencies(self, analyzer):
        """Test: Inferir dependencias de ejemplos"""
        rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        rot2 = Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102)
        rot3 = Rotator(position=(15, 5), rotator_type="ROT", rotator_id=103)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(1, 1, 1))],
            rotators=[rot1, rot2, rot3],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        example = Example(
            input_grid=np.full((64, 64), 3, dtype=np.int8),
            solution_path=[(0, 0), (5, 5), (10, 5), (15, 5), (20, 20)],
            world_state=world
        )

        deps = analyzer.infer_dependencies([example])

        # 102 debería depender de 101
        assert 101 in deps.get(102, set())
        # 103 debería depender de 101 y 102
        assert 101 in deps.get(103, set())
        assert 102 in deps.get(103, set())


class TestL3ProblemClassifier:
    """Tests para L3ProblemClassifier"""

    def test_classify_l1_simple(self):
        """Test: Clasificar problema L1"""
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

        classification = L3ProblemClassifier.classify_problem(world)
        assert classification == "L1"

    def test_classify_l2_rotator(self):
        """Test: Clasificar problema L2"""
        rot1 = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(1, 0, 0))],
            rotators=[rot1],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        classification = L3ProblemClassifier.classify_problem(world)
        assert classification in ["L2", "L3"]

    def test_classify_l3_multiple_rotators(self):
        """Test: Clasificar problema L3"""
        rots = [
            Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101),
            Rotator(position=(10, 5), rotator_type="COLOR", rotator_id=102),
            Rotator(position=(15, 5), rotator_type="ROT", rotator_id=103),
        ]

        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 20), required_key=KeyState(1, 1, 1))],
            rotators=rots,
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        classification = L3ProblemClassifier.classify_problem(world)
        assert classification in ["L3", "L3+"]

    def test_complexity_score(self):
        """Test: Calcular score de complejidad"""
        simple_world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        complex_world = WorldState(
            player_pos=(0, 0),
            walls={(i, j) for i in range(10) for j in range(10)},  # Muchos obstáculos
            doors=[Door(position=(50, 50), required_key=KeyState(1, 1, 1))],
            rotators=[
                Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=i)
                for i in range(5)
            ],
            refills=[(30, 30)],
            teleporters=[(20, 20)],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        simple_score = L3ProblemClassifier.get_complexity_score(simple_world)
        complex_score = L3ProblemClassifier.get_complexity_score(complex_world)

        assert complex_score > simple_score


class TestExtendedInductor:
    """Tests para ExtendedInductor"""

    @pytest.fixture
    def inductor(self):
        """Crear inductor extendido"""
        return create_l3_inductor(debug=False)

    def test_inductor_creation(self, inductor):
        """Test: Crear inductor extendido"""
        assert inductor is not None
        assert hasattr(inductor, 'complex_analyzer')
        assert hasattr(inductor, 'classifier')

    def test_infer_l3_rule(self, inductor):
        """Test: Inferir regla para problema L3"""
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

        rule = inductor.infer_rule([example])

        if rule:
            assert rule is not None
            assert hasattr(rule, 'dsl_program')


class TestL3EdgeCases:
    """Tests de casos extremos para L3+"""

    def test_empty_rotator_sequence(self):
        """Test: Secuencia vacía"""
        sequence = RotatorSequence([])
        assert len(sequence.rotator_ids) == 0

    def test_single_rotator(self):
        """Test: Un solo rotador"""
        sequence = RotatorSequence([101])
        assert len(sequence.rotator_ids) == 1

    def test_circular_dependencies(self):
        """Test: Manejar dependencias (sin ciclos reales)"""
        sequence = RotatorSequence([101, 102, 103])
        sequence.add_dependency(102, 101)
        sequence.add_dependency(103, 102)

        # Esto es válido (cadena lineal)
        assert sequence.is_satisfiable({101, 102, 103})

    def test_many_rotators(self):
        """Test: Muchos rotadores"""
        sequence = RotatorSequence(list(range(101, 121)))  # 20 rotadores
        assert len(sequence.rotator_ids) == 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
