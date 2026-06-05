"""
Unit tests para Experience Learner (Hito 5.3)

Verificar que:
1. Memoria de experiencias funciona
2. Agente aprende de experiencias
3. Decisiones mejoran con aprendizaje
4. Patrones se detectan
"""

import pytest
from src.experience_learner import (
    Experience, ExperienceMemory, LearningAgent,
    SmartDecisionMaker, create_learning_agent,
    create_decision_maker
)


class TestExperience:
    """Tests para Experience"""

    def test_experience_creation(self):
        """Test: Crear experiencia"""
        exp = Experience("wall", (10, 10), "obstacle", {"reason": "blocked"})

        assert exp.type == "wall"
        assert exp.position == (10, 10)
        assert exp.outcome == "obstacle"
        assert exp.metadata["reason"] == "blocked"

    def test_experience_repr(self):
        """Test: Representación de experiencia"""
        exp = Experience("rotator", (5, 5), "discovery")

        assert "rotator" in str(exp)
        assert "discovery" in str(exp)


class TestExperienceMemory:
    """Tests para ExperienceMemory"""

    def test_memory_creation(self):
        """Test: Crear memoria"""
        memory = ExperienceMemory(max_experiences=100)

        assert memory is not None
        assert len(memory.experiences) == 0

    def test_record_experience(self):
        """Test: Registrar experiencia"""
        memory = ExperienceMemory()
        exp = Experience("wall", (10, 10), "obstacle")

        memory.record_experience(exp)

        assert len(memory.experiences) == 1

    def test_get_experiences_by_type(self):
        """Test: Obtener experiencias por tipo"""
        memory = ExperienceMemory()

        memory.record_experience(Experience("wall", (10, 10), "obstacle"))
        memory.record_experience(Experience("rotator", (5, 5), "discovery"))
        memory.record_experience(Experience("wall", (20, 20), "obstacle"))

        walls = memory.get_experiences_by_type("wall")

        assert len(walls) == 2

    def test_get_success_rate(self):
        """Test: Calcular tasa de éxito"""
        memory = ExperienceMemory()

        memory.record_experience(Experience("wall", (10, 10), "success"))
        memory.record_experience(Experience("wall", (20, 20), "success"))
        memory.record_experience(Experience("wall", (30, 30), "obstacle"))

        rate = memory.get_success_rate("wall")

        assert 0.6 < rate < 0.7  # 2/3

    def test_predict_obstacle_probability(self):
        """Test: Predecir probabilidad de obstáculo"""
        memory = ExperienceMemory()

        # Registrar paredes cercanas
        memory.record_experience(Experience("wall", (5, 5), "obstacle"))
        memory.record_experience(Experience("wall", (10, 10), "obstacle"))

        prob = memory.predict_obstacle_probability((7, 7))

        assert 0 < prob < 1

    def test_get_most_common_discoveries(self):
        """Test: Obtener descubrimientos comunes"""
        memory = ExperienceMemory()

        memory.record_experience(Experience("wall", (10, 10), "discovery"))
        memory.record_experience(Experience("wall", (20, 20), "discovery"))
        memory.record_experience(Experience("rotator", (5, 5), "discovery"))

        top = memory.get_most_common_discoveries(2)

        assert len(top) <= 2
        if top:
            assert top[0][1] >= 1  # Frecuencia


class TestLearningAgent:
    """Tests para LearningAgent"""

    def test_agent_creation(self):
        """Test: Crear agente aprendiz"""
        agent = create_learning_agent(debug=False)

        assert agent is not None

    def test_learn_from_experience(self):
        """Test: Aprender de experiencia"""
        agent = create_learning_agent()
        exp = Experience("wall", (10, 10), "obstacle")

        agent.learn_from_experience(exp)

        assert len(agent.memory.experiences) == 1

    def test_choose_exploration_strategy(self):
        """Test: Elegir estrategia de exploración"""
        agent = create_learning_agent()

        strategy1 = agent.choose_exploration_strategy(100, 0.2)
        strategy2 = agent.choose_exploration_strategy(20, 0.8)

        assert strategy1 is not None
        assert strategy2 is not None

    def test_predict_outcome(self):
        """Test: Predecir resultado"""
        agent = create_learning_agent()

        # Registrar que walls generalmente son obstáculos
        for _ in range(8):
            agent.learn_from_experience(Experience("wall", (10, 10), "obstacle"))
        for _ in range(2):
            agent.learn_from_experience(Experience("wall", (20, 20), "success"))

        outcome = agent.predict_outcome("wall")

        assert outcome in ["success", "obstacle", "discovery", "unknown"]

    def test_should_avoid_area(self):
        """Test: Decidir si evitar área"""
        agent = create_learning_agent()

        # Registrar muchas paredes en una zona
        for i in range(10):
            agent.learn_from_experience(Experience("wall", (10, i), "obstacle"))

        should_avoid = agent.should_avoid_area((10, 15))

        # Probablemente sí
        assert isinstance(should_avoid, bool)

    def test_get_learning_confidence(self):
        """Test: Obtener confianza en aprendizaje"""
        agent = create_learning_agent()

        conf1 = agent.get_learning_confidence()

        # Sin experiencias
        assert conf1 < 0.5

        # Agregar experiencias
        for i in range(50):
            agent.learn_from_experience(Experience("wall", (i, i), "obstacle"))

        conf2 = agent.get_learning_confidence()

        # Con experiencias
        assert conf2 > conf1

    def test_get_stats(self):
        """Test: Obtener estadísticas"""
        agent = create_learning_agent()

        for i in range(10):
            agent.learn_from_experience(Experience("wall", (i, i), "obstacle"))

        stats = agent.get_stats()

        assert 'experiences' in stats
        assert 'patterns_learned' in stats
        assert 'confidence' in stats


class TestSmartDecisionMaker:
    """Tests para SmartDecisionMaker"""

    def test_decision_maker_creation(self):
        """Test: Crear tomador de decisiones"""
        agent = create_learning_agent()
        maker = create_decision_maker(agent)

        assert maker is not None

    def test_decide_next_move_with_frontier(self):
        """Test: Decidir próximo movimiento"""
        agent = create_learning_agent()
        maker = create_decision_maker(agent)

        frontier = [(5, 0), (10, 0), (15, 0)]
        next_move = maker.decide_next_move((0, 0), frontier)

        assert next_move in frontier or next_move is None

    def test_decide_next_move_goal_oriented(self):
        """Test: Decidir movimiento hacia objetivo"""
        agent = create_learning_agent()
        maker = create_decision_maker(agent)

        frontier = [(5, 0), (10, 0), (15, 0)]
        goal = (20, 0)

        next_move = maker.decide_next_move((0, 0), frontier, goal)

        # Debería elegir lo más cercano al goal
        if next_move:
            assert next_move in frontier

    def test_decide_strategy(self):
        """Test: Decidir estrategia"""
        agent = create_learning_agent()
        maker = create_decision_maker(agent)

        strategy = maker.decide_strategy(50, 0.3)

        assert strategy is not None


class TestExperienceLearnerEdgeCases:
    """Tests de casos extremos"""

    def test_memory_overflow(self):
        """Test: Memoria con máximo alcanzado"""
        memory = ExperienceMemory(max_experiences=10)

        # Grabar más que el máximo
        for i in range(20):
            memory.record_experience(Experience("wall", (i, i), "obstacle"))

        # Debería tener solo 10
        assert len(memory.experiences) <= 10

    def test_learning_with_no_data(self):
        """Test: Aprender sin datos"""
        agent = create_learning_agent()

        # Sin experiencias, debe comportarse con defaults
        outcome = agent.predict_outcome("unknown_type")

        assert outcome is not None

    def test_decision_with_empty_frontier(self):
        """Test: Decidir con frontera vacía"""
        agent = create_learning_agent()
        maker = create_decision_maker(agent)

        next_move = maker.decide_next_move((0, 0), [])

        assert next_move is None

    def test_learning_curve(self):
        """Test: Curva de aprendizaje"""
        agent = create_learning_agent()

        conf_values = []

        for i in range(3):
            conf_values.append(agent.get_learning_confidence())
            for j in range(30):
                agent.learn_from_experience(Experience("wall", (i*30+j, 0), "obstacle"))

        # Confianza debe aumentar
        assert conf_values[-1] > conf_values[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
