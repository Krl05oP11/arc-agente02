# 🔍 Agent Validation Guide

**ANTES de enviar a GitHub o Kaggle, valida la performance de tu agente localmente**

---

## 📋 Overview

Se ha creado un **Test Bench completo** para validar ARC-AGENTE02 contra problemas reales de ARC antes de hacer submit.

### ¿Por qué?

❌ **Enviar sin validar:** Riesgo de fallar públicamente  
✅ **Validar primero:** Confianza en que funciona

---

## 🎯 Componentes

### 1. **arc_test_bench.py** (Problemas de test)
```python
ARCTestBench:
  - Carga 5-10 problemas ARC reales
  - Categoriza por dificultad (EASY, MEDIUM, HARD)
  - Ejecuta tests contra el agente
  - Genera reportes de performance
```

### 2. **agent_validator.py** (Validador)
```python
AgentValidator:
  - Analiza resultados
  - Genera reporte completo
  - Da recomendación de envío
  
RealAgentWrapper:
  - Conecta con ARC-AGENTE02 real
  - Ejecuta pipeline completo
```

---

## 🚀 Uso Rápido

### Opción 1: Script Simple
```bash
cd ~/Projects/arc-agente02
source .venv/bin/activate

python3 << 'EOF'
from src.arc_test_bench import run_quick_validation
run_quick_validation()
EOF
```

### Opción 2: Test Completo
```python
from src.arc_test_bench import ARCTestBench
from src.agent_validator import AgentValidator, RealAgentWrapper

# Crear bench
bench = ARCTestBench(num_problems=10, debug=True)

# Crear wrapper del agente real
agent = RealAgentWrapper()

# Ejecutar tests
results = bench.run_suite(agent.predict)

# Validar
validator = AgentValidator(agent_name="ARC-AGENTE02")
analysis = bench.get_analysis()
print(validator.generate_validation_report(analysis))
```

---

## 📊 Interpretación de Resultados

### Success Rate Interpretation

| Rate | Status | Action |
|------|--------|--------|
| **≥80%** | ✅ Ready | Proceed to submission |
| **60-79%** | ⚠️ Cautious | Fix issues, then submit |
| **40-59%** | 🟡 Conditional | Major improvements needed |
| **<40%** | ❌ Not Ready | Significant rework required |

### Report Example

```
======================================================================
✅ AGENT VALIDATION REPORT - ARC-AGENTE02
======================================================================

📊 PERFORMANCE METRICS
----------------------------------------------------------------------
Total Tests:            10
Passed:                 8
Failed:                 2
Success Rate:           80.0%
Avg Time per Test:      0.50s

📈 BY DIFFICULTY
----------------------------------------------------------------------
EASY:                   5/5 (100%)
MEDIUM:                 2/3 (67%)
HARD:                   1/2 (50%)

======================================================================
✅ READY FOR SUBMISSION
   • Performance exceeds baseline expectations
   • Confidence level: HIGH
   • Recommended action: PROCEED TO GITHUB/KAGGLE
======================================================================
```

---

## 🔧 Agregar Problemas Reales

### Opción A: Dataset ARC Público

```python
# Descargar dataset oficial
# https://github.com/fchollet/ARC

# Cargar en test bench
from src.arc_test_bench import ARCTestBench

# Subclasificar para cargar datos reales
class RealARCTestBench(ARCTestBench):
    def _load_problems(self):
        # Cargar desde json de dataset ARC
        pass
```

### Opción B: Problemas Sintéticos Actuales

Los 5 problemas incluidos:
- Simple Path (encontrar camino)
- Color Mapping (mapeo de colores)
- Rotation (rotación)
- Symmetry (simetría)
- Counting (conteo)

---

## 📈 Workflow Recomendado

```
┌─────────────────────────────────────────┐
│ 1. RUN VALIDATION TESTS                 │
│    python agent_validator.py            │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Success Rate?    │
        └────┬───────┬────┘
            │       │
       ≥80% │       │ <80%
            │       │
         ✅ │       │ ❌
            ▼       ▼
        SUBMIT   IMPROVE
            │       │
            │       └──────────┐
            │                  │
            ▼                  ▼
        ┌──────────────────────────────┐
        │ 2. PUSH TO GITHUB            │
        │    git push origin main      │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ 3. JOIN KAGGLE               │
        │    Create Notebook           │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ 4. SUBMIT & MONITOR          │
        │    Watch Performance         │
        └──────────────────────────────┘
```

---

## 💡 FAQ

### ¿Estos problemas representan ARC Prize?
Parcialmente. Son **problemas sintéticos controlados** que:
- ✅ Prueban conceptos básicos (simetría, rotación, mapeo)
- ✅ Son más fáciles que problemas reales de ARC
- ✅ Sirven como sanity check
- ❌ No cubren toda la complejidad de ARC Prize

Para cobertura completa, necesitarías dataset oficial de ARC.

### ¿Qué si fallo los tests sintéticos?
Significaría que hay **problemas graves** en:
- Inferencia de reglas
- Planificación
- Ejecución del pipeline

Necesitarías debugging antes de cualquier submit.

### ¿Tiempo típico de validación?
- 5 problemas EASY: < 1 segundo
- 10 problemas mixtos: 1-5 segundos
- 50 problemas reales: 10-30 segundos

---

## 🎯 Próximos Pasos

### Ahora (Antes de GitHub)
```bash
# 1. Ejecutar validación
python3 src/agent_validator.py

# 2. Revisar reporte
# 3. Decidir si proceder
```

### Después (Si SUCCESS RATE ≥ 80%)
```bash
# 1. Push a GitHub
./push_to_github.sh

# 2. Join Kaggle
# https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3

# 3. Create Notebook
# https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/code
```

### Fase 7: Problemas Reales
Una vez que funciona con problemas sintéticos:
1. Descargar dataset oficial de ARC
2. Crear `RealARCTestBench`
3. Validar contra problemas reales
4. Ajustar si es necesario

---

## 📝 Resumen

**¡NO ENVÍES A CIEGAS!**

1. ✅ Run validation tests locally
2. ✅ Check success rate (target: ≥80%)
3. ✅ Read recommendation report
4. ✅ Then push to GitHub
5. ✅ Then submit to Kaggle

**The test bench gives you confidence before public submission.**

---

**Creado:** 2026-06-05  
**Estado:** Ready for use  
**Próximo paso:** Ejecutar validación antes de envío
