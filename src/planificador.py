"""Módulo 4: Planificador - A* search con CSP"""

from src.types import State, Plan, Rule
from src.mapeador import StateGraph


class Planificador:
    """Búsqueda A* sobre espacio de estados unificado"""

    def __init__(self, graph: StateGraph):
        self.graph = graph

    def plan(self, start: State, goal: State, rule: Rule) -> Plan:
        """
        Encontrar plan óptimo de start → goal respetando rule
        
        Args:
            start: Estado inicial
            goal: Estado objetivo
            rule: Restricciones a respetar
            
        Returns:
            Plan óptimo
        """
        raise NotImplementedError("Implementar en hito 2.2")

    def heuristic(self, state: State, goal: State) -> int:
        """Heurística admisible multi-componente"""
        raise NotImplementedError("Implementar en hito 2.3")

    def build_pattern_database(self) -> dict:
        """Precompute costos de transformación de llave"""
        raise NotImplementedError("Implementar en hito 2.3")
