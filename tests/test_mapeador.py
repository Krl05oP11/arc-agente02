"""
Unit tests para el Mapeador (Hito 2.1)

Verificar que el StateGraph puede:
1. Generar transiciones correctas para movimientos
2. Manejar rotadores (transforman llave)
3. Manejar teletransportadores
4. Validar puertas (key matching)
5. Manejar refills (energía)
"""

import pytest
from src.mapeador import StateGraph, create_state_graph
from src.types import State, WorldState, Rotator, Door, KeyState, Teleporter
import numpy as np


class TestStateGraphBasic:
    """Tests básicos del StateGraph"""

    @pytest.fixture
    def empty_world(self):
        """Mundo vacío sin obstáculos"""
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
    def state_graph(self, empty_world):
        """Crear un StateGraph para tests"""
        return create_state_graph(empty_world, debug=False)

    def test_state_graph_creation(self, state_graph):
        """Test: Crear un StateGraph"""
        assert state_graph is not None
        assert isinstance(state_graph, StateGraph)

    def test_neighbors_simple_movement(self, state_graph):
        """Test: Movimiento simple en 4 direcciones"""
        state = State(
            position=(10, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        neighbors = state_graph.neighbors(state)

        # Debería haber hasta 4 vecinos (UP, DOWN, LEFT, RIGHT)
        assert len(neighbors) > 0
        assert len(neighbors) <= 4

        # Verificar que todos los vecinos son válidos
        for next_state, cost in neighbors:
            assert isinstance(next_state, State)
            assert cost == 1  # Costo de movimiento

    def test_neighbors_energy_deduction(self, state_graph):
        """Test: Energía se deduce correctamente"""
        state = State(
            position=(10, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=5  # Energía baja
        )

        neighbors = state_graph.neighbors(state)

        # Todos los vecinos deberían tener 1 menos de energía
        for next_state, cost in neighbors:
            assert next_state.energy == 4

    def test_neighbors_no_energy(self, state_graph):
        """Test: No hay movimiento sin energía"""
        state = State(
            position=(10, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=0  # Sin energía
        )

        neighbors = state_graph.neighbors(state)

        # No debería haber vecinos
        assert len(neighbors) == 0

    def test_neighbors_boundary(self, state_graph):
        """Test: Respetar límites del grid (64×64)"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        neighbors = state_graph.neighbors(state)

        # En esquina, como máximo 2 movimientos válidos
        assert len(neighbors) <= 2


class TestStateGraphWalls:
    """Tests con paredes"""

    @pytest.fixture
    def world_with_walls(self):
        """Mundo con paredes"""
        walls = {
            (10, 10),  # Pared en el camino directo
            (10, 11),
            (10, 12),
        }
        return WorldState(
            player_pos=(0, 0),
            walls=walls,
            doors=[Door(position=(20, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def state_graph_walls(self, world_with_walls):
        return create_state_graph(world_with_walls, debug=False)

    def test_neighbors_blocked_by_wall(self, state_graph_walls):
        """Test: Paredes bloquean movimiento"""
        state = State(
            position=(9, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        neighbors = state_graph_walls.neighbors(state)

        # No debería haber movimiento DOWN (hacia pared en 10, 10)
        for next_state, _ in neighbors:
            assert next_state.position != (10, 10)


class TestStateGraphRotators:
    """Tests con rotadores"""

    @pytest.fixture
    def world_with_rotator(self):
        """Mundo con un rotador SHAPE"""
        rot = Rotator(position=(5, 5), rotator_type="SHAPE", rotator_id=101)
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 10), required_key=KeyState(0, 0, 0))],
            rotators=[rot],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def state_graph_rotator(self, world_with_rotator):
        return create_state_graph(world_with_rotator, debug=False)

    def test_rotator_transforms_key(self, state_graph_rotator):
        """Test: Rotador transforma la llave"""
        state = State(
            position=(0, 5),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        # Mover a posición del rotador
        neighbors = state_graph_rotator.neighbors(state)

        # Buscar el movimiento hacia el rotador
        rotator_transition = None
        for next_state, _ in neighbors:
            if next_state.position == (5, 5):
                rotator_transition = next_state
                break

        assert rotator_transition is not None
        # La llave SHAPE debe cambiar
        assert rotator_transition.key_shape != 0

    def test_rotator_visited_tracking(self, state_graph_rotator):
        """Test: Registrar rotadores visitados"""
        state = State(
            position=(0, 5),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        neighbors = state_graph_rotator.neighbors(state)

        # Buscar transición hacia rotador
        for next_state, _ in neighbors:
            if next_state.position == (5, 5):
                assert 101 in next_state.visited_rotators


class TestStateGraphDoors:
    """Tests con puertas"""

    @pytest.fixture
    def world_with_locked_door(self):
        """Mundo con puerta que requiere key específica"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(10, 10), required_key=KeyState(2, 2, 2))],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def state_graph_locked_door(self, world_with_locked_door):
        return create_state_graph(world_with_locked_door, debug=False)

    def test_door_blocks_wrong_key(self, state_graph_locked_door):
        """Test: Puerta bloquea con llave incorrecta"""
        state = State(
            position=(9, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        neighbors = state_graph_locked_door.neighbors(state)

        # No debería haber movimiento hacia la puerta (key no coincide)
        for next_state, _ in neighbors:
            assert next_state.position != (10, 10)

    def test_door_allows_correct_key(self, state_graph_locked_door):
        """Test: Puerta permite con llave correcta"""
        # Los movimientos son en incrementos de 5, así que usar posición compatible
        state = State(
            position=(5, 10),
            key_shape=2,
            key_color=2,
            key_rotation=2,
            energy=42
        )

        neighbors = state_graph_locked_door.neighbors(state)

        # Debería haber movimiento hacia la puerta (DOWN mueve a 5+5=10)
        can_reach_door = any(next_state.position == (10, 10) for next_state, _ in neighbors)
        assert can_reach_door


class TestStateGraphRefills:
    """Tests con refills"""

    @pytest.fixture
    def world_with_refill(self):
        """Mundo con un refill de energía"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(20, 10), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[(5, 5)],
            teleporters=[],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def state_graph_refill(self, world_with_refill):
        return create_state_graph(world_with_refill, debug=False)

    def test_refill_restores_energy(self, state_graph_refill):
        """Test: Refill restaura energía a 42"""
        state = State(
            position=(0, 5),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=5  # Energía baja
        )

        neighbors = state_graph_refill.neighbors(state)

        # Buscar movimiento hacia refill
        for next_state, _ in neighbors:
            if next_state.position == (5, 5):
                # Energía debería ser restaurada a 42, no deducida
                assert next_state.energy == 42


class TestStateGraphGoal:
    """Tests para detección de goal"""

    @pytest.fixture
    def state_graph(self):
        return create_state_graph(
            WorldState(
                player_pos=(0, 0),
                walls=set(),
                doors=[Door(position=(10, 10), required_key=KeyState(1, 1, 1))],
                rotators=[],
                refills=[],
                teleporters=[],
                key_state=KeyState(0, 0, 0),
                energy=42
            ),
            debug=False
        )

    def test_goal_detection_success(self, state_graph):
        """Test: Detectar goal cuando key coincide"""
        state = State(
            position=(10, 10),
            key_shape=1,
            key_color=1,
            key_rotation=1,
            energy=42
        )

        assert state_graph.is_goal(state) == True

    def test_goal_detection_failure_position(self, state_graph):
        """Test: No goal si posición es incorrecta"""
        state = State(
            position=(5, 5),
            key_shape=1,
            key_color=1,
            key_rotation=1,
            energy=42
        )

        assert state_graph.is_goal(state) == False

    def test_goal_detection_failure_key(self, state_graph):
        """Test: No goal si key no coincide"""
        state = State(
            position=(10, 10),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        assert state_graph.is_goal(state) == False


class TestStateGraphHeuristic:
    """Tests para heurística A*"""

    @pytest.fixture
    def state_graph(self):
        return create_state_graph(
            WorldState(
                player_pos=(0, 0),
                walls=set(),
                doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
                rotators=[],
                refills=[],
                teleporters=[],
                key_state=KeyState(0, 0, 0),
                energy=42
            ),
            debug=False
        )

    def test_heuristic_admissible(self, state_graph):
        """Test: Heurística es admisible (nunca overestima)"""
        state = State(
            position=(0, 0),
            key_shape=0,
            key_color=0,
            key_rotation=0,
            energy=42
        )

        h = state_graph.heuristic(state, (0, 0, 0))

        # Heurística debería ser positiva
        assert h > 0

        # Heurística debería ser razonable (< distancia Manhattan / 5)
        manhattan = abs(50 - 0) + abs(50 - 0)
        assert h <= manhattan


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
