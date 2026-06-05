"""
Unit tests para el Renderizador (Hito 3.1)

Verificar que:
1. Los planes se renderizan correctamente
2. El camino se dibuja sin sobrescribir paredes
3. La salida visual es válida
4. Se puede comparar con salida esperada
"""

import pytest
import numpy as np
from src.renderizador import Renderizador, create_renderizador
from src.types import Plan


class TestRenderizadorBasic:
    """Tests básicos del Renderizador"""

    @pytest.fixture
    def renderizador(self):
        """Crear un renderizador para tests"""
        return create_renderizador(debug=False)

    @pytest.fixture
    def empty_grid(self):
        """Grid vacío (todos pisos)"""
        return np.full((64, 64), 3, dtype=np.int8)

    @pytest.fixture
    def simple_plan(self):
        """Plan simple: línea recta"""
        return Plan(
            actions=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            cost=4,
            valid=True
        )

    def test_renderizador_creation(self, renderizador):
        """Test: Crear renderizador"""
        assert renderizador is not None
        assert isinstance(renderizador, Renderizador)

    def test_render_simple_plan(self, renderizador, simple_plan, empty_grid):
        """Test: Renderizar plan simple"""
        rendered = renderizador.render(simple_plan, empty_grid)

        assert rendered.shape == (64, 64)
        assert rendered.dtype == np.int8

        # Verificar que el camino fue dibujado
        for pos in simple_plan.actions:
            row, col = pos
            assert rendered[row, col] == renderizador.CAMINO_VALUE

    def test_render_doesnt_modify_original(self, renderizador, simple_plan, empty_grid):
        """Test: render() no modifica grid original"""
        original_copy = np.array(empty_grid)

        renderizador.render(simple_plan, empty_grid)

        # Grid original no debe cambiar
        assert np.array_equal(empty_grid, original_copy)

    def test_render_empty_plan_raises_error(self, renderizador, empty_grid):
        """Test: Plan vacío levanta excepción"""
        empty_plan = Plan(actions=[], cost=0, valid=False)

        with pytest.raises(ValueError):
            renderizador.render(empty_plan, empty_grid)

    def test_render_wrong_grid_size_raises_error(self, renderizador, simple_plan):
        """Test: Grid de tamaño incorrecto levanta excepción"""
        bad_grid = np.zeros((32, 32), dtype=np.int8)

        with pytest.raises(ValueError, match="64×64"):
            renderizador.render(simple_plan, bad_grid)


class TestRenderizadorWithWalls:
    """Tests con paredes"""

    @pytest.fixture
    def renderizador(self):
        return create_renderizador(debug=False)

    @pytest.fixture
    def grid_with_walls(self):
        """Grid con paredes"""
        grid = np.full((64, 64), 3, dtype=np.int8)
        grid[0:5, 20:25] = 4  # Pared rectangular
        return grid

    @pytest.fixture
    def plan_avoiding_walls(self):
        """Plan que evita las paredes"""
        return Plan(
            actions=[(0, 0), (5, 0), (10, 0), (15, 0), (20, 0)],
            cost=4,
            valid=True
        )

    def test_render_skips_walls(self, renderizador, plan_avoiding_walls, grid_with_walls):
        """Test: No sobrescribir paredes"""
        rendered = renderizador.render(plan_avoiding_walls, grid_with_walls)

        # Paredes originales deben mantener su valor
        for i in range(0, 5):
            for j in range(20, 25):
                assert rendered[i, j] == 4  # Wall value

    def test_render_skips_positions_on_walls(self, renderizador, grid_with_walls):
        """Test: Posiciones sobre paredes no son dibujadas"""
        plan = Plan(
            actions=[(2, 22), (3, 22)],  # Posiciones que están en pared
            cost=1,
            valid=True
        )

        rendered = renderizador.render(plan, grid_with_walls)

        # Las posiciones sobre paredes no deberían cambiar
        for pos in plan.actions:
            row, col = pos
            assert rendered[row, col] == grid_with_walls[row, col]


class TestRenderizadorValidation:
    """Tests para validación de renders"""

    @pytest.fixture
    def renderizador(self):
        return create_renderizador(debug=False)

    @pytest.fixture
    def grid(self):
        return np.full((64, 64), 3, dtype=np.int8)

    @pytest.fixture
    def plan(self):
        return Plan(
            actions=[(0, 0), (5, 0), (10, 0), (10, 5), (10, 10)],
            cost=4,
            valid=True
        )

    def test_validate_correct_render(self, renderizador, grid, plan):
        """Test: Validar render correcto"""
        rendered = renderizador.render(plan, grid)

        is_valid, msg = renderizador.validate_render(rendered, plan, grid)
        assert is_valid, f"Validation failed: {msg}"

    def test_validate_wrong_shape(self, renderizador, plan):
        """Test: Rechazar grid con forma incorrecta"""
        bad_rendered = np.zeros((32, 32), dtype=np.int8)
        grid = np.full((64, 64), 3, dtype=np.int8)

        is_valid, msg = renderizador.validate_render(bad_rendered, plan, grid)
        assert not is_valid

    def test_validate_wrong_dtype(self, renderizador, grid, plan):
        """Test: Rechazar dtype incorrecto"""
        rendered = renderizador.render(plan, grid)
        rendered = rendered.astype(np.float32)  # Cambiar tipo

        is_valid, msg = renderizador.validate_render(rendered, plan, grid)
        assert not is_valid


class TestRenderizadorComparison:
    """Tests para comparación con salida esperada"""

    @pytest.fixture
    def renderizador(self):
        return create_renderizador(debug=False)

    def test_compare_identical_grids(self, renderizador):
        """Test: Grids idénticos tienen similitud 100%"""
        grid1 = np.full((64, 64), 3, dtype=np.int8)
        grid2 = np.full((64, 64), 3, dtype=np.int8)

        is_similar, score = renderizador.compare_with_expected(grid1, grid2)
        assert is_similar
        assert score == 1.0

    def test_compare_different_grids(self, renderizador):
        """Test: Grids diferentes tienen similitud menor"""
        grid1 = np.full((64, 64), 3, dtype=np.int8)
        grid2 = np.full((64, 64), 2, dtype=np.int8)

        is_similar, score = renderizador.compare_with_expected(grid1, grid2)
        assert not is_similar
        assert score == 0.0

    def test_compare_mostly_similar(self, renderizador):
        """Test: Grids muy similares pasan el threshold"""
        grid1 = np.full((64, 64), 3, dtype=np.int8)
        grid2 = np.full((64, 64), 3, dtype=np.int8)
        # Cambiar solo 5% de celdas
        for i in range(5):
            grid2[i, 0] = 2

        is_similar, score = renderizador.compare_with_expected(grid1, grid2, tolerance=0.94)
        assert is_similar  # 95% coincide, threshold es 94%


class TestRenderizadorAnalysis:
    """Tests para análisis de planes"""

    @pytest.fixture
    def renderizador(self):
        return create_renderizador(debug=False)

    def test_get_path_length(self, renderizador):
        """Test: Calcular longitud del camino"""
        plan = Plan(
            actions=[(0, 0), (5, 0), (10, 0), (15, 0), (20, 0)],
            cost=4,
            valid=True
        )

        length = renderizador.get_path_length(plan)
        assert length == 5

    def test_get_path_bounds(self, renderizador):
        """Test: Obtener límites del camino"""
        plan = Plan(
            actions=[(5, 10), (10, 15), (15, 20), (8, 12)],
            cost=3,
            valid=True
        )

        min_row, max_row, min_col, max_col = renderizador.get_path_bounds(plan)

        assert min_row == 5
        assert max_row == 15
        assert min_col == 10
        assert max_col == 20

    def test_get_path_bounds_empty_plan(self, renderizador):
        """Test: Límites de plan vacío"""
        plan = Plan(actions=[], cost=0, valid=False)

        bounds = renderizador.get_path_bounds(plan)
        assert bounds == (0, 0, 0, 0)


class TestRenderizadorEdgeCases:
    """Tests de casos extremos"""

    @pytest.fixture
    def renderizador(self):
        return create_renderizador(debug=False)

    def test_render_single_position(self, renderizador):
        """Test: Plan con una sola posición"""
        grid = np.full((64, 64), 3, dtype=np.int8)
        plan = Plan(actions=[(32, 32)], cost=0, valid=True)

        rendered = renderizador.render(plan, grid)

        assert rendered[32, 32] == renderizador.CAMINO_VALUE

    def test_render_out_of_bounds_positions(self, renderizador):
        """Test: Manejar posiciones fuera de límites"""
        grid = np.full((64, 64), 3, dtype=np.int8)
        plan = Plan(
            actions=[(0, 0), (100, 100), (10, 10)],  # (100,100) está fuera
            cost=2,
            valid=True
        )

        # Debería no lanzar excepción, solo ignorar posiciones fuera de límites
        rendered = renderizador.render(plan, grid)

        assert rendered[0, 0] == renderizador.CAMINO_VALUE
        assert rendered[10, 10] == renderizador.CAMINO_VALUE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
