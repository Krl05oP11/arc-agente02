"""
Unit tests para el Perceptor (Hito 1.1)

Verificar que el Perceptor puede:
1. Parsear grids 64×64
2. Identificar paredes correctamente
3. Extraer entidades del grid
4. Integrar con el juego real
"""

import pytest
import numpy as np
from src.perceptor import Perceptor, create_perceptor
from src.types import WorldState, KeyState


class TestPerceptorBasic:
    """Tests básicos del Perceptor"""

    @pytest.fixture
    def perceptor(self):
        """Crear un Perceptor para tests"""
        return create_perceptor(debug=False)

    @pytest.fixture
    def empty_grid(self):
        """Grid vacío (todos pisos, valor 3)"""
        grid = np.full((64, 64), 3, dtype=np.int8)
        return grid

    @pytest.fixture
    def grid_with_walls(self):
        """Grid con algunas paredes"""
        grid = np.full((64, 64), 3, dtype=np.int8)
        # Agregar paredes en una línea
        grid[10, 10:20] = 4  # Pared horizontal
        grid[20:30, 15] = 5  # Pared vertical
        return grid

    def test_perceptor_creation(self, perceptor):
        """Test: Crear un Perceptor"""
        assert perceptor is not None
        assert isinstance(perceptor, Perceptor)

    def test_parse_empty_grid(self, perceptor, empty_grid):
        """Test: Parsear grid vacío sin paredes"""
        world = perceptor.parse_grid(empty_grid)

        assert isinstance(world, WorldState)
        assert len(world.walls) == 0
        assert world.player_pos == (0, 0)  # Placeholder
        assert world.energy == 42

    def test_identify_walls(self, perceptor, grid_with_walls):
        """Test: Identificar paredes correctamente"""
        world = perceptor.parse_grid(grid_with_walls)

        # Verificar paredes identificadas
        assert len(world.walls) > 0
        # Línea horizontal en fila 10, columnas 10-19
        for col in range(10, 20):
            assert (10, col) in world.walls
        # Línea vertical en columna 15, filas 20-29
        for row in range(20, 30):
            assert (row, 15) in world.walls

    def test_grid_dimension_check(self, perceptor):
        """Test: Rechazar grids con dimensiones incorrectas"""
        bad_grid = np.zeros((32, 32), dtype=np.int8)

        with pytest.raises(ValueError, match="64×64"):
            perceptor.parse_grid(bad_grid)

    def test_extract_key_panel(self, perceptor, empty_grid):
        """Test: Extraer estado de llave"""
        key_state = perceptor.extract_key_panel(empty_grid)

        assert isinstance(key_state, KeyState)
        # Por ahora debería retornar estado inicial (0,0,0)
        assert key_state.shape_id == 0
        assert key_state.color_id == 0
        assert key_state.rotation_id == 0


class TestPerceptorIntegration:
    """Tests de integración con el juego real"""

    @pytest.mark.skip(reason="Requiere arc_agi y env disponibles")
    def test_parse_real_game_grid(self):
        """Test: Parsear grid real del juego ls20"""
        try:
            from arc_agi import Arcade
            import os

            ENV_DIR = os.path.expanduser('~/arc_env_files/ls20')
            arcade = Arcade(environments_dir=ENV_DIR)
            env = arcade.make('ls20')
            obs = env.reset()

            perceptor = create_perceptor(debug=True)
            grid = np.array(obs.frame[0], dtype=np.int8)

            world = perceptor.parse_grid(grid)

            # Verificaciones básicas
            assert isinstance(world, WorldState)
            assert len(world.walls) > 0  # Debería haber paredes
            assert world.energy == 42

        except ImportError:
            pytest.skip("arc_agi no disponible")

    @pytest.mark.skip(reason="Requiere integración con game object")
    def test_identify_entities_from_game(self):
        """Test: Identificar entidades del objeto Game real"""
        # Este test requiere acceso a game._levels[0] y game.gudziatsk
        # Se implementará cuando se integre completamente con el juego
        pass


class TestPerceptorEdgeCases:
    """Tests de casos extremos"""

    @pytest.fixture
    def perceptor(self):
        return create_perceptor(debug=False)

    def test_all_walls_grid(self, perceptor):
        """Test: Grid completamente lleno de paredes"""
        grid = np.full((64, 64), 4, dtype=np.int8)
        world = perceptor.parse_grid(grid)

        # Todas las celdas deberían ser paredes
        assert len(world.walls) == 64 * 64

    def test_mixed_wall_values(self, perceptor):
        """Test: Grid con valores mixtos de paredes (4 y 5)"""
        grid = np.full((64, 64), 3, dtype=np.int8)
        # Mezclar valores 4 y 5
        grid[0:10, 0:10] = 4
        grid[20:30, 20:30] = 5

        world = perceptor.parse_grid(grid)

        # Ambos valores deberían ser identificados como paredes
        assert len(world.walls) == 10 * 10 + 10 * 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
