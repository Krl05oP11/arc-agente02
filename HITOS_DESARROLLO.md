# PLAN DE DESARROLLO - RASTREO DE HITOS

**Proyecto:** arc-agente02  
**Estado:** 🚀 En Inicio (Fase 1)  
**Última actualización:** 2026-06-05

---

## FASE 1: NÚCLEO DE INFERENCIA

### Hito 1.1: Perceptor Completo ⬜
- [ ] Implementar `Perceptor.parse_grid()` para extraer entidades
- [ ] Crear clases `WorldState`, `Door`, `Rotator`, `Teleporter`
- [ ] Implementar `identify_entities()` para detectar objetos
- [ ] Implementar `extract_key_panel()` para llave inicial
- [ ] Manejar paredes, pisos, refills, teletransportadores
- [ ] **Unit tests:** Parsing L1 y L2
- [ ] **Validación:** Perceptor identifica correctamente todos los objetos

**Criterio de Éxito:** Perceptor puede parsear cualquier grid y producir WorldState correcto

---

### Hito 1.2: Inductor de Reglas v1 ⬜
- [ ] Implementar `extract_rotator_sequence(grid, path)`
- [ ] Analizar ejemplos L1: debería ser "shortest_path"
- [ ] Analizar ejemplos L2: debería ser "visit ROT, then DOOR"
- [ ] Implementar `infer_dsl_rule()` para generar programa DSL
- [ ] Soportar reglas simples: shortest_path, visit_rotators_in_order
- [ ] **Unit tests:** Inferencia correcta en L1 y L2
- [ ] Documentar formato DSL

**Criterio de Éxito:** Inductor infiere regla correcta para L1 y L2

---

### Hito 1.3: Validación de Reglas ⬜
- [ ] Implementar `InductorReglas.validate_rule(rule, examples)`
- [ ] Ejecutar planificador (stub) con regla en todos los ejemplos
- [ ] Verificar que salida coincide con soluciones esperadas
- [ ] Si regla falla, intentar alternativas (búsqueda de ordenes)
- [ ] **Unit tests:** Validación éxito/fracaso de reglas
- [ ] Feedback legible: qué falló y por qué

**Criterio de Éxito:** Sistema puede confirmar o rechazar una regla basado en ejemplos

---

## FASE 2: PLANIFICADOR Y BÚSQUEDA

### Hito 2.1: Estado Unificado ⬜
- [ ] Definir clase `State = (pos, key_shape, key_color, key_rotation, energy)`
- [ ] Implementar `StateGraph.neighbors(state)` respetando:
  - Paredes (no atravesables)
  - Rotadores (transforman llave)
  - Teletransportadores (salto instantáneo)
  - Puertas (requieren key match)
  - Refills (energía → 42)
- [ ] Manejar colisiones (rotadores transforman KEY on entry)
- [ ] **Unit tests:** neighbors() correcto para cada tipo de celda
- [ ] Validación: grafo conectado correctamente

**Criterio de Éxito:** StateGraph.neighbors() retorna transiciones correctas

---

### Hito 2.2: A* Básico ⬜
- [ ] Implementar algoritmo A* search
- [ ] Usar PriorityQueue con cost = g(n) + h(n)
- [ ] Heurística inicial simple: Manhattan distance a puerta
- [ ] Reconstrucción de camino (came_from tracking)
- [ ] **Unit tests:** A* encuentra camino en L1 (< 50ms)
- [ ] Benchmarking: tiempo de búsqueda

**Criterio de Éxito:** A* encuentra camino óptimo en L1

---

### Hito 2.3: Pattern Database ⬜
- [ ] Precompute tabla: DB[key_A][key_B] = min rotators needed
- [ ] Integrar en heurística: h = manhattan + DB cost
- [ ] Validar que heurística sigue siendo admisible
- [ ] **Unit tests:** DB devuelve valores correctos
- [ ] Benchmarking: mejora en velocidad de búsqueda (vs 2.2)

**Criterio de Éxito:** A* con heurística mejorada es más rápido

---

### Hito 2.4: Manejo de Restricciones ⬜
- [ ] Integrar reglas inferidas en State transitions
- [ ] CSP simple: si regla dice "visit ROT antes DOOR", forbid DOOR antes ROT
- [ ] Implementar precondiciones en neighbors()
- [ ] Propagar restricciones desde Rule a StateGraph
- [ ] **Unit tests:** Plan respeta restricciones
- [ ] Validación: no se viola ninguna restricción

**Criterio de Éxito:** Planificador respeta todas las restricciones de la regla

---

## FASE 3: MÓDULOS AUXILIARES

### Hito 3.1: Renderizador ⬜
- [ ] Implementar `Renderizador.render(plan, grid)`
- [ ] Convertir plan (lista de posiciones) a grid con camino dibujado
- [ ] Marcar celdas con color correcto (típicamente rojo)
- [ ] Coincidir exactamente con formato de ejemplos
- [ ] **Unit tests:** Salida visual correcta
- [ ] Validación: pixel-perfect match (si es necesario)

**Criterio de Éxito:** Salida rendered coincide con ejemplos esperados

---

### Hito 3.2: Supervisor (Pipeline) ⬜
- [ ] Conectar Perceptor → Inductor → Planificador → Renderizador
- [ ] Implementar `Supervisor.run(examples, test)`
- [ ] Manejo de errores en cada etapa
- [ ] Fallback: si algo falla, intentar estrategia alternativa
- [ ] **Unit tests:** Pipeline L1-L2 completo end-to-end
- [ ] Logging detallado de cada etapa

**Criterio de Éxito:** Pipeline completo funciona en L1 y L2

---

### Hito 3.3: Multi-vida ⬜
- [ ] Planificador puede insertar RESET si energía insuficiente
- [ ] Modelar como transición: (energy=0) → (energy=42, pos=start, life−1)
- [ ] Búsqueda continúa con vidas restantes
- [ ] **Unit tests:** Problema requiere 2+ vidas
- [ ] Validación: plan usa exactamente N vidas

**Criterio de Éxito:** Planificador puede usar múltiples vidas si es necesario

---

## FASE 4: EXTENSIÓN A L3+

### Hito 4.1: Múltiples Rotators ⬜
- [ ] Inductor: inferir orden correcto de rotators (L3+)
- [ ] Soportar órdenes complejas: SH→CO→ROT, etc.
- [ ] CSP: formalizar prerequisitos y precedencias
- [ ] Planificador: generar plan que respeta orden
- [ ] **Unit tests:** L3 resuelto correctamente
- [ ] Validación: comparar con soluciones esperadas

**Criterio de Éxito:** L3 completado con regla inferida correcta

---

### Hito 4.2: Teleporters ⬜
- [ ] Perceptor: detectar pares teleporter (source, dest)
- [ ] StateGraph: agregar aristas con costo 1
- [ ] Consideraciones: ¿teleporter ayuda o perjudica?
- [ ] Planificador: integrar en búsqueda
- [ ] **Unit tests:** L4+ con teleporters
- [ ] Validación: teleporters usados inteligentemente

**Criterio de Éxito:** L4+ resuelto usando teleporters

---

## FASE 5: VISIBILIDAD PARCIAL (L7)

### Hito 5.1: Memory & Exploration ⬜
- [ ] Mantener mapa explorado (30×30 grid: desconocido/pared/libre)
- [ ] Implementar frontier-based exploration
- [ ] Dirigirse a frontera más cercana (celda desconocida adyacente)
- [ ] Update mapa cuando nuevas celdas se ven
- [ ] **Unit tests:** Explorador llega a fronteras correctas
- [ ] Validación: mapa converge a estado real

**Criterio de Éxito:** Explorador descubre todo el mapa

---

### Hito 5.2: Replanificación ⬜
- [ ] Detectar cuando plan falló (pared inesperada)
- [ ] Recomputar mapa local con nueva información
- [ ] Replanificar usando información actualizada
- [ ] Loop: explore → plan → execute → replan
- [ ] **Unit tests:** Replanificación en tiempo real
- [ ] Validación: no entra en loops infinitos

**Criterio de Éxito:** Sistema puede replanificar cuando plan falla

---

### Hito 5.3: LRTA* Online ⬜
- [ ] Implementar Learning Real-Time A*
- [ ] Buscar localmente cuando stuck
- [ ] Update heurística basado en experiencia
- [ ] Combinar con exploration + replan
- [ ] **Unit tests:** L7 exploración + solución
- [ ] Validación: completa L7 exitosamente

**Criterio de Éxito:** L7 resuelto con visibilidad parcial

---

## FASE 6: VALIDACIÓN & OPTIMIZACIÓN

### Hito 6.1: Test Suite Completo ⬜
- [ ] Unit tests para cada módulo (≥ 80% coverage)
- [ ] Integration tests para pipeline completo
- [ ] Test cases para cada nivel (L1-L7)
- [ ] Regresión: verificar fixes no rompan lo anterior
- [ ] Coverage report visible
- [ ] CI/CD setup (pytest automático)

**Criterio de Éxito:** Todos los tests pasan, ≥ 80% coverage

---

### Hito 6.2: Benchmarking ⬜
- [ ] Medir tiempo: inference + planning por nivel
- [ ] Consumo de memoria durante búsqueda
- [ ] Comparación con arc-superagent (si aplica)
- [ ] Identificar bottlenecks
- [ ] Documentar resultados

**Criterio de Éxito:** Rendimiento < 60s por nivel, < 2GB RAM

---

### Hito 6.3: Optimizaciones ⬜
- [ ] Profiling: identificar bottlenecks reales
- [ ] Caché de resultados (memoization)
- [ ] Paralelización donde sea posible (multiprocessing)
- [ ] Reducir overhead de búsqueda
- [ ] Recompilación de código crítico si aplica

**Criterio de Éxito:** Rendimiento mejorado ≥ 30% sin perder corrección

---

## MATRIZ DE RASTREO

| Fase | Hito | Estado | Responsable | Notas |
|------|------|--------|-------------|-------|
| 1 | 1.1 | ✅ | - | Perceptor |
| 1 | 1.2 | ✅ | - | Inductor v1 |
| 1 | 1.3 | ✅ | - | Validación |
| 2 | 2.1 | ✅ | - | Estado Unificado |
| 2 | 2.2 | ✅ | - | A* Básico |
| 2 | 2.3 | ✅ | - | Pattern DB |
| 2 | 2.4 | ⬜ | - | Restricciones |
| 3 | 3.1 | ⬜ | - | Renderizador |
| 3 | 3.2 | ⬜ | - | Supervisor |
| 3 | 3.3 | ⬜ | - | Multi-vida |
| 4 | 4.1 | ⬜ | - | Multi-rotators |
| 4 | 4.2 | ⬜ | - | Teleporters |
| 5 | 5.1 | ⬜ | - | Memory & Explor |
| 5 | 5.2 | ⬜ | - | Replan |
| 5 | 5.3 | ⬜ | - | LRTA* |
| 6 | 6.1 | ⬜ | - | Tests |
| 6 | 6.2 | ⬜ | - | Benchmark |
| 6 | 6.3 | ⬜ | - | Optimize |

**Leyenda:**
- ⬜ = No iniciado
- 🟨 = En progreso
- ✅ = Completado
- ❌ = Bloqueado

---

## NOTAS IMPORTANTES

1. **Los hitos NO tienen duraciones en semanas** — el enfoque es completar cada hito correctamente, no rápidamente
2. **Progresión es progresiva** — cada fase construye sobre la anterior
3. **Testing es parte de cada hito** — no agregar tests después
4. **Documentación es esencial** — código autodocumentado + docstrings
5. **Refactorización permitida** — mejorar diseño entre hitos

---

## CAMBIOS HISTÓRICOS

- **2026-06-05:** Documento creado con 18 hitos en 6 fases
