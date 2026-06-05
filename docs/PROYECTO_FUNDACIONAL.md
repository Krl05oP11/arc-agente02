# PROYECTO ARC-AGENTE02
## DOCUMENTO FUNDACIONAL

**Versión:** 1.0  
**Fecha:** 2026-06-05  
**Estado:** Preparado para aprobación  
**Responsable:** Carlos + Claude

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis del Problema](#análisis-del-problema)
3. [Requisitos del Proyecto](#requisitos-del-proyecto)
4. [Arquitectura del Sistema](#arquitectura-del-sistema)
5. [Especificaciones Técnicas por Módulo](#especificaciones-técnicas-por-módulo)
6. [Plan de Desarrollo](#plan-de-desarrollo)
7. [Infraestructura & Despliegue](#infraestructura--despliegue)
8. [Validación & Testing](#validación--testing)

---

## RESUMEN EJECUTIVO

### Visión
Desarrollar un agente simbólico con aprendizaje que **aprenda las reglas de juego a partir de pocos ejemplos** y luego **planifique óptimamente** para resolver laberintos con múltiples restricciones en la competición ARC-AGI-3.

### Diferencia con arc-superagent
- **arc-superagent:** Intenta jugar directamente; descubre reglas por ensayo-error
- **arc-agente02:** Analiza ejemplos; infiere reglas formalmente; planifica bajo esas reglas

### Objetivo
Resolver los **7 niveles de ls20** (y escalar a otros problemas ARC) mediante:
1. **Inferencia de reglas** desde ejemplos de entrenamiento
2. **Planificación óptima** con búsqueda heurística (A*)
3. **Exploración inteligente** para visibilidad parcial (L7)

### Resultado Esperado
- Nivel 1-6: Solución óptima (análisis de ejemplos + A*)
- Nivel 7: Exploración + replanificación bajo incertidumbre
- **Éxito: 5-7 niveles resueltos** (vs actual 1 nivel en arc-superagent)

---

## ANÁLISIS DEL PROBLEMA

### 1. Naturaleza de la Tarea ARC-ls20

#### 1.1 ¿Qué es realmente ls20?

**NO es:** Un simple problema de pathfinding (A* ya lo resolvería)

**SÍ es:** Un problema de **aprendizaje automático simbólico** con dos fases:

**Fase 1: Learning (aprendizaje)**
- Recibimos N ejemplos de entrenamiento (típicamente 3-4)
- Cada ejemplo: cuadrícula de entrada + solución (camino dibujado)
- Tarea: **Inferir la REGLA OCULTA** que define un camino válido

**Fase 2: Testing (aplicación)**
- Recibimos una nueva cuadrícula (test set)
- Aplicamos la regla aprendida
- Encontramos la solución óptima que satisface la regla

#### 1.2 La Regla Oculta (ejemplos)

**L1:** "Camino más corto desde start hasta DOOR"
- Trivial: shortest path

**L2:** "Atacar al ROT rotator hasta transformar KEY a estado correcto, luego alcanzar DOOR"
- Prerequisito: KEY debe estar en estado específico
- Acción: Visitar ROT (ataque por colisión)

**L3+:** Múltiples rotators, órdenes específicos, teleporters, etc.

**L7:** Todo lo anterior + visibilidad parcial (radio ~5 celdas)

#### 1.3 Por Qué Es Difícil para la IA

Humanos: Vemos el patrón inmediatamente ("ah, colecciona las llaves en orden")

Máquina: Espacio de hipótesis enorme
- ¿Qué define un camino válido?
- ¿Qué hace cada rotator?
- ¿Hay prerequisitos?
- ¿Qué restricciones existen?

Nuestra solución: **Búsqueda en un espacio de reglas pequeño + validación en ejemplos**

### 2. Sistema de Juego

#### 2.1 Grid Geometry
- **Dimensión:** 30×30 celdas (filas × columnas)
- **Indexación:** (row, col) con (0,0) en esquina superior izquierda
- **Coordenadas:** [0..29] × [0..29]

#### 2.2 Objetos Principales

| Objeto | Cantidad | Propiedades |
|--------|----------|-----------|
| Player | 1 | Posición, energía (42/vida) |
| Walls | Variable | Posiciones no-transitables |
| Floors | Variable | Celdas vacías |
| Key Panel | 1 | Fijo en (25–29, 0–4), no transitable |
| Door | 1 | Requisito: Key state matching |
| Rotators | 1-3 | Tipo: SHAPE, COLOR, ROT |
| Refills | 1-2 | Restaura energía a 42 |
| Teleporters | 0-8 | Par: source → destination |

#### 2.3 Dinámica de Juego

**Estado inicial:**
- Player en posición inicio
- Key en estado inicial (shape_0, color_0, rotation_0)
- Energía = 42

**Cada acción:**
- Move (UP/DOWN/LEFT/RIGHT): 1 energía
- Teleporter: 1 energía (destino instantáneo)
- Rotator (colisión): 1 energía + transforma Key

**Victorias/Fracaso:**
- **Win:** Alcanzar DOOR cuando Key matches requisito
- **Fracaso:** Energía = 0 antes de win
- **Multi-vida:** 3 vidas, Key persiste entre vidas

---

## REQUISITOS DEL PROYECTO

### Requisitos Funcionales

| ID | Requisito | Prioridad | Descripción |
|----|-----------|-----------|----|
| RF-1 | Rule Inference | CRITICAL | Analizar ejemplos, inferir regla de juego |
| RF-2 | World Modeling | CRITICAL | Grafo de mundo con estado (position, key_state, energy) |
| RF-3 | Optimal Planning | CRITICAL | A* sobre espacio de estados unificado |
| RF-4 | Constraint Handling | CRITICAL | Validar y respetar prerequisitos |
| RF-5 | Multi-life Management | HIGH | Planificar usando múltiples vidas si es necesario |
| RF-6 | Teleporter Handling | HIGH | Detectar y modelar teletransportadores |
| RF-7 | Exploration (L7) | HIGH | Exploración bajo visibilidad parcial |
| RF-8 | Pattern Database | MEDIUM | Precompute key transformation costs |
| RF-9 | Curriculum Learning | MEDIUM | Aprender simples primero, generalizar a complejos |
| RF-10 | Validation | MEDIUM | Verificar que plan satisface regla inferida |

### Requisitos No-Funcionales

| ID | Requisito | Criterio |
|----|-----------|----------|
| RNF-1 | Modularidad | Cada módulo ≤ 500 líneas, responsabilidad única |
| RNF-2 | Testabilidad | Unit tests para cada módulo |
| RNF-3 | Mantenibilidad | Código comentado, documentado, SOLID |
| RNF-4 | Performance | Inferencia + planning < 60s por nivel |
| RNF-5 | Isolation | Dockerizado para reproducibilidad |
| RNF-6 | Version Control | Git con historia clara |

---

## ARQUITECTURA DEL SISTEMA

### Visión General

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPERVISOR ORCHESTRATOR                   │
│  (Coordina pipeline: learn → plan → execute → validate)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┬───────────────────┐
    │                  │                  │                   │
    v                  v                  v                   v
┌─────────┐      ┌──────────┐      ┌──────────┐        ┌───────┐
│Perceptor│      │ Mapeador │      │ Inductor │        │Renderer│
│(Parser) │  →   │  (Graph) │  →   │(Learner) │   →    │(Output)│
└─────────┘      └──────────┘      └──────────┘        └───────┘
   Input:          Graph:             Rules:             Output:
  Raw Grid      (V, E, props)      DSL Programs      Rendered Path


             ┌─────────────────────────────────┐
             │  PLANIFICADOR (A* con CSP)      │
             │  (Núcleo de búsqueda)           │
             │                                 │
             │ State: (pos, key, energy, ...)  │
             │ Heurística: Manhattan + DB      │
             │ Restricciones: prerequisitos    │
             └─────────────────────────────────┘
```

### 6 Módulos Principales

#### 1. **Perceptor (Analizador)**
- **Entrada:** Matriz 30×30 de colores/símbolos
- **Proceso:** Identificar entidades (player, walls, rotators, doors, etc.)
- **Salida:** Estructura de datos (WorldState)
- **Responsabilidad:** Abstracción de la percepción cruda

#### 2. **Mapeador (Constructor de Grafo)**
- **Entrada:** WorldState
- **Proceso:** Construir grafo con nodos y aristas
- **Salida:** StateGraph (posiciones + propiedades + transiciones)
- **Responsabilidad:** Modelo del entorno

#### 3. **Inductor de Reglas (Learner)**
- **Entrada:** Training examples (input grids + solution paths)
- **Proceso:** Inferir regla que explica las soluciones
- **Salida:** Rule object (DSL, lógica, o programa)
- **Responsabilidad:** Aprendizaje desde ejemplos

#### 4. **Planificador (A* + CSP)**
- **Entrada:** WorldState + Rule + Goal
- **Proceso:** Búsqueda A* sobre espacio de estados
- **Salida:** Plan (secuencia de acciones)
- **Responsabilidad:** Búsqueda óptima respetando restricciones

#### 5. **Renderizador (Executor)**
- **Entrada:** Plan (secuencia de posiciones)
- **Proceso:** Traducir a salida visual (grid con camino dibujado)
- **Salida:** Imagen/Grid de salida
- **Responsabilidad:** Formato de salida exacto

#### 6. **Supervisor (Orquestador)**
- **Entrada:** Problema (ejemplos + test)
- **Proceso:** Coordinar módulos 1-5, gestionar pipeline
- **Salida:** Solución final
- **Responsabilidad:** Flujo de control, validación, manejo de errores

---

## ESPECIFICACIONES TÉCNICAS POR MÓDULO

### Módulo 1: PERCEPTOR

```python
class Perceptor:
    """Parse grid → WorldState"""
    
    def parse_grid(self, grid: np.ndarray) -> WorldState:
        """
        Entrada: 30×30 numpy array de colores
        Salida: WorldState con entidades identificadas
        """
        pass
    
    def identify_entities(self, grid) -> Dict:
        """
        Detectar:
        - player_position
        - walls (celdas negras)
        - door (posición + requisito)
        - rotators (SHAPE, COLOR, ROT con posiciones)
        - refills (posiciones)
        - teleporters (pares source → dest)
        - key_panel (fijo 25-29, 0-4, no transitable)
        """
        pass

class WorldState:
    player_pos: Tuple[int, int]
    walls: Set[Tuple[int, int]]
    doors: List[Door]  # Door = (pos, required_key_state)
    rotators: List[Rotator]  # (pos, type: SHAPE|COLOR|ROT)
    refills: List[Tuple[int, int]]
    teleporters: List[Teleporter]  # (src, dst)
    key_state: KeyState  # (shape_id, color_id, rotation_id)
    energy: int
```

**Salida esperada:** WorldState correctamente poblado

---

### Módulo 2: MAPEADOR

```python
class Mapeador:
    """WorldState → StateGraph"""
    
    def build_graph(self, world: WorldState) -> StateGraph:
        """
        Construir grafo donde:
        - Nodos: estados (pos, key_state, energy, ...)
        - Aristas: transiciones válidas
        """
        pass
    
    def get_neighbors(self, state: State) -> List[Tuple[State, cost]]:
        """
        Para cada dirección (UP, DOWN, LEFT, RIGHT):
            1. Calcular next_pos = move(state.pos, dir)
            2. Si wall → skip
            3. Si rotator → new_key = apply(state.key, rotator)
            4. Si teleporter → next_pos = destination
            5. Si door → check key_state matches
            6. Si refill → next_energy = 42
            7. Agregar (next_state, cost=1)
        """
        pass

class State:
    position: Tuple[int, int]
    key_shape: int
    key_color: int
    key_rotation: int
    energy: int
    visited_rotators: Set[int] = None  # Para tracking

class StateGraph:
    """Grafo de búsqueda para A*"""
    def neighbors(self, state: State) -> List[Tuple[State, cost]]:
        pass
    
    def heuristic(self, state: State, goal: State) -> int:
        pass
```

**Salida esperada:** StateGraph con neighbors() callable

---

### Módulo 3: INDUCTOR DE REGLAS

```python
class InductorReglas:
    """Examples → Rule"""
    
    def infer_rule(self, examples: List[Example]) -> Rule:
        """
        Dado lista de (input_grid, solution_path):
        1. Extraer secuencia de rotadores en cada solución
        2. Buscar patrón común
        3. Formular hipótesis (DSL)
        4. Validar en todos los ejemplos
        5. Retornar regla confirmada
        """
        pass
    
    def extract_rotator_sequence(self, grid, path) -> List[Rotator]:
        """
        Dado un camino solución, retornar qué rotators fueron visitados
        en qué orden
        """
        pass
    
    def infer_dsl_rule(self, rotator_sequences: List[List[Rotator]]) -> str:
        """
        Dados múltiples secuencias, inferir la regla.
        Ejemplos de salida:
        - "visit SHAPE, then COLOR, then ROT"
        - "shortest_path_to_door"
        - "collect_key_then_door"
        """
        pass
    
    def validate_rule(self, rule: str, examples: List[Example]) -> bool:
        """
        Ejecutar planner con esta regla en todos los ejemplos.
        Si todas las soluciones generadas coinciden con las esperadas → True
        """
        pass

class Rule:
    """Abstracción de una regla de juego"""
    dsl_program: str  # Descripción legible
    constraint_list: List[str]  # Fórmulas CSP
    rotator_order: List[int]  # Orden requerido (si aplica)
```

**Salida esperada:** Rule object que explica validly todas las soluciones

---

### Módulo 4: PLANIFICADOR

```python
class Planificador:
    """State space search: A* con heurística multi-componente"""
    
    def plan(self, start: State, goal: State, rules: Rule) -> Plan:
        """
        A* search:
        1. Inicializar cola de prioridad con (0, start)
        2. Mientras no empty:
            a. Pop estado con costo mínimo
            b. Si == goal: reconstruir y retornar plan
            c. Para cada neighbor:
               - Calcular new_cost = cost + step_cost
               - Agregar heurístico: h = heuristic(neighbor, goal)
               - Insert en cola si es mejor
        """
        pass
    
    def heuristic(self, state: State, goal: State) -> int:
        """
        Heurística admisible multi-componente:
        
        h = manhattan_to_door(state.pos)  # Distancia celdas
          + pattern_db_cost(state.key, goal.key)  # Costo min transformación
          + energy_penalty(state.energy, estimated_remaining)
        
        Asegurar: h(state) ≤ h*(state) (admisible)
        """
        pass
    
    def build_pattern_database(self, rotators) -> Dict[KeyState, Dict[KeyState, int]]:
        """
        Precompute: para cada par de key states, 
        cuál es el número mínimo de rotators a visitar.
        
        Resultado: DB[key_A][key_B] = min_rotators_needed
        
        Se calcula offline una sola vez.
        """
        pass

class Plan:
    """Resultado de planning"""
    actions: List[Tuple[int, int]]  # Secuencia de posiciones
    cost: int  # Total energía gastada
    valid: bool  # Satisface rule?
```

**Salida esperada:** Plan con secuencia de movimientos óptima

---

### Módulo 5: RENDERIZADOR

```python
class Renderizador:
    """Plan → Output Grid"""
    
    def render(self, plan: Plan, original_grid: np.ndarray) -> np.ndarray:
        """
        Dado un plan (secuencia de posiciones):
        1. Copiar grid original
        2. Para cada posición en plan.actions:
            - Marcar celda con color específico (ej. rojo)
        3. Retornar grid modificado
        """
        pass
    
    def match_output_format(self, grid: np.ndarray, example_output) -> np.ndarray:
        """
        Asegurar que el formato exacto coincida con los ejemplos:
        - Tamaño
        - Colores
        - Espesor de línea (si aplica)
        """
        pass
```

**Salida esperada:** Grid 30×30 con camino dibujado

---

### Módulo 6: SUPERVISOR

```python
class Supervisor:
    """Orchestrator de todo el pipeline"""
    
    def run(self, problem: Problem) -> Solution:
        """
        Flujo:
        1. Perceptor.parse_grid(training examples) → WorldStates
        2. Mapeador.build_graph(world) → StateGraph
        3. InductorReglas.infer_rule(examples) → Rule
        4. Validar rule en training set
        5. Para test set:
            a. Perceptor.parse_grid(test) → WorldState
            b. Mapeador.build_graph(test) → StateGraph
            c. Planificador.plan(start, goal, rule) → Plan
            d. Renderizador.render(plan) → Output
        6. Retornar Solution
        """
        pass
    
    def validate_rule(self, rule: Rule, examples) -> bool:
        """Verificar que rule es consistente con todos los ejemplos"""
        pass
    
    def curriculum_learning(self, levels: List[Level]):
        """
        Para múltiples niveles:
        1. Aprender L1 (más simple)
        2. Usar conocimiento de L1 como prior para L2
        3. etc.
        """
        pass
    
    def handle_failure(self, failure_reason: str):
        """Si la rule inference falla, intentar alternativas"""
        pass
```

---

## PLAN DE DESARROLLO

### FASE 1: Núcleo de Inferencia

**Hito 1.1: Perceptor Completo**
- [ ] Implementar `Perceptor.parse_grid()` para extraer entidades
- [ ] Crear clases `WorldState`, `Door`, `Rotator`, `Teleporter`
- [ ] Unit tests: parsing de grids L1 y L2
- [ ] Validación: perceptor identifica correctamente todos los objetos

**Hito 1.2: Inductor de Reglas v1**
- [ ] Implementar `extract_rotator_sequence(grid, path)`
- [ ] Analizar ejemplos L1 (debería ser "shortest path")
- [ ] Analizar ejemplos L2 (debería ser "visit ROT, then DOOR")
- [ ] Generar DSL program que explica el patrón
- [ ] Unit tests: validar que regla inferida es correcta

**Hito 1.3: Validación de Reglas**
- [ ] Implementar `InductorReglas.validate_rule()`
- [ ] Verificar regla contra todos los ejemplos de entrenamiento
- [ ] Feedback: si regla es incorrecta, intentar alternativas
- [ ] Unit tests: casos de éxito/fracaso de validación

---

### FASE 2: Planificador y Búsqueda

**Hito 2.1: Estado Unificado**
- [ ] Definir clase `State` = (pos, key_shape, key_color, key_rotation, energy)
- [ ] Implementar `StateGraph.neighbors()` que respeta restricciones
- [ ] Manejar rotators, teleporters, doors, walls en transiciones
- [ ] Unit tests: verificar que neighbors() es correcta

**Hito 2.2: A* Básico**
- [ ] Implementar A* search sobre StateGraph
- [ ] Heurística simple: Manhattan distance
- [ ] Búsqueda de camino optimal start → door
- [ ] Unit tests: L1 debe encontrar camino en < 50ms

**Hito 2.3: Pattern Database**
- [ ] Precompute costos de transformación key: A → B
- [ ] Integrar en heurística: h = manhattan + DB cost
- [ ] Verificar que heurística sigue siendo admisible
- [ ] Benchmarking: mejoría en velocidad de búsqueda

**Hito 2.4: Manejo de Restricciones**
- [ ] Integrar reglas inferidas en transiciones
- [ ] CSP simple: si regla dice "visit ROT antes DOOR", forbid DOOR antes ROT
- [ ] Unit tests: plan respeta restricciones

---

### FASE 3: Módulos Auxiliares

**Hito 3.1: Renderizador**
- [ ] Convertir plan → grid de salida
- [ ] Marcar camino con color correcto
- [ ] Coincidir exactamente con formato de ejemplos
- [ ] Unit tests: salida visual correcta

**Hito 3.2: Supervisor (Pipeline)**
- [ ] Encadenar Perceptor → Inductor → Planificador → Renderizador
- [ ] Manejo de errores en cada etapa
- [ ] Fallback: si algo falla, intentar estrategia alternativa
- [ ] Unit tests: pipeline L1-L2 completo

**Hito 3.3: Multi-vida**
- [ ] Planificador puede insertar reinicio si energía insuficiente
- [ ] Modelar como transición: (energy=0) → (energy=42, pos=start)
- [ ] Unit tests: problema requiere 2+ vidas

---

### FASE 4: Extensión a L3+

**Hito 4.1: Múltiples Rotators**
- [ ] Inductor: inferir orden de rotators (L3+)
- [ ] CSP: formalizar prerequisitos
- [ ] Planificador: respetar orden
- [ ] Unit tests: L3 resuelto

**Hito 4.2: Teleporters**
- [ ] Perceptor: detectar pares teleporter
- [ ] StateGraph: agregar aristas teleporter
- [ ] Planificador: considerar teleporters en búsqueda
- [ ] Unit tests: L4+ con teleporters

---

### FASE 5: Visibilidad Parcial (L7)

**Hito 5.1: Memory & Exploration**
- [ ] Mantener mapa explorado (30×30 grid)
- [ ] Frontier-based exploration: dirigirse a frontera más cercana
- [ ] Update mapa cuando nuevas celdas se ven
- [ ] Unit tests: explorador llega a fronteras correctas

**Hito 5.2: Replanificación**
- [ ] Detectar cuando plan falló (pared inesperada)
- [ ] Recomputar mapa local
- [ ] Replanificar con información actualizada
- [ ] Unit tests: replanificación en tiempo real

**Hito 5.3: LRTA* Online**
- [ ] Implementar Learning Real-Time A*
- [ ] Buscar localmente cuando stuck
- [ ] Update heurística basado en experiencia
- [ ] Unit tests: L7 exploración + solución

---

### FASE 6: Validación & Optimización

**Hito 6.1: Test Suite Completo**
- [ ] Todos los módulos con ≥ 80% coverage
- [ ] Test cases para cada nivel (L1-L7)
- [ ] Regresión: verificar que fixes no rompan lo anterior

**Hito 6.2: Benchmarking**
- [ ] Tiempo inference + planning por nivel
- [ ] Consumo de memoria
- [ ] Comparación con arc-superagent

**Hito 6.3: Optimizaciones**
- [ ] Profiling: identificar bottlenecks
- [ ] Caché de resultados (memoization)
- [ ] Paralelización donde sea posible

---

## INFRAESTRUCTURA & DESPLIEGUE

### Estructura de Directorios

```
arc-agente02/
├── src/
│   ├── __init__.py
│   ├── perceptor.py         # Módulo 1
│   ├── mapeador.py          # Módulo 2
│   ├── inductor_reglas.py   # Módulo 3
│   ├── planificador.py      # Módulo 4
│   ├── renderizador.py      # Módulo 5
│   ├── supervisor.py        # Módulo 6
│   ├── types.py             # Clases compartidas
│   └── utils.py             # Utilidades
├── tests/
│   ├── __init__.py
│   ├── test_perceptor.py
│   ├── test_mapeador.py
│   ├── test_inductor.py
│   ├── test_planificador.py
│   ├── test_renderizador.py
│   └── test_integration.py  # Tests de pipeline
├── docs/
│   ├── PROYECTO_FUNDACIONAL.md   # Este archivo
│   ├── API.md                     # Especificación de interfaces
│   └── ARCHITECTURAL_DECISIONS.md # ADRs
├── data/
│   ├── examples/             # Ejemplos de entrenamiento (L1-L6)
│   └── pretrained/           # Pattern DBs, modelos pre-entrenados
├── config/
│   ├── config.yaml           # Parámetros globales
│   └── logging.yaml          # Logging config
├── Dockerfile                # Containerización
├── docker-compose.yml        # Desarrollo local
├── requirements.txt          # Dependencias Python
├── pyproject.toml            # Metadata del proyecto
├── .gitignore                # Git
├── README.md                 # Guía de inicio rápido
└── CHANGELOG.md              # Historia de cambios
```

### Dependencias Python

```
numpy>=1.21
scipy>=1.7
networkx>=2.6
pydantic>=1.8
pytest>=6.2
pytest-cov>=2.12
python-dotenv>=0.19
```

### Dockerización

**Buildear:**
```bash
cd ~/Projects/arc-agente02
docker-compose build
```

**Ejecutar:**
```bash
docker-compose run arc-agente02 bash
```

**Dentro del container:**
```bash
cd /workspace
python -m pytest tests/
python -c "from src.supervisor import Supervisor; ..."
```

---

## VALIDACIÓN & TESTING

### Testing Strategy

**Unit Tests (módulos individuales)**
- Perceptor: ¿Parsing correcto?
- Inductor: ¿Regla inferida correcta?
- Planificador: ¿Plan óptimo?
- Renderizador: ¿Formato correcto?

**Integration Tests (pipeline)**
- L1 completo: ejemplo → regla → plan → salida
- L2 completo: igual, con rotators
- L3+: múltiples niveles

**Validación contra Golden Set**
- Comparar salida con ejemplos esperados
- Pixel-perfect match (si es necesario)

### Métricas de Éxito

| Métrica | Criterio |
|---------|----------|
| **Reglas Inferidas** | ≥ 4/7 niveles regla correcta |
| **Planos Óptimos** | ≥ 5/7 niveles solución óptima |
| **Rendimiento** | < 60s total por nivel |
| **Cobertura Code** | ≥ 80% tests |

---

## ANEXO: EJEMPLO CONCRETO (L1)

### Entrada
```
- Grid 30×30 con start en (5,5), door en (25,10)
- Paredes en posiciones varias
- Key inicial: (shape=square, color=red, rot=0)
- Door requisito: (shape=square, color=red, rot=0)
```

### Pipeline L1

**1. Perceptor** → Identifica start, door, walls
```
WorldState(
    player_pos=(5,5),
    walls={...},
    doors=[Door(pos=(25,10), required=(0,0,0))],
    ...
)
```

**2. Mapeador** → Construye StateGraph
```
StateGraph con nodos:
- (5,5,0,0,0,42) - start
- (5,6,0,0,0,41) - 1 paso east
- (5,7,0,0,0,40) - 2 pasos
- ... 
- (25,10,0,0,0,X) - door con energía restante
```

**3. Inductor** → Infiere regla
```
Análisis de ejemplos:
- Todos van directamente del start a la door
- No hay rotators visitados
- Regla: "shortest_path_to_door"
```

**4. Planificador** → A* search
```
A*(start=(5,5,0,0,0,42), goal=(25,10,0,0,0,≥0), rule="shortest_path")
→ Encuentra camino de 25 pasos (óptimo)
→ Plan = [(5,5)→(5,6)→(5,7)→...→(25,10)]
```

**5. Renderizador** → Output
```
Copia grid original
Marca cada celda del plan con rojo
Retorna grid con camino dibujado
```

**6. Supervisor** → Valida y retorna
```
Verifica que plan satisface regla (✓)
Verifica que salida coincide con ejemplo (✓)
Retorna solución final
```

---

## PRÓXIMOS PASOS

1. **Aprobación de este documento** por el usuario
2. **Creación de estructura de archivos** (ya iniciado)
3. **Implementación Fase 1** (Perceptor + Inductor)
4. **Iteración y refinamiento** basado en testing

---

**Documento Preparado:** 2026-06-05  
**Estado:** Pendiente Aprobación  
**Responsable:** Claude (arquitectura), Carlos (revisión)
