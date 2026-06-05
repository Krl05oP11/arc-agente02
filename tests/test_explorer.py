"""
Unit tests para Explorer (Hito 5.1)

Verificar que:
1. Exploración funciona correctamente
2. Memoria se mantiene
3. Estrategias eligen targets correctamente
4. Progreso se rastrea
"""

import pytest
from src.explorer import (
    ExploredArea, ExplorationStrategy, Explorer,
    create_explorer
)
from src.types import WorldState, Door, KeyState, Rotator


class TestExploredArea:
    """Tests para ExploredArea"""

    def test_explored_area_creation(self):
        """Test: Crear área explorada"""
        area = ExploredArea()

        assert area is not None
        assert len(area.discovered_cells) == 0

    def test_discover_cell(self):
        """Test: Descubrir una celda"""
        area = ExploredArea()
        area.discover_cell((10, 10), "floor")

        assert (10, 10) in area.discovered_cells

    def test_discover_wall(self):
        """Test: Descubrir una pared"""
        area = ExploredArea()
        area.discover_cell((10, 10), "wall")

        assert (10, 10) in area.walls
        assert (10, 10) in area.discovered_cells

    def test_discover_rotator(self):
        """Test: Descubrir un rotador"""
        area = ExploredArea()
        rot = Rotator(position=(10, 10), rotator_type="SHAPE", rotator_id=101)
        area.discover_rotator(rot)

        assert 101 in area.rotators
        assert (10, 10) in area.discovered_cells

    def test_get_unknown_neighbors(self):
        """Test: Obtener vecinos desconocidos"""
        area = ExploredArea()
        area.discover_cell((0, 0), "floor")

        # Descubrir solo una celda, luego buscar vecinos desconocidos
        unknown = area.get_unknown_neighbors((0, 0))

        assert len(unknown) > 0

    def test_get_exploration_frontier(self):
        """Test: Obtener frontera de exploración"""
        area = ExploredArea()
        area.discover_cell((0, 0), "floor")
        area.discover_cell((5, 0), "floor")

        frontier = area.get_exploration_frontier()

        assert len(frontier) > 0

    def test_is_cell_explored(self):
        """Test: Verificar si celda fue explorada"""
        area = ExploredArea()
        area.discover_cell((10, 10), "floor")

        assert area.is_cell_explored((10, 10))
        assert not area.is_cell_explored((20, 20))


class TestExplorationStrategy:
    """Tests para ExplorationStrategy"""

    @pytest.fixture
    def setup(self):
        """Setup para tests"""
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
        area = ExploredArea(world)
        return area

    def test_breadth_first_strategy(self, setup):
        """Test: Estrategia BFS"""
        strategy = ExplorationStrategy(ExplorationStrategy.BREADTH_FIRST)
        target = strategy.choose_next_exploration_target((0, 0), setup)

        assert target is not None

    def test_depth_first_strategy(self, setup):
        """Test: Estrategia DFS"""
        strategy = ExplorationStrategy(ExplorationStrategy.DEPTH_FIRST)
        target = strategy.choose_next_exploration_target((0, 0), setup)

        # Puede ser None si no hay frontera
        if target:
            assert isinstance(target, tuple)

    def test_goal_oriented_strategy(self, setup):
        """Test: Estrategia orientada a objetivo"""
        strategy = ExplorationStrategy(ExplorationStrategy.GOAL_ORIENTED)
        target = strategy.choose_next_exploration_target(
            (0, 0), setup, known_goal=(50, 50)
        )

        if target:
            assert isinstance(target, tuple)


class TestExplorer:
    """Tests para Explorer"""

    @pytest.fixture
    def world(self):
        """Mundo para exploración"""
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

    def test_explorer_creation(self, world):
        """Test: Crear explorador"""
        explorer = create_explorer(world, debug=False)

        assert explorer is not None

    def test_update_with_observation(self, world):
        """Test: Actualizar con observación"""
        explorer = create_explorer(world)

        observation = {
            "cell_type": "floor",
            "content": "empty"
        }

        explorer.update_with_observation((5, 5), observation)

        assert explorer.is_explored((5, 5))

    def test_get_next_exploration_target(self, world):
        """Test: Obtener siguiente objetivo"""
        explorer = create_explorer(world)

        target = explorer.get_next_exploration_target((0, 0))

        if target:
            assert isinstance(target, tuple)
            assert 0 <= target[0] < 64
            assert 0 <= target[1] < 64

    def test_get_exploration_progress(self, world):
        """Test: Obtener progreso de exploración"""
        explorer = create_explorer(world)

        progress = explorer.get_exploration_progress()

        assert 'discovered_cells' in progress
        assert 'coverage' in progress
        assert 'frontier_size' in progress
        assert 0 <= progress['coverage'] <= 1

    def test_can_reach_goal_unknown(self, world):
        """Test: Goal desconocido retorna None"""
        explorer = create_explorer(world)

        reachable = explorer.can_reach_goal((0, 0), (50, 50))

        assert reachable is None

    def test_can_reach_goal_wall(self, world):
        """Test: Goal en pared es inalcanzable"""
        explorer = create_explorer(world)
        explorer.update_with_observation((50, 50), {"cell_type": "wall"})

        reachable = explorer.can_reach_goal((0, 0), (50, 50))

        assert reachable is False

    def test_can_reach_goal_known_floor(self, world):
        """Test: Goal en piso es alcanzable"""
        explorer = create_explorer(world)
        explorer.update_with_observation((50, 50), {"cell_type": "floor"})

        reachable = explorer.can_reach_goal((0, 0), (50, 50))

        assert reachable is True


class TestExplorationEdgeCases:
    """Tests de casos extremos"""

    def test_empty_world(self):
        """Test: Mundo vacío"""
        explorer = create_explorer(None)

        assert explorer is not None

    def test_full_exploration(self):
        """Test: Exploración completa (simulada)"""
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

        # Simular descubrimiento de muchas celdas
        for i in range(0, 64, 5):
            for j in range(0, 64, 5):
                explorer.update_with_observation((i, j), {"cell_type": "floor"})

        progress = explorer.get_exploration_progress()

        assert progress['discovered_cells'] > 100

    def test_different_strategies(self):
        """Test: Probar diferentes estrategias"""
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

        for strategy in [
            ExplorationStrategy.BREADTH_FIRST,
            ExplorationStrategy.DEPTH_FIRST,
            ExplorationStrategy.GOAL_ORIENTED
        ]:
            explorer = create_explorer(world, strategy=strategy)
            assert explorer is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
