"""
Módulo: TELEPORTER OPTIMIZER - Optimización de rutas con teletransportes

Extiende el sistema para:
- Detectar y mapear teleportadores
- Encontrar shortcuts mediante teletransportes
- Evitar ciclos de teleporte
- Optimizar rutas multi-hop
"""

from src.types import WorldState, State, Plan
from src.extension_l3 import L3ProblemClassifier
from typing import List, Set, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class TeleporterInfo:
    """Información sobre un teleportador"""

    def __init__(self, source: Tuple[int, int], destination: Tuple[int, int],
                 entry_directions: Optional[Set[Tuple[int, int]]] = None):
        """
        Inicializar info de teleportador

        Args:
            source: Posición de entrada
            destination: Posición de salida
            entry_directions: Direcciones desde las cuales se activa (None = cualquiera)
        """
        self.source = source
        self.destination = destination
        self.entry_directions = entry_directions  # None = omnidireccional

    def is_accessible_from(self, from_pos: Tuple[int, int]) -> bool:
        """
        Verificar si el teleportador es accesible desde una posición

        Args:
            from_pos: Posición de origen

        Returns:
            True si se puede llegar al teleportador desde aquí
        """
        # Simplificación: si entry_directions no está definido, es accessible
        if self.entry_directions is None:
            return True

        # Si la posición es la misma, es accessible
        if from_pos == self.source:
            return True

        # Calcular dirección (desde from_pos hacia self.source)
        dr = self.source[0] - from_pos[0]
        dc = self.source[1] - from_pos[1]

        # Normalizar dirección
        dr = 0 if dr == 0 else (1 if dr > 0 else -1)
        dc = 0 if dc == 0 else (1 if dc > 0 else -1)

        return (dr, dc) in self.entry_directions

    def __repr__(self):
        return f"TP({self.source} → {self.destination})"


class TeleporterNetwork:
    """Red de teleportadores"""

    def __init__(self, world: WorldState, debug: bool = False):
        """
        Inicializar red de teleportadores

        Args:
            world: Estado del mundo
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.teleporters: List[TeleporterInfo] = []
        self.source_map: Dict[Tuple[int, int], TeleporterInfo] = {}  # source → TP
        self.cycle_map: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}  # source → destinations

        # Mapear teleportadores del mundo
        for tp_source in world.teleporters:
            # Nota: world.teleporters es una lista de posiciones
            # En un mundo real, necesitaríamos información de destino
            # Por ahora, asumimos que son pares (source, dest) o solo sources
            if isinstance(tp_source, tuple) and len(tp_source) == 2:
                # Es una posición, marcar como potencial teleportador
                tp = TeleporterInfo(tp_source, None)  # Destino desconocido por ahora
                self.teleporters.append(tp)
                self.source_map[tp_source] = tp

        if debug:
            logger.debug(f"✓ TeleporterNetwork created with {len(self.teleporters)} TPs")

    def register_teleport(self, source: Tuple[int, int], destination: Tuple[int, int]):
        """
        Registrar un teleporte descubierto

        Args:
            source: Posición de entrada
            destination: Posición de salida
        """
        if source not in self.source_map:
            tp = TeleporterInfo(source, destination)
            self.teleporters.append(tp)
            self.source_map[source] = tp

        self.source_map[source].destination = destination

        # Registrar para detección de ciclos
        if source not in self.cycle_map:
            self.cycle_map[source] = set()
        self.cycle_map[source].add(destination)

        if self.debug:
            logger.debug(f"Registered teleport: {source} → {destination}")

    def find_cycles(self) -> List[List[Tuple[int, int]]]:
        """
        Encontrar ciclos en la red de teleportes

        Returns:
            Lista de ciclos detectados
        """
        cycles = []
        visited_global = set()

        for start_tp in self.teleporters:
            if start_tp.source in visited_global:
                continue

            # BFS para encontrar ciclos desde este TP
            visited = {start_tp.source}
            queue = [(start_tp.source, [start_tp.source])]

            while queue:
                current, path = queue.pop(0)

                if current in self.cycle_map:
                    for next_pos in self.cycle_map[current]:
                        if next_pos == start_tp.source and len(path) > 1:
                            # Ciclo encontrado
                            cycle = path + [start_tp.source]
                            cycles.append(cycle)
                            visited_global.update(path)

                        elif next_pos not in visited and len(path) < 10:  # Límite para evitar infinito
                            visited.add(next_pos)
                            queue.append((next_pos, path + [next_pos]))

        return cycles

    def get_teleporter_shortcut(self, from_pos: Tuple[int, int],
                               to_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Encontrar teleportador que acorte la ruta

        Args:
            from_pos: Posición actual
            to_pos: Posición objetivo

        Returns:
            Posición de salida si hay shortcut, None si no
        """
        for tp in self.teleporters:
            if tp.destination is None:
                continue

            # Calcular distancias
            normal_dist = abs(to_pos[0] - from_pos[0]) + abs(to_pos[1] - from_pos[1])

            tp_to_goal = abs(to_pos[0] - tp.destination[0]) + abs(to_pos[1] - tp.destination[1])
            tp_from_current = abs(tp.source[0] - from_pos[0]) + abs(tp.source[1] - from_pos[1])

            # Si usar teleporte es más corto
            if tp_from_current + tp_to_goal < normal_dist:
                return tp.destination

        return None

    def is_safe_teleport(self, source: Tuple[int, int], destination: Tuple[int, int]) -> bool:
        """
        Verificar si un teleporte es seguro (no causa ciclos infinitos)

        Args:
            source: Posición de entrada
            destination: Posición de salida

        Returns:
            True si es seguro usarlo
        """
        # Verificar si ya hay un ciclo registrado que nos afecta
        if source in self.cycle_map and destination in self.cycle_map[source]:
            # Este teleporte está en un ciclo
            if destination == source:
                return False  # Auto-ciclo

            # Verificar si destination eventualmente vuelve a source
            visited = {source}
            queue = [destination]

            while queue:
                current = queue.pop(0)

                if current == source:
                    return False  # Ciclo detectado

                if current in self.cycle_map:
                    for next_pos in self.cycle_map[current]:
                        if next_pos not in visited and len(visited) < 10:
                            visited.add(next_pos)
                            queue.append(next_pos)

        return True


class TeleporterOptimizer:
    """Optimiza rutas usando teleportadores"""

    def __init__(self, world: WorldState, debug: bool = False):
        """
        Inicializar optimizador

        Args:
            world: Estado del mundo
            debug: Si True, imprimir logs
        """
        self.debug = debug
        self.network = TeleporterNetwork(world, debug)
        self.classifier = L3ProblemClassifier()

    def has_teleporters(self) -> bool:
        """Verificar si hay teleportadores en el mundo"""
        return len(self.network.teleporters) > 0

    def can_use_teleporters(self, world: WorldState) -> bool:
        """
        Verificar si deberíamos optimizar con teleportadores

        Args:
            world: Estado del mundo

        Returns:
            True si tiene sentido usarlos
        """
        if not self.has_teleporters():
            return False

        # Usar si el problema es complejo
        score = self.classifier.get_complexity_score(world)
        return score >= 3  # L2 o más

    def optimize_plan(self, plan: Plan, world: WorldState) -> Optional[Plan]:
        """
        Optimizar un plan insertando teleportadores si es beneficioso

        Args:
            plan: Plan original
            world: Estado del mundo

        Returns:
            Plan optimizado o None si no se puede mejorar
        """
        if not self.can_use_teleporters(world):
            return None

        # Buscar oportunidades de teleporte
        optimized_actions = []
        i = 0

        while i < len(plan.actions):
            current_pos = plan.actions[i]

            # Buscar siguiente checkpoint (rotador, puerta, etc.)
            remaining = plan.actions[i+1:] if i+1 < len(plan.actions) else []

            if remaining:
                target_pos = remaining[-1]  # Ir al último (puerta)

                # Buscar shortcut
                shortcut = self.network.get_teleporter_shortcut(current_pos, target_pos)

                if shortcut and self.network.is_safe_teleport(current_pos, shortcut):
                    # Usar teleporte
                    optimized_actions.append(current_pos)
                    optimized_actions.append(shortcut)

                    # Saltar el camino normal
                    i = len(plan.actions) - 1
                    continue

            optimized_actions.append(current_pos)
            i += 1

        # Si es más corto, retornar plan optimizado
        if len(optimized_actions) < len(plan.actions):
            return Plan(
                actions=optimized_actions,
                cost=len(optimized_actions) - 1,
                valid=True
            )

        return None

    def detect_teleporter_cycles(self) -> List[List[Tuple[int, int]]]:
        """
        Detectar ciclos en teleportadores para evitar

        Returns:
            Lista de ciclos detectados
        """
        return self.network.find_cycles()

    def get_optimization_report(self) -> Dict[str, any]:
        """
        Generar reporte de oportunidades de optimización

        Returns:
            Dict con estadísticas
        """
        cycles = self.detect_teleporter_cycles()

        return {
            'teleporters': len(self.network.teleporters),
            'cycles': len(cycles),
            'can_optimize': self.has_teleporters(),
        }


def create_teleporter_optimizer(world: WorldState, debug: bool = False) -> TeleporterOptimizer:
    """Factory para crear optimizador de teleportadores"""
    return TeleporterOptimizer(world, debug)
