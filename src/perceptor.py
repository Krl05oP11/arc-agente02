"""Módulo 1: Perceptor - Parse grid → WorldState"""

from src.types import WorldState, Door, Rotator, Teleporter, KeyState
import numpy as np
from typing import Optional


class Perceptor:
    """Analizador que convierte grids crudos en estructura de datos"""

    def parse_grid(self, grid: np.ndarray) -> WorldState:
        """
        Parse una grid 30×30 y retorna WorldState
        
        Args:
            grid: numpy array 30×30 de colores
            
        Returns:
            WorldState con entidades identificadas
        """
        raise NotImplementedError("Implementar en hito 1.1")

    def identify_entities(self, grid: np.ndarray) -> dict:
        """
        Detectar entidades en el grid:
        - player_position
        - walls
        - door + requisito
        - rotators con tipos
        - refills
        - teleporters
        """
        raise NotImplementedError("Implementar en hito 1.1")

    def extract_key_panel(self, grid: np.ndarray) -> KeyState:
        """Extraer estado inicial de llave del panel (25-29, 0-4)"""
        raise NotImplementedError("Implementar en hito 1.1")
