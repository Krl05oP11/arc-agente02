"""
Módulo: EXPERIENCE LEARNER - Aprendizaje basado en experiencias

Permite al agente:
- Registrar experiencias (qué pasó, qué funcionó)
- Aprender patrones de descubrimientos
- Mejorar estrategias de exploración
- Tomar decisiones informadas
- Predecir obstáculos basado en experiencia
"""

from src.explorer import ExplorationStrategy
from typing import Dict, List, Tuple, Optional, Any, Set
import logging

logger = logging.getLogger(__name__)


class Experience:
    """Registro de una experiencia"""

    def __init__(self, experience_type: str, position: Tuple[int, int],
                 outcome: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Inicializar experiencia

        Args:
            experience_type: Tipo de experiencia ("wall", "rotator", "door", etc)
            position: Posición donde ocurrió
            outcome: Resultado ("success", "obstacle", "discovery")
            metadata: Información adicional
        """
        self.type = experience_type
        self.position = position
        self.outcome = outcome
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Experience({self.type}@{self.position}→{self.outcome})"


class ExperienceMemory:
    """Memoria de experiencias acumuladas"""

    def __init__(self, max_experiences: int = 1000):
        """
        Inicializar memoria

        Args:
            max_experiences: Máximo de experiencias a recordar
        """
        self.experiences: List[Experience] = []
        self.max_experiences = max_experiences
        self.pattern_cache: Dict[str, int] = {}  # Patrones frecuentes

    def record_experience(self, experience: Experience):
        """
        Registrar una experiencia

        Args:
            experience: Experiencia a recordar
        """
        self.experiences.append(experience)

        # Limitar tamaño de memoria
        if len(self.experiences) > self.max_experiences:
            self.experiences = self.experiences[-self.max_experiences:]

        # Actualizar cache de patrones
        pattern_key = f"{experience.type}_{experience.outcome}"
        self.pattern_cache[pattern_key] = self.pattern_cache.get(pattern_key, 0) + 1

        if len(self.experiences) % 100 == 0:
            logger.debug(f"Memory: {len(self.experiences)} experiences recorded")

    def get_experiences_by_type(self, experience_type: str) -> List[Experience]:
        """
        Obtener experiencias de un tipo

        Args:
            experience_type: Tipo a filtrar

        Returns:
            Lista de experiencias
        """
        return [exp for exp in self.experiences if exp.type == experience_type]

    def get_success_rate(self, experience_type: str) -> float:
        """
        Calcular tasa de éxito para un tipo

        Args:
            experience_type: Tipo a evaluar

        Returns:
            Tasa de éxito (0.0-1.0)
        """
        relevant = self.get_experiences_by_type(experience_type)

        if not relevant:
            return 0.5  # Neutral si no hay datos

        successes = sum(1 for exp in relevant if exp.outcome == "success")
        return successes / len(relevant)

    def predict_obstacle_probability(self, position: Tuple[int, int]) -> float:
        """
        Predecir probabilidad de obstáculo en posición

        Args:
            position: Posición a evaluar

        Returns:
            Probabilidad (0.0-1.0)
        """
        # Buscar experiencias cercanas
        nearby = [exp for exp in self.get_experiences_by_type("wall")
                 if self._distance(exp.position, position) <= 10]

        if not nearby:
            return 0.1  # Baja probabilidad por defecto

        # Más cercanas = más probable
        return min(len(nearby) * 0.1, 0.9)

    def _distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Distancia Manhattan"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def get_most_common_discoveries(self, limit: int = 5) -> List[Tuple[str, int]]:
        """
        Obtener descubrimientos más comunes

        Args:
            limit: Máximo de resultados

        Returns:
            Lista de (tipo, frecuencia)
        """
        discovery_counts: Dict[str, int] = {}

        for exp in self.experiences:
            if exp.outcome == "discovery":
                discovery_counts[exp.type] = discovery_counts.get(exp.type, 0) + 1

        sorted_discoveries = sorted(discovery_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_discoveries[:limit]

    def __repr__(self):
        return f"ExperienceMemory({len(self.experiences)} experiences)"


class LearningAgent:
    """Agente que aprende de experiencias"""

    def __init__(self, memory: ExperienceMemory, debug: bool = False):
        """
        Inicializar agente aprendiz

        Args:
            memory: Memoria de experiencias
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.memory = memory
        self.strategy_effectiveness: Dict[str, float] = {}
        self.learned_patterns: Set[Tuple[str, str]] = set()

    def learn_from_experience(self, experience: Experience):
        """
        Aprender de una experiencia

        Args:
            experience: Experiencia registrada
        """
        self.memory.record_experience(experience)

        # Actualizar patrones aprendidos
        pattern = (experience.type, experience.outcome)
        self.learned_patterns.add(pattern)

        if self.debug:
            logger.debug(f"Learned pattern: {pattern}")

    def choose_exploration_strategy(self, frontier_size: int,
                                   covered_percentage: float) -> str:
        """
        Elegir estrategia basada en aprendizaje

        Args:
            frontier_size: Tamaño de la frontera de exploración
            covered_percentage: Porcentaje de cobertura (0.0-1.0)

        Returns:
            Nombre de estrategia recomendada
        """
        # Si ya exploramos bastante, ser más dirigido
        if covered_percentage > 0.7:
            return ExplorationStrategy.GOAL_ORIENTED

        # Si la frontera es grande, expandir
        if frontier_size > 50:
            return ExplorationStrategy.BREADTH_FIRST

        # Por defecto, profundidad
        return ExplorationStrategy.DEPTH_FIRST

    def predict_outcome(self, experience_type: str) -> str:
        """
        Predecir resultado probable de una experiencia

        Args:
            experience_type: Tipo de experiencia

        Returns:
            Resultado predicho ("success", "obstacle", "discovery", "unknown")
        """
        success_rate = self.memory.get_success_rate(experience_type)

        if success_rate > 0.7:
            return "success"
        elif success_rate < 0.3:
            return "obstacle"
        else:
            return "discovery"

    def get_learned_patterns(self) -> List[Tuple[str, str]]:
        """
        Obtener patrones aprendidos

        Returns:
            Lista de patrones (tipo, resultado)
        """
        return list(self.learned_patterns)

    def should_avoid_area(self, position: Tuple[int, int]) -> bool:
        """
        Determinar si área debe ser evitada

        Args:
            position: Posición a evaluar

        Returns:
            True si debe evitarse
        """
        obstacle_prob = self.memory.predict_obstacle_probability(position)
        return obstacle_prob > 0.6

    def get_learning_confidence(self) -> float:
        """
        Obtener confianza en aprendizaje

        Returns:
            Confianza (0.0-1.0) basada en experiencias acumuladas
        """
        num_experiences = len(self.memory.experiences)

        # Más experiencias = más confianza
        if num_experiences < 10:
            return 0.1
        elif num_experiences < 50:
            return 0.3
        elif num_experiences < 100:
            return 0.6
        else:
            return 0.9

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de aprendizaje

        Returns:
            Dict con stats
        """
        return {
            'experiences': len(self.memory.experiences),
            'patterns_learned': len(self.learned_patterns),
            'confidence': self.get_learning_confidence(),
            'top_discoveries': self.memory.get_most_common_discoveries(3),
        }


class SmartDecisionMaker:
    """Tomador de decisiones basado en aprendizaje"""

    def __init__(self, agent: LearningAgent, debug: bool = False):
        """
        Inicializar tomador de decisiones

        Args:
            agent: Agente aprendiz
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.agent = agent

    def decide_next_move(self, current_position: Tuple[int, int],
                        frontier: List[Tuple[int, int]],
                        goal_position: Optional[Tuple[int, int]] = None
                        ) -> Optional[Tuple[int, int]]:
        """
        Decidir siguiente movimiento basado en aprendizaje

        Args:
            current_position: Posición actual
            frontier: Frontera de exploración
            goal_position: Objetivo conocido (opcional)

        Returns:
            Siguiente posición a visitar
        """
        if not frontier:
            return None

        # Filtrar posiciones con alto riesgo
        safe_frontier = [pos for pos in frontier if not self.agent.should_avoid_area(pos)]

        if not safe_frontier:
            # Si todo es riesgoso, asumir riesgo calculado
            safe_frontier = frontier

        # Si hay objetivo, priorizar ruta hacia él
        if goal_position:
            goal_frontier = self._find_closest_to(safe_frontier, goal_position)
            if goal_frontier:
                return goal_frontier

        # Sino, elegir la más cercana (estrategia segura)
        return self._find_closest_to(safe_frontier, current_position)

    def _find_closest_to(self, positions: List[Tuple[int, int]],
                        target: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Encontrar posición más cercana a target

        Args:
            positions: Lista de posiciones
            target: Posición objetivo

        Returns:
            Posición más cercana
        """
        if not positions:
            return None

        def distance(pos: Tuple[int, int]) -> int:
            return abs(pos[0] - target[0]) + abs(pos[1] - target[1])

        return min(positions, key=distance)

    def decide_strategy(self, frontier_size: int,
                       covered_percentage: float) -> str:
        """
        Decidir estrategia de exploración

        Args:
            frontier_size: Tamaño de frontera
            covered_percentage: Porcentaje cubierto

        Returns:
            Nombre de estrategia
        """
        return self.agent.choose_exploration_strategy(frontier_size, covered_percentage)


def create_learning_agent(max_experiences: int = 1000,
                         debug: bool = False) -> LearningAgent:
    """Factory para crear agente aprendiz"""
    memory = ExperienceMemory(max_experiences)
    return LearningAgent(memory, debug)


def create_decision_maker(agent: LearningAgent,
                         debug: bool = False) -> SmartDecisionMaker:
    """Factory para crear tomador de decisiones"""
    return SmartDecisionMaker(agent, debug)
