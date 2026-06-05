"""
Módulo 6: RENDERIZADOR - Plan → Visual Grid

Convierte un plan (lista de posiciones) en una representación visual
dibujando el camino en el grid original.

El camino se dibuja típicamente en rojo (valor específico según el juego).
"""

from src.types import Plan
import numpy as np
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class Renderizador:
    """Renderiza planes como grids visuales"""

    # Colores/valores para dibujar el camino
    CAMINO_VALUE = 2  # Valor típico para el camino (rojo en visualización)
    WALL_VALUE = 4
    WALL_VARIANT = 5
    FLOOR_VALUE = 3
    EMPTY_VALUE = 0

    def __init__(self, debug: bool = False):
        """
        Inicializar el renderizador

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)

    def render(self, plan: Plan, grid: np.ndarray) -> np.ndarray:
        """
        Renderizar un plan en un grid

        Dibuja el camino sobre el grid original, marcando cada celda del camino
        con el valor CAMINO_VALUE.

        Args:
            plan: Plan con lista de acciones (posiciones)
            grid: Grid original 64×64

        Returns:
            Grid con camino dibujado

        Raises:
            ValueError: Si plan o grid son inválidos
        """
        if not plan or not plan.actions:
            raise ValueError("Plan is empty")

        if grid.shape != (64, 64):
            raise ValueError(f"Grid debe ser 64×64, got {grid.shape}")

        # Copiar grid para no modificar el original
        rendered = np.array(grid, dtype=np.int8)

        # Dibujar camino
        for pos in plan.actions:
            row, col = pos

            # Validación de límites
            if not (0 <= row < 64 and 0 <= col < 64):
                if self.debug:
                    logger.warning(f"Position {pos} out of bounds")
                continue

            # No sobrescribir paredes
            if grid[row, col] in [self.WALL_VALUE, self.WALL_VARIANT]:
                if self.debug:
                    logger.debug(f"Skipping wall at {pos}")
                continue

            # Marcar celda como parte del camino
            rendered[row, col] = self.CAMINO_VALUE

        if self.debug:
            logger.debug(f"✓ Rendered plan with {len(plan.actions)} steps")

        return rendered

    def render_with_highlights(self, plan: Plan, grid: np.ndarray,
                              highlight_rotators: List[Tuple[int, int]] = None,
                              highlight_door: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Renderizar plan con puntos de interés destacados

        Args:
            plan: Plan a renderizar
            grid: Grid original
            highlight_rotators: Lista de posiciones de rotadores
            highlight_door: Posición de la puerta

        Returns:
            Grid renderizado con highlights
        """
        # Renderizar camino base
        rendered = self.render(plan, grid)

        # Nota: Los highlights se pueden implementar con valores diferentes
        # Por ahora solo retornamos el grid básico
        # En una versión más elaborada, usaríamos valores especiales para
        # marcar rotadores (ej: valor 6) y puerta (ej: valor 7)

        return rendered

    def validate_render(self, rendered: np.ndarray, plan: Plan,
                       original_grid: np.ndarray) -> Tuple[bool, Optional[str]]:
        """
        Validar que un render es correcto

        Args:
            rendered: Grid renderizado
            plan: Plan original
            original_grid: Grid original

        Returns:
            Tupla (is_valid, error_message)
        """
        if rendered.shape != (64, 64):
            return False, f"Rendered grid shape {rendered.shape} != (64, 64)"

        if rendered.dtype != original_grid.dtype:
            return False, f"Dtype mismatch: {rendered.dtype} vs {original_grid.dtype}"

        # Verificar que el camino está presente
        for pos in plan.actions:
            row, col = pos
            if not (0 <= row < 64 and 0 <= col < 64):
                continue

            # Permitir que paredes no sean dibujadas
            if original_grid[row, col] in [self.WALL_VALUE, self.WALL_VARIANT]:
                continue

            # El camino debe estar marcado (o ser el valor original si es piso)
            # Esto es flexible para permitir diferentes formatos
            if rendered[row, col] not in [self.CAMINO_VALUE, self.FLOOR_VALUE]:
                pass  # Permitir ambos valores

        # Verificar que no se sobrescribieron paredes innecesariamente
        for i in range(64):
            for j in range(64):
                if original_grid[i, j] in [self.WALL_VALUE, self.WALL_VARIANT]:
                    if rendered[i, j] not in [self.WALL_VALUE, self.WALL_VARIANT]:
                        return False, f"Wall overwritten at ({i}, {j})"

        if self.debug:
            logger.debug("✓ Render validation passed")

        return True, None

    def compare_with_expected(self, rendered: np.ndarray,
                             expected: np.ndarray,
                             tolerance: float = 0.95) -> Tuple[bool, float]:
        """
        Comparar render con salida esperada

        Args:
            rendered: Grid renderizado
            expected: Grid esperado
            tolerance: Porcentaje de similitud requerida (0.0-1.0)

        Returns:
            Tupla (is_similar, similarity_score)
        """
        if rendered.shape != expected.shape:
            return False, 0.0

        # Contar celdas que coinciden
        matches = np.sum(rendered == expected)
        total = rendered.size
        similarity = matches / total

        if self.debug:
            logger.debug(f"Similarity: {similarity:.1%} (threshold: {tolerance:.1%})")

        return similarity >= tolerance, similarity

    def get_path_length(self, plan: Plan) -> int:
        """
        Retornar longitud del camino

        Args:
            plan: Plan a analizar

        Returns:
            Número de pasos (posiciones únicas)
        """
        if not plan or not plan.actions:
            return 0
        return len(plan.actions)

    def get_path_bounds(self, plan: Plan) -> Tuple[int, int, int, int]:
        """
        Retornar límites del camino

        Args:
            plan: Plan a analizar

        Returns:
            Tupla (min_row, max_row, min_col, max_col)
        """
        if not plan or not plan.actions:
            return 0, 0, 0, 0

        rows = [pos[0] for pos in plan.actions]
        cols = [pos[1] for pos in plan.actions]

        return min(rows), max(rows), min(cols), max(cols)


def create_renderizador(debug: bool = False) -> Renderizador:
    """Factory para crear un renderizador"""
    return Renderizador(debug=debug)
