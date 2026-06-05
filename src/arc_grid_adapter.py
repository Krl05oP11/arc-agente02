"""
Grid Adapter - Mapeo entre formatos ARC-AGENTE02 y ARC Prize

Traduce grillas entre los dos sistemas para integración completa.
"""

import numpy as np
from typing import Tuple, Optional


class GridAdapter:
    """Adaptador para convertir grillas entre ARC-AGENTE02 y ARC Prize"""

    # ARC Prize usa 64x64 con escala 5px
    # ARC-AGENTE02 usa coordenadas directas (row, col)
    GRID_SIZE = 64
    CELL_SCALE = 5  # ARC Prize multiplica por 5

    @staticmethod
    def arc_prize_to_arc_agente(grid_array: np.ndarray) -> np.ndarray:
        """
        Convertir grid de ARC Prize a ARC-AGENTE02 format

        ARC Prize: (H, W) array de 0-15
        ARC-AGENTE02: (H, W) array de 0-15
        (directa, solo asegurar tipo)
        """
        if grid_array is None:
            return None

        return np.asarray(grid_array, dtype=np.int8)

    @staticmethod
    def arc_agente_to_arc_prize(grid_array: np.ndarray) -> np.ndarray:
        """
        Convertir grid de ARC-AGENTE02 a ARC Prize format

        ARC-AGENTE02: (H, W) array de 0-15
        ARC Prize: (H, W) array de 0-15
        (directa, solo asegurar tipo)
        """
        if grid_array is None:
            return None

        return np.asarray(grid_array, dtype=np.int8)

    @staticmethod
    def grid_position_to_game_action(
        current_pos: Tuple[int, int],
        target_pos: Tuple[int, int]
    ) -> Optional[str]:
        """
        Convertir posición target a GameAction

        Args:
            current_pos: (row, col) posición actual del jugador
            target_pos: (row, col) posición objetivo

        Returns:
            Nombre de acción: "ACTION1" (UP), "ACTION2" (DOWN), etc.
        """
        dr = target_pos[0] - current_pos[0]
        dc = target_pos[1] - current_pos[1]

        # Mapeo: ARC Prize usa grid estándar
        # ACTION1 = UP    = (-5, 0)
        # ACTION2 = DOWN  = (+5, 0)
        # ACTION3 = LEFT  = (0, -5)
        # ACTION4 = RIGHT = (0, +5)

        if dr < 0 and dc == 0:  # Moving up
            return "ACTION1"
        elif dr > 0 and dc == 0:  # Moving down
            return "ACTION2"
        elif dr == 0 and dc < 0:  # Moving left
            return "ACTION3"
        elif dr == 0 and dc > 0:  # Moving right
            return "ACTION4"
        else:
            # Diagonal o salto (teleporte)
            # Priorizar por distancia
            if abs(dr) > abs(dc):
                return "ACTION2" if dr > 0 else "ACTION1"
            else:
                return "ACTION4" if dc > 0 else "ACTION3"

    @staticmethod
    def game_position_to_grid_position(
        game_pos: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Convertir posición de ARC Prize a grid coordinates

        ARC Prize: (x, y) en 5px units
        ARC-AGENTE02: (row, col) en grid cells
        """
        x, y = game_pos
        # x = col * 5, y = row * 5
        row = y // GridAdapter.CELL_SCALE
        col = x // GridAdapter.CELL_SCALE
        return (row, col)

    @staticmethod
    def grid_position_to_game_position(
        grid_pos: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Convertir posición de grid a ARC Prize coordinates

        ARC-AGENTE02: (row, col) en grid cells
        ARC Prize: (x, y) en pixels (5px scale)
        """
        row, col = grid_pos
        x = col * GridAdapter.CELL_SCALE + GridAdapter.CELL_SCALE // 2
        y = row * GridAdapter.CELL_SCALE + GridAdapter.CELL_SCALE // 2
        return (x, y)

    @staticmethod
    def validate_grid(grid_array: np.ndarray) -> bool:
        """
        Validar que grid sea válido

        Args:
            grid_array: Grid a validar

        Returns:
            True si válido
        """
        if grid_array is None:
            return False

        if not isinstance(grid_array, np.ndarray):
            return False

        if len(grid_array.shape) != 2:
            return False

        H, W = grid_array.shape
        if H != GridAdapter.GRID_SIZE or W != GridAdapter.GRID_SIZE:
            return False

        # Validar valores en rango 0-15
        if np.any(grid_array < 0) or np.any(grid_array > 15):
            return False

        return True

    @staticmethod
    def get_player_position(grid_array: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Obtener posición del jugador en la grid

        El jugador es el color 12 (naranja)

        Args:
            grid_array: Grid con jugador

        Returns:
            (row, col) posición del jugador, None si no encontrado
        """
        if not GridAdapter.validate_grid(grid_array):
            return None

        # Buscar color 12 (jugador)
        positions = np.where(grid_array == 12)
        if len(positions[0]) == 0:
            return None

        # Usar el centroide si hay múltiples celdas
        row = np.mean(positions[0]).astype(int)
        col = np.mean(positions[1]).astype(int)

        return (row, col)

    @staticmethod
    def get_walls(grid_array: np.ndarray) -> set:
        """
        Obtener conjunto de posiciones de paredes

        Paredes son: 4 (dark grey), 5 (black)

        Args:
            grid_array: Grid

        Returns:
            Set de (row, col) posiciones de paredes
        """
        if not GridAdapter.validate_grid(grid_array):
            return set()

        walls = set()
        positions = np.where((grid_array == 4) | (grid_array == 5))
        for row, col in zip(positions[0], positions[1]):
            walls.add((int(row), int(col)))

        return walls

    @staticmethod
    def get_doors(grid_array: np.ndarray) -> set:
        """
        Obtener conjunto de posiciones de puertas

        Puertas son: 5 (black, cerradas)

        Args:
            grid_array: Grid

        Returns:
            Set de (row, col) posiciones de puertas
        """
        if not GridAdapter.validate_grid(grid_array):
            return set()

        doors = set()
        positions = np.where(grid_array == 5)
        for row, col in zip(positions[0], positions[1]):
            doors.add((int(row), int(col)))

        return doors
