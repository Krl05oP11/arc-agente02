# ARC-AGENTE02: Symbolic Learning Agent for ARC-AGI-3

**Proyecto:** Agente que aprende reglas de juego a partir de pocos ejemplos y planifica óptimamente para resolver laberintos complejos.

**Status:** 🚀 En desarrollo (Fase 1)

## Inicio Rápido

### Con Docker
```bash
docker-compose up -d
docker-compose run arc-agente02 bash

# Dentro del container:
python -m pytest tests/
```

### Local
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/
python -c "from src.supervisor import Supervisor; ..."
```

## Documentación Principal

- **[PROYECTO_FUNDACIONAL.md](docs/PROYECTO_FUNDACIONAL.md)** — Análisis, arquitectura, plan de desarrollo
- **[API.md](docs/API.md)** — Especificación de interfaces (TBD)
- **[ARCHITECTURAL_DECISIONS.md](docs/ARCHITECTURAL_DECISIONS.md)** — ADRs (TBD)

## Arquitectura (6 Módulos)

```
Perceptor → Mapeador → Inductor → Planificador → Renderizador
                          ↓
                      Supervisor (Orquestador)
```

1. **Perceptor** — Parse grid → WorldState
2. **Mapeador** — WorldState → StateGraph
3. **Inductor** — Examples → Rule
4. **Planificador** — A* search optimal plan
5. **Renderizador** — Plan → output grid
6. **Supervisor** — Coordina pipeline

## Plan de Desarrollo

### Fase 1: Núcleo de Inferencia
- [ ] Hito 1.1: Perceptor Completo
- [ ] Hito 1.2: Inductor de Reglas v1
- [ ] Hito 1.3: Validación de Reglas

### Fase 2: Planificador y Búsqueda
- [ ] Hito 2.1: Estado Unificado
- [ ] Hito 2.2: A* Básico
- [ ] Hito 2.3: Pattern Database
- [ ] Hito 2.4: Manejo de Restricciones

### Fase 3: Módulos Auxiliares
- [ ] Hito 3.1: Renderizador
- [ ] Hito 3.2: Supervisor (Pipeline)
- [ ] Hito 3.3: Multi-vida

### Fase 4: Extensión L3+
- [ ] Hito 4.1: Múltiples Rotators
- [ ] Hito 4.2: Teleporters

### Fase 5: Visibilidad Parcial (L7)
- [ ] Hito 5.1: Memory & Exploration
- [ ] Hito 5.2: Replanificación
- [ ] Hito 5.3: LRTA* Online

### Fase 6: Validación & Optimización
- [ ] Hito 6.1: Test Suite Completo
- [ ] Hito 6.2: Benchmarking
- [ ] Hito 6.3: Optimizaciones

## Métricas de Éxito

| Métrica | Criterio |
|---------|----------|
| Reglas Inferidas | ≥ 4/7 niveles |
| Planos Óptimos | ≥ 5/7 niveles |
| Rendimiento | < 60s por nivel |
| Test Coverage | ≥ 80% |

## Contribuciones

Por favor referirse a [PROYECTO_FUNDACIONAL.md](docs/PROYECTO_FUNDACIONAL.md) para especificaciones técnicas detalladas.
