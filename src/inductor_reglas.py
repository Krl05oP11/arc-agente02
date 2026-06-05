"""Módulo 3: Inductor de Reglas - Examples → Rule"""

from src.types import Example, Rule
from typing import List


class InductorReglas:
    """Inferidor de reglas desde ejemplos de entrenamiento"""

    def infer_rule(self, examples: List[Example]) -> Rule:
        """
        Analizar ejemplos de entrenamiento e inferir la regla de juego
        
        Args:
            examples: Lista de ejemplos (input, solution)
            
        Returns:
            Rule que explica los ejemplos
        """
        raise NotImplementedError("Implementar en hito 1.2")

    def extract_rotator_sequence(self, grid, path) -> List[int]:
        """Extraer qué rotadores fueron visitados en la solución"""
        raise NotImplementedError("Implementar en hito 1.2")

    def validate_rule(self, rule: Rule, examples: List[Example]) -> bool:
        """Verificar que la regla es consistente con todos los ejemplos"""
        raise NotImplementedError("Implementar en hito 1.3")
