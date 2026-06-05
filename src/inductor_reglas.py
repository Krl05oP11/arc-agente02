"""
Módulo 3: INDUCTOR DE REGLAS - Examples → Rule

Infiere las reglas de juego analizando ejemplos de entrenamiento.
Genera programas DSL que describen qué define un camino válido.
"""

from src.types import Example, Rule, WorldState, Rotator
from typing import List, Optional, Set, Dict, Tuple, Any
import logging
from enum import Enum

# Type alias for validation results
ValidationResult = Tuple[bool, Optional[str]]

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Tipos de reglas soportadas"""
    SHORTEST_PATH = "shortest_path"
    VISIT_ROTATORS = "visit_rotators_in_order"
    VISIT_ROTATORS_ANY_ORDER = "visit_rotators_any_order"
    CUSTOM = "custom"


class DSLProgram:
    """Programa en DSL que describe una regla de juego"""

    def __init__(self, rule_type: RuleType, details: Dict[str, Any]):
        """
        Inicializar un programa DSL

        Args:
            rule_type: Tipo de regla
            details: Detalles específicos de la regla (ej: orden de rotadores)
        """
        self.rule_type = rule_type
        self.details = details

    def __str__(self) -> str:
        """Representación legible del programa"""
        if self.rule_type == RuleType.SHORTEST_PATH:
            return "shortest_path(start, door)"

        elif self.rule_type == RuleType.VISIT_ROTATORS:
            order = self.details.get('rotator_order', [])
            order_str = ' → '.join([f"ROT[{r}]" for r in order])
            return f"visit_rotators_in_order({order_str}), then door"

        elif self.rule_type == RuleType.VISIT_ROTATORS_ANY_ORDER:
            rotators = self.details.get('rotators', [])
            rots_str = ', '.join([f"ROT[{r}]" for r in rotators])
            return f"visit_rotators_any_order({rots_str}), then door"

        else:
            return f"custom({self.details})"

    def to_rule(self) -> Rule:
        """Convertir a tipo Rule para el resto del sistema"""
        rule = Rule(
            dsl_program=str(self),
            constraint_list=self._generate_constraints(),
            rotator_order=self.details.get('rotator_order', []),
        )
        return rule

    def _generate_constraints(self) -> List[str]:
        """Generar lista de restricciones CSP a partir del DSL"""
        constraints = []

        if self.rule_type == RuleType.VISIT_ROTATORS:
            order = self.details.get('rotator_order', [])
            for i in range(len(order) - 1):
                constraints.append(f"visit({order[i]}) before visit({order[i+1]})")
            constraints.append(f"visit({order[-1]}) before door")

        elif self.rule_type == RuleType.VISIT_ROTATORS_ANY_ORDER:
            rotators = self.details.get('rotators', [])
            for rot in rotators:
                constraints.append(f"visit({rot}) before door")

        return constraints


class InductorReglas:
    """Inferidor de reglas desde ejemplos de entrenamiento"""

    def __init__(self, debug: bool = False):
        """
        Inicializar el Inductor

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)

    def infer_rule(self, examples: List[Example]) -> Optional[Rule]:
        """
        Analizar ejemplos de entrenamiento e inferir la regla de juego

        Estrategia:
        1. Si todos los ejemplos solo usan shortest_path → "shortest_path"
        2. Si todos visitan los mismos rotadores en el mismo orden → "visit_rotators_in_order"
        3. Si todos visitan los mismos rotadores pero en cualquier orden → "visit_rotators_any_order"
        4. Si no hay patrón claro → intentar buscar orden óptimo

        Args:
            examples: Lista de ejemplos (input_grid, solution_path)

        Returns:
            Rule que explica los ejemplos, o None si no puede inferirse
        """
        if not examples:
            return None

        # Paso 1: Extraer secuencias de rotadores de cada ejemplo
        rotator_sequences = []
        for example in examples:
            seq = self.extract_rotator_sequence(example)
            rotator_sequences.append(seq)
            if self.debug:
                logger.debug(f"Example rotators: {seq}")

        # Paso 2: Analizar patrones
        if self._all_empty(rotator_sequences):
            # No hay rotadores visitados → shortest path
            dsl = DSLProgram(RuleType.SHORTEST_PATH, {})
            if self.debug:
                logger.debug(f"Inferred rule: {dsl}")
            return dsl.to_rule()

        if self._all_same_order(rotator_sequences):
            # Todos visitan los mismos rotadores en el mismo orden
            order = rotator_sequences[0]
            dsl = DSLProgram(RuleType.VISIT_ROTATORS, {'rotator_order': order})
            if self.debug:
                logger.debug(f"Inferred rule: {dsl}")
            return dsl.to_rule()

        if self._all_same_set(rotator_sequences):
            # Todos visitan los mismos rotadores, pero en diferente orden
            rotators = set(rotator_sequences[0])
            dsl = DSLProgram(RuleType.VISIT_ROTATORS_ANY_ORDER, {'rotators': list(rotators)})
            if self.debug:
                logger.debug(f"Inferred rule: {dsl}")
            return dsl.to_rule()

        # Paso 3: Si no hay patrón obvio, intentar encontrar orden más frecuente
        if self.debug:
            logger.warning("No obvious pattern found, attempting order inference...")

        best_order = self._find_best_order(rotator_sequences)
        if best_order:
            dsl = DSLProgram(RuleType.VISIT_ROTATORS, {'rotator_order': best_order})
            if self.debug:
                logger.debug(f"Inferred rule (best guess): {dsl}")
            return dsl.to_rule()

        # No se pudo inferir regla
        if self.debug:
            logger.error("Failed to infer rule from examples")
        return None

    def extract_rotator_sequence(self, example: Example) -> List[int]:
        """
        Extraer la secuencia de rotadores visitados en un camino solución

        Analiza el camino solución y retorna qué rotadores fueron pisados,
        en el orden en que fueron visitados.

        Args:
            example: Ejemplo con grid y camino solución

        Returns:
            Lista de IDs de rotadores visitados en orden
        """
        if not example.world_state:
            return []

        rotators_by_pos = {
            rot.position: rot.rotator_id
            for rot in example.world_state.rotators
        }

        visited_rotators = []
        for pos in example.solution_path:
            if pos in rotators_by_pos:
                rot_id = rotators_by_pos[pos]
                if rot_id not in visited_rotators:
                    visited_rotators.append(rot_id)

        return visited_rotators

    def validate_rule(self, rule: Rule, examples: List[Example]) -> Tuple[bool, Optional[str]]:
        """
        Verificar que una regla es consistente con todos los ejemplos

        Para cada ejemplo, verifica que el camino solución satisface la regla.

        Args:
            rule: Regla a validar
            examples: Ejemplos de entrenamiento

        Returns:
            Tupla (is_valid, error_message)
            - is_valid: True si la regla es consistente
            - error_message: Descripción del error (None si es válido)
        """
        if not rule:
            return False, "Rule is None"

        if not examples:
            return False, "No examples provided"

        for i, example in enumerate(examples):
            is_valid, msg = self._path_satisfies_rule(
                example.solution_path, rule, example.world_state
            )
            if not is_valid:
                if self.debug:
                    logger.warning(f"Rule failed for example {i}: {msg}")
                return False, f"Example {i}: {msg}"

        if self.debug:
            logger.debug(f"✓ Rule validated on {len(examples)} examples")
        return True, None

    def _path_satisfies_rule(self, path: List[Tuple[int, int]],
                             rule: Rule, world: Optional[WorldState]) -> Tuple[bool, Optional[str]]:
        """
        Verificar si un camino satisface una regla

        Returns:
            Tupla (is_valid, error_message)
        """
        if not world:
            return False, "World state is None"

        if not path:
            return False, "Path is empty"

        # Extraer rotadores visitados en este camino, preservando orden
        rotators_by_pos = {rot.position: rot.rotator_id for rot in world.rotators}
        visited_rotators = []
        for pos in path:
            if pos in rotators_by_pos:
                rot_id = rotators_by_pos[pos]
                if rot_id not in visited_rotators:
                    visited_rotators.append(rot_id)

        # Verificar restricciones de la regla
        for constraint in rule.constraint_list:
            is_satisfied, msg = self._check_constraint(
                constraint, visited_rotators
            )
            if not is_satisfied:
                return False, f"Constraint failed: {msg}"

        return True, None

    def _check_constraint(self, constraint: str, visited_rotators: List[int]) -> Tuple[bool, Optional[str]]:
        """
        Verificar si una restricción CSP es satisfecha

        Soporta restricciones del tipo:
        - "visit(X) before visit(Y)" → X debe visitarse antes que Y
        - "visit(X) before door" → X debe visitarse antes de la puerta

        Args:
            constraint: Descripción de la restricción
            visited_rotators: Orden en que fueron visitados los rotadores

        Returns:
            Tupla (is_satisfied, error_message)
        """
        if "before" not in constraint:
            return True, None

        # Parse: "visit(X) before visit(Y)"
        parts = constraint.split(" before ")
        if len(parts) != 2:
            return True, None  # Ignorar restricciones malformadas

        before_part = parts[0].strip()  # "visit(X)"
        after_part = parts[1].strip()   # "visit(Y)" or "door"

        # Extraer IDs de las restricciones
        try:
            if "visit(" in before_part:
                before_id_str = before_part.replace("visit(", "").replace(")", "").strip()
                before_id = int(before_id_str)
            else:
                return True, None

            if "door" in after_part:
                # No hay restricción de rotador antes que puerta en este contexto
                return True, None

            if "visit(" in after_part:
                after_id_str = after_part.replace("visit(", "").replace(")", "").strip()
                after_id = int(after_id_str)
            else:
                return True, None
        except (ValueError, IndexError):
            # Si no se puede parsear, ignorar
            return True, None

        # Verificar que before_id aparece antes que after_id
        if before_id not in visited_rotators:
            return False, f"Rotator {before_id} not visited"

        if after_id not in visited_rotators:
            return False, f"Rotator {after_id} not visited"

        before_idx = visited_rotators.index(before_id)
        after_idx = visited_rotators.index(after_id)

        if before_idx >= after_idx:
            return False, f"Rotator {before_id} must be visited before {after_id}"

        return True, None

    # Métodos auxiliares

    def _all_empty(self, sequences: List[List[int]]) -> bool:
        """Verificar si todas las secuencias están vacías"""
        return all(len(seq) == 0 for seq in sequences)

    def _all_same_order(self, sequences: List[List[int]]) -> bool:
        """Verificar si todas las secuencias tienen el mismo orden"""
        if not sequences:
            return False
        first = sequences[0]
        return all(seq == first for seq in sequences)

    def _all_same_set(self, sequences: List[List[int]]) -> bool:
        """Verificar si todas las secuencias contienen el mismo conjunto (posiblemente en diferente orden)"""
        if not sequences:
            return False
        first_set = set(sequences[0])
        return all(set(seq) == first_set for seq in sequences)

    def _find_best_order(self, sequences: List[List[int]]) -> Optional[List[int]]:
        """Encontrar el orden más frecuente o consistente"""
        if not sequences:
            return None

        # Contar frecuencias de cada rotador
        all_rotators = set()
        for seq in sequences:
            all_rotators.update(seq)

        if not all_rotators:
            return None

        # Por ahora, retornar el orden del primer ejemplo
        # En una versión más sofisticada, buscaríamos consensus
        return sequences[0] if sequences[0] else list(all_rotators)


def create_inductor(debug: bool = False) -> InductorReglas:
    """Factory para crear un Inductor de Reglas"""
    return InductorReglas(debug=debug)
