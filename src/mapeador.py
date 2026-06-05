"""Módulo 2: Mapeador - WorldState → StateGraph"""

from src.types import WorldState, State
from typing import List, Tuple


class StateGraph:
    """Grafo de búsqueda para A*"""

    def neighbors(self, state: State) -> List[Tuple[State, int]]:
        """
        Retornar estados alcanzables desde state
        
        Args:
            state: Estado actual
            
        Returns:
            Lista de (next_state, cost) pares
        """
        raise NotImplementedError("Implementar en hito 2.1")

    def heuristic(self, state: State, goal: State) -> int:
        """Heurística admisible para A*"""
        raise NotImplementedError("Implementar en hito 2.3")


class Mapeador:
    """Construye grafo de búsqueda desde WorldState"""

    def build_graph(self, world: WorldState) -> StateGraph:
        """
        Convertir WorldState → StateGraph
        
        Args:
            world: Estado del mundo
            
        Returns:
            Grafo listo para búsqueda
        """
        raise NotImplementedError("Implementar en hito 2.1")
