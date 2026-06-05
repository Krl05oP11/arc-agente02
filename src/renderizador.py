"""Módulo 5: Renderizador - Plan → Output Grid"""

from src.types import Plan
import numpy as np


class Renderizador:
    """Convierte plan en grid de salida"""

    def render(self, plan: Plan, original_grid: np.ndarray) -> np.ndarray:
        """
        Renderizar plan sobre grid original
        
        Args:
            plan: Secuencia de acciones
            original_grid: Grid 30×30 original
            
        Returns:
            Grid con camino dibujado
        """
        raise NotImplementedError("Implementar en hito 3.1")

    def match_output_format(self, grid: np.ndarray, example_output: np.ndarray) -> np.ndarray:
        """Asegurar que el formato coincide exactamente con ejemplos"""
        raise NotImplementedError("Implementar en hito 3.1")
