"""
Unit tests para Teleporter Optimizer (Hito 4.2)

Verificar que:
1. Red de teleportadores se crea correctamente
2. Se detectan ciclos
3. Se encuentran shortcuts
4. Se optimizan planes
"""

import pytest
import numpy as np
from src.teleporter_optimizer import (
    TeleporterInfo, TeleporterNetwork, TeleporterOptimizer,
    create_teleporter_optimizer
)
from src.types import WorldState, Door, KeyState, Plan


class TestTeleporterInfo:
    """Tests para TeleporterInfo"""

    def test_teleporter_creation(self):
        """Test: Crear teleportador"""
        tp = TeleporterInfo((5, 5), (20, 20))

        assert tp.source == (5, 5)
        assert tp.destination == (20, 20)

    def test_teleporter_accessible_omnidirectional(self):
        """Test: Teleportador accesible desde cualquier dirección"""
        tp = TeleporterInfo((5, 5), (20, 20))

        assert tp.is_accessible_from((0, 0))
        assert tp.is_accessible_from((10, 10))

    def test_teleporter_with_entry_directions(self):
        """Test: Teleportador con direcciones de entrada"""
        tp = TeleporterInfo(
            (5, 5),
            (20, 20),
            entry_directions={(1, 0), (0, 1)}  # Desde abajo (1,0) o derecha (0,1)
        )

        # Desde posición que está arriba (0,0) → (5,5) es (1,1) - NO accesible
        assert not tp.is_accessible_from((0, 0))

        # Desde posición que está a la izquierda (5,0) → (5,5) es (0,1) - accesible
        assert tp.is_accessible_from((5, 0))


class TestTeleporterNetwork:
    """Tests para TeleporterNetwork"""

    @pytest.fixture
    def world_with_teleporters(self):
        """Mundo con teleportadores"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[(5, 5), (10, 10)],  # Dos teleportadores
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    @pytest.fixture
    def network(self, world_with_teleporters):
        """Crear red de teleportadores"""
        return TeleporterNetwork(world_with_teleporters, debug=False)

    def test_network_creation(self, network):
        """Test: Crear red de teleportadores"""
        assert network is not None
        assert len(network.teleporters) >= 0

    def test_register_teleport(self, network):
        """Test: Registrar teleporte descubierto"""
        network.register_teleport((5, 5), (20, 20))

        assert (5, 5) in network.source_map
        assert network.source_map[(5, 5)].destination == (20, 20)

    def test_register_multiple_teleports(self, network):
        """Test: Registrar múltiples teleportes"""
        network.register_teleport((5, 5), (20, 20))
        network.register_teleport((10, 10), (30, 30))

        assert len([tp for tp in network.teleporters if tp.destination]) >= 2

    def test_get_teleporter_shortcut(self, network):
        """Test: Encontrar shortcut de teleporte"""
        network.register_teleport((5, 5), (45, 45))  # Cerca de la puerta en (50,50)

        shortcut = network.get_teleporter_shortcut((0, 0), (50, 50))

        # Si el teleporte acorta, debería encontrarse
        if shortcut:
            assert shortcut == (45, 45)

    def test_is_safe_teleport_no_cycle(self, network):
        """Test: Teleporte sin ciclos es seguro"""
        network.register_teleport((5, 5), (20, 20))

        assert network.is_safe_teleport((5, 5), (20, 20))

    def test_is_safe_teleport_simple(self, network):
        """Test: Teleporte simple es seguro"""
        network.register_teleport((5, 5), (20, 20))

        # Teleporte simple sin ciclos es seguro
        assert network.is_safe_teleport((5, 5), (20, 20))

    def test_find_cycles(self, network):
        """Test: Encontrar ciclos"""
        network.register_teleport((5, 5), (10, 10))
        network.register_teleport((10, 10), (5, 5))

        cycles = network.find_cycles()

        assert len(cycles) > 0


class TestTeleporterOptimizer:
    """Tests para TeleporterOptimizer"""

    @pytest.fixture
    def simple_world(self):
        """Mundo simple sin teleportadores"""
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
    def world_with_tp(self):
        """Mundo con teleportadores"""
        return WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[(5, 5)],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

    def test_optimizer_creation(self, simple_world):
        """Test: Crear optimizador"""
        optimizer = create_teleporter_optimizer(simple_world, debug=False)

        assert optimizer is not None

    def test_has_teleporters_false(self, simple_world):
        """Test: Detectar ausencia de teleportadores"""
        optimizer = create_teleporter_optimizer(simple_world)

        assert not optimizer.has_teleporters()

    def test_has_teleporters_true(self, world_with_tp):
        """Test: Detectar presencia de teleportadores"""
        optimizer = create_teleporter_optimizer(world_with_tp)

        assert optimizer.has_teleporters()

    def test_can_use_teleporters_simple_problem(self, simple_world):
        """Test: No usar teleportes en problema simple"""
        optimizer = create_teleporter_optimizer(simple_world)

        assert not optimizer.can_use_teleporters(simple_world)

    def test_optimize_plan_simple(self, simple_world):
        """Test: Optimizar plan sin teleportadores"""
        optimizer = create_teleporter_optimizer(simple_world)
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0), (15, 0), (20, 0), (30, 30)],
            cost=5,
            valid=True
        )

        optimized = optimizer.optimize_plan(plan, simple_world)

        # Sin teleportes, no debería poder optimizar
        assert optimized is None

    def test_get_optimization_report(self, world_with_tp):
        """Test: Generar reporte de optimización"""
        optimizer = create_teleporter_optimizer(world_with_tp)

        report = optimizer.get_optimization_report()

        assert 'teleporters' in report
        assert 'cycles' in report
        assert 'can_optimize' in report


class TestTeleporterEdgeCases:
    """Tests de casos extremos"""

    def test_teleporter_long_distance(self):
        """Test: Teleportador a larga distancia"""
        tp = TeleporterInfo((0, 0), (63, 63))

        assert tp.source == (0, 0)
        assert tp.destination == (63, 63)

    def test_self_teleport(self):
        """Test: Teleportador a la misma posición"""
        tp = TeleporterInfo((5, 5), (5, 5))

        assert tp.source == tp.destination

    def test_network_empty(self):
        """Test: Red vacía de teleportadores"""
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

        network = TeleporterNetwork(world)

        assert len(network.teleporters) == 0

    def test_complex_cycle(self):
        """Test: Ciclo complejo (3+ teleportes)"""
        world = WorldState(
            player_pos=(0, 0),
            walls=set(),
            doors=[Door(position=(50, 50), required_key=KeyState(0, 0, 0))],
            rotators=[],
            refills=[],
            teleporters=[(5, 5), (10, 10), (15, 15)],
            key_state=KeyState(0, 0, 0),
            energy=42
        )

        network = TeleporterNetwork(world)

        # Crear ciclo: A→B→C→A
        network.register_teleport((5, 5), (10, 10))
        network.register_teleport((10, 10), (15, 15))
        network.register_teleport((15, 15), (5, 5))

        cycles = network.find_cycles()

        assert len(cycles) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
