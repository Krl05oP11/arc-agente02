"""
Módulo de soporte: PATTERN DATABASE - Heurística mejorada

Una Pattern Database es una tabla precalculada que almacena el costo mínimo
para ir de un estado de llave a otro estado de llave.

DB[key_a][key_b] = mínimo número de rotadores a visitar para transformar
                   key_a en key_b

Esto mejora significativamente la heurística de A* sin violar admisibilidad.
"""

from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class KeyState:
    """Representación de estado de llave para Pattern Database"""

    def __init__(self, shape: int, color: int, rotation: int):
        self.shape = shape % 4
        self.color = color % 4
        self.rotation = rotation % 4

    def __eq__(self, other):
        return (self.shape == other.shape and
                self.color == other.color and
                self.rotation == other.rotation)

    def __hash__(self):
        return hash((self.shape, self.color, self.rotation))

    def __repr__(self):
        return f"KeyState({self.shape},{self.color},{self.rotation})"

    def transform_shape(self):
        """Aplicar rotador SHAPE"""
        return KeyState((self.shape + 1) % 4, self.color, self.rotation)

    def transform_color(self):
        """Aplicar rotador COLOR"""
        return KeyState(self.shape, (self.color + 1) % 4, self.rotation)

    def transform_rot(self):
        """Aplicar rotador ROT"""
        return KeyState(self.shape, self.color, (self.rotation + 1) % 4)

    def all_neighbors(self):
        """Retornar todos los estados vecinos (1 rotador)"""
        return [
            self.transform_shape(),
            self.transform_color(),
            self.transform_rot()
        ]


class PatternDatabase:
    """
    Tabla de búsqueda para transformaciones de llave.

    Precalcula el costo mínimo para ir de cualquier estado de llave
    a cualquier otro usando BFS en el espacio de transformaciones.
    """

    def __init__(self, debug: bool = False):
        """
        Inicializar la Pattern Database

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        self.db: Dict[KeyState, Dict[KeyState, int]] = {}
        self._build()

    def _build(self):
        """Construir la Pattern Database usando BFS desde cada estado"""
        if self.debug:
            logger.debug("Building Pattern Database...")

        # Generar todos los estados posibles
        all_states = [
            KeyState(s, c, r)
            for s in range(4)
            for c in range(4)
            for r in range(4)
        ]

        # Para cada estado, calcular distancia a todos los demás
        for start_state in all_states:
            distances = self._bfs_distances(start_state)
            self.db[start_state] = distances

        if self.debug:
            logger.debug(f"✓ Pattern Database built: {len(all_states)} states, "
                        f"{len(self.db)} entries")

    def _bfs_distances(self, start: KeyState) -> Dict[KeyState, int]:
        """
        Calcular distancias desde start a todos los demás estados usando BFS

        Args:
            start: Estado inicial

        Returns:
            Mapping {estado: distancia}
        """
        from collections import deque

        distances = {start: 0}
        queue = deque([start])

        while queue:
            current = queue.popleft()
            current_dist = distances[current]

            # Explorar vecinos (1 rotador)
            for neighbor in current.all_neighbors():
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)

        return distances

    def lookup(self, key_from: Tuple[int, int, int],
               key_to: Tuple[int, int, int]) -> int:
        """
        Consultar el costo mínimo de transformación

        Args:
            key_from: (shape, color, rotation) inicial
            key_to: (shape, color, rotation) objetivo

        Returns:
            Costo mínimo (número de rotadores)
        """
        from_state = KeyState(*key_from)
        to_state = KeyState(*key_to)

        if from_state not in self.db:
            # Fallback: usar aproximación simple
            return self._fallback_heuristic(from_state, to_state)

        if to_state not in self.db[from_state]:
            # Fallback
            return self._fallback_heuristic(from_state, to_state)

        return self.db[from_state][to_state]

    def _fallback_heuristic(self, key_from: KeyState, key_to: KeyState) -> int:
        """
        Heurística simple si no está en DB

        Cuenta cuántas dimensiones son diferentes
        """
        cost = 0
        if key_from.shape != key_to.shape:
            cost += 1
        if key_from.color != key_to.color:
            cost += 1
        if key_from.rotation != key_to.rotation:
            cost += 1
        return cost

    def stats(self) -> Dict[str, any]:
        """Retornar estadísticas de la DB"""
        total_entries = sum(len(v) for v in self.db.values())
        return {
            'num_states': len(self.db),
            'total_entries': total_entries,
            'avg_cost': sum(sum(v.values()) for v in self.db.values()) / max(total_entries, 1)
        }


# Instancia global (singleton)
_global_db: Optional[PatternDatabase] = None


def get_pattern_database(debug: bool = False) -> PatternDatabase:
    """
    Obtener instancia global de Pattern Database (lazy initialization)

    Args:
        debug: Si True, imprimir logs

    Returns:
        Instancia de PatternDatabase
    """
    global _global_db
    if _global_db is None:
        _global_db = PatternDatabase(debug=debug)
    return _global_db


def reset_pattern_database():
    """Resetear la instancia global (para testing)"""
    global _global_db
    _global_db = None
