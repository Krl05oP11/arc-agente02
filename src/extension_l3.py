"""
Módulo: EXTENSION L3+ - Soporte para problemas complejos

Extiende el sistema para manejar:
- Múltiples rotadores en secuencias complejas
- Rotadores con dependencias
- Optimización de rutas con múltiples puntos de interés
- Detección automática de patrones complejos
"""

from src.types import Rule, Rotator, State, Example, WorldState
from src.inductor_reglas import DSLProgram, RuleType
from typing import List, Set, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class RotatorSequence:
    """Representa una secuencia de rotadores a visitar"""

    def __init__(self, rotator_ids: List[int], required_order: bool = True):
        """
        Inicializar secuencia

        Args:
            rotator_ids: IDs de rotadores a visitar
            required_order: Si True, deben visitarse en orden
        """
        self.rotator_ids = rotator_ids
        self.required_order = required_order
        self.dependencies: Dict[int, Set[int]] = {}  # rotator → set of prerequisites

    def add_dependency(self, rotator_id: int, depends_on: int):
        """Agregar dependencia: rotador X requiere visitar Y primero"""
        if rotator_id not in self.dependencies:
            self.dependencies[rotator_id] = set()
        self.dependencies[rotator_id].add(depends_on)

    def is_satisfiable(self, visited: Set[int]) -> bool:
        """Verificar si la secuencia es satisfiable desde estado actual"""
        for rot_id, prereqs in self.dependencies.items():
            if rot_id in visited:
                # Si ya visitamos este rotador, sus requisitos deben estar satisfechos
                if not prereqs.issubset(visited):
                    return False
        return True

    def next_valid_rotators(self, visited: Set[int]) -> List[int]:
        """Retornar rotadores que pueden visitarse a continuación"""
        candidates = []

        for rot_id in self.rotator_ids:
            if rot_id in visited:
                continue  # Ya visitado

            # Verificar requisitos
            if rot_id in self.dependencies:
                prereqs = self.dependencies[rot_id]
                if not prereqs.issubset(visited):
                    continue  # Requisitos no satisfechos

            candidates.append(rot_id)

        return candidates

    def __repr__(self):
        return (f"RotatorSequence(ids={self.rotator_ids}, "
                f"ordered={self.required_order}, deps={self.dependencies})")


class ComplexRuleAnalyzer:
    """Analiza reglas complejas con múltiples rotadores"""

    def __init__(self, debug: bool = False):
        """
        Inicializar analizador

        Args:
            debug: Si True, imprimir logs
        """
        self.debug = debug

    def detect_rotator_sequence(self, example: Example) -> Optional[RotatorSequence]:
        """
        Detectar secuencia de rotadores desde ejemplo

        Args:
            example: Ejemplo de solución

        Returns:
            RotatorSequence o None si no detecta patrón
        """
        if not example.world_state or not example.world_state.rotators:
            return None

        # Mapear posiciones a rotadores
        pos_to_rotator = {rot.position: rot.rotator_id
                         for rot in example.world_state.rotators}

        # Extraer rotadores visitados del path
        visited_rotators = []
        for pos in example.solution_path:
            if pos in pos_to_rotator:
                rot_id = pos_to_rotator[pos]
                if rot_id not in visited_rotators:
                    visited_rotators.append(rot_id)

        if not visited_rotators:
            return None

        # Crear secuencia
        sequence = RotatorSequence(visited_rotators, required_order=True)

        if self.debug:
            logger.debug(f"✓ Detected sequence: {visited_rotators}")

        return sequence

    def infer_dependencies(self, examples: List[Example]) -> Dict[int, Set[int]]:
        """
        Inferir dependencias entre rotadores de múltiples ejemplos

        Args:
            examples: Lista de ejemplos

        Returns:
            Dict[rotator_id → set of dependencies]
        """
        dependencies = {}

        for example in examples:
            sequence = self.detect_rotator_sequence(example)
            if not sequence:
                continue

            # Para cada rotador, sus dependencias son todos los anteriores
            for i, rot_id in enumerate(sequence.rotator_ids):
                if rot_id not in dependencies:
                    dependencies[rot_id] = set()

                # Los rotadores anteriores son prerequisitos
                for j in range(i):
                    dependencies[rot_id].add(sequence.rotator_ids[j])

        return dependencies

    def create_complex_rule(self, examples: List[Example]) -> Optional[Rule]:
        """
        Crear regla para problema complejo

        Args:
            examples: Ejemplos de entrenamiento

        Returns:
            Rule o None
        """
        if not examples or not examples[0].world_state:
            return None

        # Detectar secuencia desde primer ejemplo
        sequence = self.detect_rotator_sequence(examples[0])
        if not sequence:
            return None

        # Inferir dependencias de todos los ejemplos
        dependencies = self.infer_dependencies(examples)

        # Actualizar secuencia con dependencias
        for rot_id, deps in dependencies.items():
            for dep in deps:
                sequence.add_dependency(rot_id, dep)

        # Crear programa DSL
        dsl = DSLProgram(
            rule_type=RuleType.VISIT_ROTATORS,
            details={'rotator_order': sequence.rotator_ids}
        )

        rule = dsl.to_rule()

        # Agregar restricciones de dependencia
        for rot_id, deps in dependencies.items():
            for dep in deps:
                constraint = f"visit({dep}) before visit({rot_id})"
                rule.constraint_list.append(constraint)

        if self.debug:
            logger.debug(f"✓ Complex rule created with {len(sequence.rotator_ids)} rotators")
            logger.debug(f"  Dependencies: {dependencies}")

        return rule


class L3ProblemClassifier:
    """Clasifica problemas como L1, L2, o L3+ según complejidad"""

    @staticmethod
    def get_complexity_score(world: WorldState) -> int:
        """
        Calcular score de complejidad

        Args:
            world: Estado del mundo

        Returns:
            Score (1-10)
        """
        score = 1

        # Contar obstáculos
        score += min(len(world.walls) // 10, 3)  # Máx 3 puntos

        # Contar rotadores (major factor)
        num_rotators = len(world.rotators)
        if num_rotators == 0:
            pass  # L1
        elif num_rotators == 1:
            score += 1  # L1/L2
        elif num_rotators == 2:
            score += 2  # L2/L3
        else:
            score += 3  # L3+ (3+ rotadores)

        # Contar puertas/refills
        score += min(len(world.doors) + len(world.refills), 2)

        # Contar teleportadores
        score += min(len(world.teleporters), 2)

        return min(score, 10)

    @staticmethod
    def classify_problem(world: WorldState) -> str:
        """
        Clasificar problema por dificultad

        Args:
            world: Estado del mundo

        Returns:
            "L1", "L2", "L3", o "L3+"
        """
        score = L3ProblemClassifier.get_complexity_score(world)

        if score <= 2:
            return "L1"
        elif score <= 4:
            return "L2"
        elif score <= 6:
            return "L3"
        else:
            return "L3+"


class ExtendedInductor:
    """Inductor extendido para problemas L3+"""

    def __init__(self, debug: bool = False):
        """
        Inicializar inductor extendido

        Args:
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.complex_analyzer = ComplexRuleAnalyzer(debug)
        self.classifier = L3ProblemClassifier()

    def infer_rule(self, examples: List[Example]) -> Optional[Rule]:
        """
        Inferir regla, detectando automáticamente complejidad

        Args:
            examples: Ejemplos de entrenamiento

        Returns:
            Rule adaptada a la complejidad del problema
        """
        if not examples or not examples[0].world_state:
            return None

        # Clasificar problema
        world = examples[0].world_state
        complexity = self.classifier.classify_problem(world)

        if self.debug:
            logger.debug(f"Problem classified as: {complexity}")

        # Para L3+, usar análisis complejo
        if complexity in ["L3", "L3+"]:
            rule = self.complex_analyzer.create_complex_rule(examples)
            if rule:
                return rule

        # Fallback a análisis simple
        return None


def create_l3_inductor(debug: bool = False) -> ExtendedInductor:
    """Factory para crear inductor extendido"""
    return ExtendedInductor(debug=debug)
