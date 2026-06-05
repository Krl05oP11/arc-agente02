"""
Unit tests para Multi-vida (Hito 3.3)

Verificar que:
1. Extended state se crea correctamente
2. Reset de vidas funciona
3. Multi-vida planning usa vidas eficientemente
4. Límite de vidas se respeta
"""

import pytest
from src.multi_vida import ExtendedState, MultiLifeStateGraph, create_multi_vida_graph
from src.types import WorldState, Door, KeyState
import numpy as np


class TestExtendedState:
    """Tests para ExtendedState"""

    def test_extended_state_creation(self):
        """Test: Crear ExtendedState"""
        state = ExtendedState(
            position=(10, 10),
            key_shape=1,
            key_color=2,
            key_rotation=3,
            energy=30,
            lives=2
        )

        assert state.position == (10, 10)
        assert state.energy == 30
        assert state.lives == 2

    def test_extended_state_to_base(self):
        """Test: Convertir ExtendedState a State base"""
        extended = ExtendedState(
            position=(10, 10),
            key_shape=1,
            key_color=2,
            key_rotation=3,
            energy=30,
            lives=2
        )

        base = extended.to_state()

        assert base.position == (10, 10)
        assert base.energy == 30
        # Lives no están en State base
        assert not hasattr(base, 'lives')

    def test_extended_state_equality(self):
        """Test: Igualdad de ExtendedState"""
        s1 = ExtendedState((0, 0), 0, 0, 0, 42, 3)
        s2 = ExtendedState((0, 0), 0, 0, 0, 42, 3)
        s3 = ExtendedState((0, 0), 0, 0, 0, 42, 2)

        assert s1 == s2
        assert s1 != s3

    def test_extended_state_hash(self):
        """Test: ExtendedState es hashable"""
        s1 = ExtendedState((0, 0), 0, 0, 0, 42, 3)
        s2 = ExtendedState((0, 0), 0, 0, 0, 42, 3)

        state_set = {s1, s2}
        assert len(state_set) == 1


class TestMultiLifeStateGraph:
    """Tests para MultiLifeStateGraph"""

    @pytest.fixture
    def world(self):
        """Mundo simple para tests"""
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
    def graph(self, world):
        """Crear MultiLifeStateGraph"""
        return create_multi_vida_graph(world, initial_lives=3, debug=False)

    def test_graph_creation(self, graph):
        """Test: Crear MultiLifeStateGraph"""
        assert graph is not None
        assert graph.initial_lives == 3

    def test_neighbors_with_energy(self, graph):
        """Test: Generar vecinos cuando hay energía"""
        state = ExtendedState(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=30,
            lives=3
        )

        neighbors = graph.neighbors_with_lives(state)

        assert len(neighbors) > 0
        # Los vecinos deben mantener vidas
        for next_state, _ in neighbors:
            assert next_state.lives == 3

    def test_neighbors_zero_energy_with_lives(self, graph):
        """Test: Reset cuando energía = 0 y quedan vidas"""
        state = ExtendedState(
            position=(5, 5),
            key_shape=1,
            key_color=1,
            key_rotation=1,
            energy=0,
            lives=2
        )

        neighbors = graph.neighbors_with_lives(state)

        # Debería haber un reset transition
        reset_found = False
        for next_state, cost in neighbors:
            if next_state.lives == 1 and next_state.energy == 42:
                reset_found = True
                # Reset debe volver a posición inicial
                assert next_state.position == graph.initial_position
                # Key state debe mantenerse
                assert next_state.key_shape == 1
                assert next_state.key_color == 1
                assert next_state.key_rotation == 1

        assert reset_found, "Reset transition not found"

    def test_neighbors_zero_energy_no_lives(self, graph):
        """Test: Sin vecinos cuando energía = 0 y no hay vidas"""
        state = ExtendedState(
            position=(5, 5),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=0,
            lives=1  # Última vida
        )

        neighbors = graph.neighbors_with_lives(state)

        # Sin vidas no hay vecinos
        assert len(neighbors) == 0

    def test_is_goal_with_lives_requires_energy(self, graph, world):
        """Test: Goal requiere energía > 0"""
        # Goal sin energía
        state_no_energy = ExtendedState(
            position=(10, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=0,
            lives=3
        )

        assert not graph.is_goal_with_lives(state_no_energy)

        # Goal con energía
        state_with_energy = ExtendedState(
            position=(10, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=10,
            lives=3
        )

        assert graph.is_goal_with_lives(state_with_energy)

    def test_can_reach_goal(self, graph):
        """Test: Verificar viabilidad de reach goal"""
        # Con vidas
        state_with_lives = ExtendedState(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42,
            lives=3
        )

        assert graph.can_reach_goal(state_with_lives, (10, 10))

        # Sin vidas
        state_no_lives = ExtendedState(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42,
            lives=0
        )

        assert not graph.can_reach_goal(state_no_lives, (10, 10))


class TestMultiLifePlanning:
    """Tests para planificación con múltiples vidas"""

    @pytest.fixture
    def limited_world(self):
        """Mundo donde la energía inicial es insuficiente"""
        return WorldState(
            player_pos=(0, 0),
            walls={
                # Pared que bloquea ruta directa
                (5, i) for i in range(0, 10)
            },
            doors=[Door(position=(20, 20), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=10  # Poca energía
        )

    @pytest.fixture
    def multi_graph(self, limited_world):
        return create_multi_vida_graph(limited_world, initial_lives=2, debug=False)

    def test_multiple_lives_needed(self, multi_graph):
        """Test: Reconocer cuando se necesitan múltiples vidas"""
        # Distancia a goal requiere ~24 pasos (con pared)
        # Energía inicial = 10, así que necesita al menos 2 vidas

        start = ExtendedState(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=10,
            lives=2
        )

        # Este estado debería poder alcanzar goal con 2 vidas
        # (primera vida llega a ~10 pasos, reset, segunda vida completa el camino)
        assert multi_graph.can_reach_goal(start, (20, 20))

    def test_insufficient_lives(self, multi_graph):
        """Test: Con cero vidas no se puede alcanzar goal"""
        start = ExtendedState(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=5,
            lives=0  # Sin vidas
        )

        # Sin vidas no alcanzable
        can_reach = multi_graph.can_reach_goal(start, (20, 20))
        assert not can_reach


class TestMultiLifeEdgeCases:
    """Tests de casos extremos"""

    @pytest.fixture
    def graph(self):
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
        return create_multi_vida_graph(world, initial_lives=3)

    def test_zero_initial_lives(self):
        """Test: Crear con cero vidas iniciales"""
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

        graph = create_multi_vida_graph(world, initial_lives=0)
        assert graph.initial_lives == 0

    def test_many_lives(self):
        """Test: Crear con muchas vidas"""
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

        graph = create_multi_vida_graph(world, initial_lives=99)
        assert graph.initial_lives == 99

    def test_energy_exactly_zero(self, graph):
        """Test: Energía exactamente cero"""
        state = ExtendedState(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=0,  # Exactamente cero
            lives=2
        )

        neighbors = graph.neighbors_with_lives(state)
        # Debería permitir reset
        assert any(n[0].lives == 1 for n in neighbors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
