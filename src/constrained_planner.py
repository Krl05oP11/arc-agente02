"""
Módulo integrado: CONSTRAINED PLANNER - Reglas + Búsqueda

Integra las reglas inferidas por el Inductor con el planificador A*.

Las restricciones CSP se aplican como precondiciones en las transiciones,
asegurando que el plan respeta la regla aprendida.
"""

from src.types import State, Rule, WorldState, Plan
from src.mapeador import StateGraph
from src.planificador import AStarPlanner, PlanValidator
from typing import List, Tuple, Optional, Dict, Set
import logging

logger = logging.getLogger(__name__)


class ConstraintChecker:
    """Verifica que un estado satisface las restricciones de una regla"""

    def __init__(self, rule: Rule, debug: bool = False):
        """
        Inicializar el verificador de restricciones

        Args:
            rule: Regla con restricciones CSP
            debug: Si True, imprimir logs
        """
        self.rule = rule
        self.debug = debug
        self._parse_constraints()

    def _parse_constraints(self):
        """Parsear las restricciones de la regla en estructuras útiles"""
        self.must_visit_before: Dict[int, Set[int]] = {}
        self.must_visit: Set[int] = set()

        for constraint in self.rule.constraint_list:
            if "visit(" in constraint and "before" in constraint:
                # Parse: "visit(X) before visit(Y)"
                parts = constraint.split(" before ")
                before_str = parts[0].strip()
                after_str = parts[1].strip()

                try:
                    if "visit(" in before_str:
                        before_id = int(before_str.replace("visit(", "").replace(")", "").strip())
                        if "visit(" in after_str:
                            after_id = int(after_str.replace("visit(", "").replace(")", "").strip())
                            if after_id not in self.must_visit_before:
                                self.must_visit_before[after_id] = set()
                            self.must_visit_before[after_id].add(before_id)
                            self.must_visit.add(before_id)
                            self.must_visit.add(after_id)
                except ValueError:
                    pass

        if self.debug:
            logger.debug(f"✓ Constraints parsed: {len(self.must_visit)} rotators, "
                        f"{len(self.must_visit_before)} ordering constraints")

    def is_feasible(self, current_state: State) -> bool:
        """
        Verificar que es posible satisfacer las restricciones desde este estado

        Una transición es factible si:
        1. No hemos visitado rotadores que violarían el orden
        2. Aún podemos visitar los rotadores requeridos

        Args:
            current_state: Estado actual

        Returns:
            True si es factible continuar
        """
        visited = current_state.visited_rotators if current_state.visited_rotators else set()

        for rot_id in visited:
            # Si ya visitamos este rotador, verificar que los prerequisitos fueron visitados
            if rot_id in self.must_visit_before:
                prerequisites = self.must_visit_before[rot_id]
                for prereq in prerequisites:
                    if prereq not in visited:
                        if self.debug:
                            logger.debug(f"Constraint violated: {rot_id} requires {prereq} first")
                        return False

        return True

    def is_satisfied(self, final_state: State) -> bool:
        """
        Verificar que un estado final satisface todas las restricciones

        Args:
            final_state: Estado final (debería ser en la puerta)

        Returns:
            True si se satisfacen todas las restricciones
        """
        visited = final_state.visited_rotators if final_state.visited_rotators else set()

        # Verificar que visitamos todos los rotadores requeridos
        for rot_id in self.must_visit:
            if rot_id not in visited:
                if self.debug:
                    logger.debug(f"Missing rotator: {rot_id}")
                return False

        # Verificar orden de visitas
        for rot_id in visited:
            if rot_id in self.must_visit_before:
                prerequisites = self.must_visit_before[rot_id]
                for prereq in prerequisites:
                    if prereq not in visited:
                        if self.debug:
                            logger.debug(f"Order violated: {rot_id} before {prereq}")
                        return False
                    # Verificar que prerequisito fue visitado primero
                    # (esto es más complejo, requeriría tracking de orden)

        return True


class ConstrainedStateGraph(StateGraph):
    """
    StateGraph que respeta las restricciones de una regla.

    Extiende StateGraph para incluir verificación de restricciones
    en la generación de transiciones.
    """

    def __init__(self, world: WorldState, rule: Optional[Rule] = None, debug: bool = False):
        """
        Inicializar el StateGraph con restricciones

        Args:
            world: Estado del mundo
            rule: Regla con restricciones (None = sin restricciones)
            debug: Si True, imprimir logs
        """
        super().__init__(world, debug)
        self.rule = rule
        self.constraint_checker = ConstraintChecker(rule, debug) if rule else None

    def neighbors(self, state: State) -> List[Tuple[State, int]]:
        """
        Generar vecinos respetando restricciones de la regla

        Args:
            state: Estado actual

        Returns:
            Lista de (next_state, cost) válidos según la regla
        """
        # Obtener vecinos del grafo base
        all_neighbors = super().neighbors(state)

        # Si no hay restricciones, retornar todos
        if not self.constraint_checker:
            return all_neighbors

        # Filtrar según viabilidad de restricciones
        filtered = []
        for next_state, cost in all_neighbors:
            if self.constraint_checker.is_feasible(next_state):
                filtered.append((next_state, cost))

        if self.debug and len(filtered) < len(all_neighbors):
            logger.debug(f"Filtered {len(all_neighbors) - len(filtered)} moves due to constraints")

        return filtered

    def is_goal(self, state: State) -> bool:
        """
        Verificar si es goal, respetando restricciones

        Args:
            state: Estado a verificar

        Returns:
            True si está en puerta Y satisface todas las restricciones
        """
        # Primero verificar si está en la puerta con llave correcta
        if not super().is_goal(state):
            return False

        # Luego verificar restricciones
        if self.constraint_checker:
            return self.constraint_checker.is_satisfied(state)

        return True


class ConstrainedPlanner:
    """
    Planificador que respeta reglas y restricciones.

    Combina el Inductor (que genera reglas) con el Planificador (A*).
    """

    def __init__(self, world: WorldState, rule: Rule, debug: bool = False):
        """
        Inicializar el planificador con restricciones

        Args:
            world: Estado del mundo
            rule: Regla a respetar
            debug: Si True, imprimir logs
        """
        self.world = world
        self.rule = rule
        self.debug = debug

        # Crear grafo con restricciones
        self.graph = ConstrainedStateGraph(world, rule, debug)

        # Crear planificador A*
        self.planner = AStarPlanner(self.graph, debug)

        # Crear validador
        self.validator = PlanValidator(self.graph, debug)

    def plan(self, start_state: State, goal_key: Tuple[int, int, int],
             max_iterations: int = 100000) -> Optional[Plan]:
        """
        Generar plan que respeta la regla

        Args:
            start_state: Estado inicial
            goal_key: (shape, color, rotation) requerido
            max_iterations: Límite de iteraciones A*

        Returns:
            Plan válido o None si no existe
        """
        if self.debug:
            logger.debug(f"Planning with rule: {self.rule.dsl_program}")

        # Ejecutar A* con restricciones
        plan = self.planner.search(start_state, goal_key, max_iterations)

        if plan is None:
            if self.debug:
                logger.debug("No plan found")
            return None

        # Validar que el plan respeta las restricciones
        is_valid, msg = self.validator.validate(plan, start_state)

        if not is_valid:
            if self.debug:
                logger.warning(f"Plan validation failed: {msg}")
            return None

        if self.debug:
            logger.debug(f"✓ Valid plan: {len(plan.actions)} steps, cost {plan.cost}")

        return plan

    def get_stats(self) -> Dict[str, any]:
        """Retornar estadísticas de búsqueda"""
        return self.planner.get_stats()


def create_constrained_planner(world: WorldState, rule: Rule,
                               debug: bool = False) -> ConstrainedPlanner:
    """Factory para crear un planificador con restricciones"""
    return ConstrainedPlanner(world, rule, debug)
