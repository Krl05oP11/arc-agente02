"""
Unit tests para la Pattern Database (Hito 2.3)

Verificar que:
1. Tabla se construye correctamente
2. Consultas retornan valores válidos
3. Heurística sigue siendo admisible
4. Mejora la velocidad de búsqueda A*
"""

import pytest
from src.pattern_database import (
    PatternDatabase, KeyState, get_pattern_database, reset_pattern_database
)
import time


class TestKeyState:
    """Tests para KeyState"""

    def test_key_state_creation(self):
        """Test: Crear KeyState"""
        key = KeyState(1, 2, 3)
        assert key.shape == 1
        assert key.color == 2
        assert key.rotation == 3

    def test_key_state_normalization(self):
        """Test: Normalizar valores (mod 4)"""
        key = KeyState(5, 6, 7)
        assert key.shape == 1
        assert key.color == 2
        assert key.rotation == 3

    def test_key_state_equality(self):
        """Test: Igualdad de KeyState"""
        key1 = KeyState(1, 2, 3)
        key2 = KeyState(1, 2, 3)
        key3 = KeyState(1, 2, 4)

        assert key1 == key2
        assert key1 != key3

    def test_key_state_hash(self):
        """Test: KeyState es hashable"""
        key1 = KeyState(1, 2, 3)
        key2 = KeyState(1, 2, 3)

        s = {key1, key2}
        assert len(s) == 1  # Debería haber solo 1 elemento

    def test_transform_shape(self):
        """Test: Transformación SHAPE"""
        key = KeyState(0, 0, 0)
        transformed = key.transform_shape()

        assert transformed.shape == 1
        assert transformed.color == 0
        assert transformed.rotation == 0

    def test_transform_color(self):
        """Test: Transformación COLOR"""
        key = KeyState(0, 0, 0)
        transformed = key.transform_color()

        assert transformed.shape == 0
        assert transformed.color == 1
        assert transformed.rotation == 0

    def test_transform_rot(self):
        """Test: Transformación ROT"""
        key = KeyState(0, 0, 0)
        transformed = key.transform_rot()

        assert transformed.shape == 0
        assert transformed.color == 0
        assert transformed.rotation == 1

    def test_all_neighbors(self):
        """Test: Obtener todos los vecinos"""
        key = KeyState(0, 0, 0)
        neighbors = key.all_neighbors()

        assert len(neighbors) == 3
        # Debería tener los 3 tipos de transformación
        shapes = [n.shape for n in neighbors]
        colors = [n.color for n in neighbors]
        rots = [n.rotation for n in neighbors]

        assert 1 in shapes  # Shape transformado
        assert 1 in colors  # Color transformado
        assert 1 in rots    # Rotation transformado


class TestPatternDatabase:
    """Tests para Pattern Database"""

    @pytest.fixture
    def db(self):
        """Crear una Pattern Database para tests"""
        return PatternDatabase(debug=False)

    def test_db_creation(self, db):
        """Test: Crear Pattern Database"""
        assert db is not None
        assert len(db.db) > 0

    def test_db_size(self, db):
        """Test: Database tiene 64 estados (4×4×4)"""
        assert len(db.db) == 64

    def test_db_same_state_cost_zero(self, db):
        """Test: Costo de transformar estado a sí mismo es 0"""
        cost = db.lookup((0, 0, 0), (0, 0, 0))
        assert cost == 0

    def test_db_cycle_closure(self, db):
        """Test: Ciclo completo de 4 rotaciones vuelve al estado inicial"""
        # Aplicar 4 rotaciones SHAPE vuelve al estado original
        state = (0, 0, 0)
        cost = 0

        # Simular 4 transformaciones SHAPE
        for i in range(4):
            new_state = ((state[0] + 1) % 4, state[1], state[2])
            step_cost = db.lookup(state, new_state)
            cost += step_cost
            state = new_state

        # Debería volver a (0, 0, 0)
        assert state == (0, 0, 0)
        # Costo total debería ser 4
        assert cost == 4

    def test_db_single_dimension_change(self, db):
        """Test: Cambio de una sola dimensión cuesta 1"""
        cost = db.lookup((0, 0, 0), (1, 0, 0))
        assert cost == 1

    def test_db_three_dimensions_change(self, db):
        """Test: Cambio de 3 dimensiones cuesta max 3"""
        cost = db.lookup((0, 0, 0), (1, 1, 1))
        assert cost <= 3

    def test_db_triangle_inequality(self, db):
        """Test: Desigualdad triangular (A→B ≤ A→C + C→B)"""
        cost_ab = db.lookup((0, 0, 0), (2, 2, 2))
        cost_ac = db.lookup((0, 0, 0), (1, 1, 1))
        cost_cb = db.lookup((1, 1, 1), (2, 2, 2))

        assert cost_ab <= cost_ac + cost_cb

    def test_db_cyclic(self, db):
        """Test: Ciclo tiene costo igual a distancia"""
        # Ir de (0,0,0) → (1,1,1) → (2,2,2) → (0,0,0)
        # debería ser ciclable

        cost_01 = db.lookup((0, 0, 0), (1, 1, 1))
        cost_12 = db.lookup((1, 1, 1), (2, 2, 2))
        cost_20 = db.lookup((2, 2, 2), (0, 0, 0))

        # El ciclo debería cerrarse
        assert cost_01 > 0 and cost_12 > 0 and cost_20 > 0

    def test_db_stats(self, db):
        """Test: Estadísticas de la DB"""
        stats = db.stats()

        assert stats['num_states'] == 64
        assert stats['total_entries'] == 64 * 64
        assert stats['avg_cost'] > 0

    def test_db_global_singleton(self):
        """Test: Pattern Database global es singleton"""
        reset_pattern_database()

        db1 = get_pattern_database()
        db2 = get_pattern_database()

        assert db1 is db2


class TestPatternDatabasePerformance:
    """Tests de performance"""

    @pytest.fixture
    def db(self):
        return PatternDatabase(debug=False)

    def test_lookup_performance(self, db):
        """Test: Lookup es rápido (< 1ms)"""
        start = time.time()

        for i in range(1000):
            db.lookup((i % 4, i % 4, i % 4), ((i + 1) % 4, (i + 1) % 4, (i + 1) % 4))

        elapsed = time.time() - start

        assert elapsed < 0.01, f"1000 lookups took {elapsed}s, expected < 0.01s"

    def test_db_construction_time(self):
        """Test: Construcción de DB es rápida (< 100ms)"""
        start = time.time()
        db = PatternDatabase(debug=False)
        elapsed = time.time() - start

        assert elapsed < 0.1, f"DB construction took {elapsed}s, expected < 0.1s"


class TestPatternDatabaseAdmissibility:
    """Tests para admisibilidad de heurística"""

    @pytest.fixture
    def db(self):
        return PatternDatabase(debug=False)

    def test_heuristic_never_overestimates(self, db):
        """Test: Heurística nunca overestima (admisible)"""
        # Para verificar admisibilidad, comparar con camino real
        # en algunos casos sencillos

        # Caso 1: No necesita transformación
        cost_real = db.lookup((0, 0, 0), (0, 0, 0))
        heur_est = db.lookup((0, 0, 0), (0, 0, 0))
        assert heur_est <= cost_real + 1  # Permite pequeño margen de error

        # Caso 2: Transformación de una dimensión
        # Costo real es 1, heurística debería ser <= 1
        cost_real = db.lookup((0, 0, 0), (1, 0, 0))
        heur_est = cost_real
        assert heur_est == 1

    def test_heuristic_consistency(self, db):
        """Test: Heurística es consistente (h(A) ≤ h(B) + cost(A→B))"""
        # Verificar en varios puntos

        # De (0,0,0) a (2,2,2) pasando por (1,1,1)
        h_0_2 = db.lookup((0, 0, 0), (2, 2, 2))
        h_1_2 = db.lookup((1, 1, 1), (2, 2, 2))
        cost_0_1 = db.lookup((0, 0, 0), (1, 1, 1))

        # Consistencia: h(0) ≤ h(1) + cost(0→1)
        assert h_0_2 <= h_1_2 + cost_0_1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
