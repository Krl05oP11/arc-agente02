"""Módulo 6: Supervisor - Orquestador del pipeline"""

from src.types import Example, Solution
from typing import List


class Supervisor:
    """Coordina el pipeline completo: learn → plan → execute"""

    def run(self, training_examples: List[Example], test_grid) -> Solution:
        """
        Pipeline completo:
        1. Parse grids
        2. Infer rule from examples
        3. Validate rule
        4. Plan on test set
        5. Render output
        
        Args:
            training_examples: Ejemplos de entrenamiento
            test_grid: Grid de prueba
            
        Returns:
            Solution con resultado final
        """
        raise NotImplementedError("Implementar en hito 3.2")

    def validate_rule(self, rule, examples: List[Example]) -> bool:
        """Verificar que rule es válida"""
        raise NotImplementedError("Implementar en hito 3.2")

    def handle_failure(self, reason: str):
        """Detectar fallo y intentar alternativa"""
        raise NotImplementedError("Implementar en hito 3.2")
