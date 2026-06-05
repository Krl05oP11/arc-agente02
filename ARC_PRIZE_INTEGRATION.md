# ARC Prize Integration Guide

## 🎯 Overview

**ARC-AGENTE02** puede ser testeado en benchmarks públicos del **ARC Prize 2026** usando el toolkit oficial de ARC Prize.

**Sitio oficial:** https://arcprize.org/arc-agi/3

---

## 📋 Requisitos

### 1. ARC Prize Toolkit
```bash
# Opción A: Con uv (recomendado)
uv add arc-agi

# Opción B: Con pip
pip install arc-agi
```

### 2. API Key (Opcional pero recomendado)
```bash
# Registrarse en: https://arcprize.org/sign-up
# Luego configurar:
export ARC_API_KEY="tu-api-key-aqui"
```

### 3. Python >= 3.12
```bash
python3 --version  # Verificar versión
```

---

## 🚀 Instalación Rápida

```bash
# 1. Actualizar proyecto
cd ~/Projects/arc-agente02
source .venv/bin/activate

# 2. Instalar toolkit de ARC Prize
pip install arc-agi

# 3. Verificar instalación
python3 -c "import arc_agi; print('✓ arc-agi instalado')"
```

---

## 💻 Uso Básico

### Test de Conexión

```python
from src.arc_prize_adapter import test_connection

# Verificar conexión al benchmark
test_connection(game_name="ls20", level_idx=0)
```

### Ejecutar Agente en Benchmark

```python
from src.arc_prize_adapter import ArcPrizeAgent

# Crear agente
agent = ArcPrizeAgent(
    game_name="ls20",
    level_idx=0,
    debug=True
)

# Ejecutar con estrategia aleatoria (demo)
result = agent.run(max_steps=100, strategy="random")

# Ver resultados
print(f"Status: {result['status']}")
print(f"Pasos: {result['steps']}")
print(f"Scorecard: {result['scorecard']}")
```

### Resumen de Ejecución

```python
# Ver qué acciones se ejecutaron
summary = agent.get_summary()
print(f"Acciones: {summary['actions']}")
print(f"Estado final: {summary['final_status']}")
```

---

## 🎮 Juegos Disponibles

Según la documentación de ARC Prize:

| Juego | Descripción | Niveles |
|-------|-------------|---------|
| `ls20` | Level Selection (demostración) | 0-2 |
| `arc-agi-3` | Benchmark oficial | Variable |
| Otros | Más juegos en desarrollo | - |

---

## 📊 Formatos de Acción

### Acciones Básicas

```python
# Acciones disponibles:
ACTION1 through ACTION12

# Ejemplo:
env.step(GameAction.ACTION1)
```

### Acciones con Parámetros

```python
from arcengine import GameAction

# Acción con coordenadas
env.step(
    GameAction.ACTION6,
    data={"x": 32, "y": 32},
    reasoning={"thought": "Mover a posición (32,32)"}
)
```

---

## 🔄 Integración Completa

### Próximas Fases

Para máximo rendimiento, podríamos:

1. **Fase 7A: Adaptador Inteligente**
   - Traducir planes de ARC-AGENTE02 a acciones de ARC Prize
   - Usar estrategia optimal vs random

2. **Fase 7B: Benchmark Loop**
   - Ejecutar contra múltiples niveles
   - Recopilar resultados
   - Medir performance

3. **Fase 7C: Optimización**
   - Ajustar parámetros según resultados
   - Mejorar estrategia de exploración

---

## 📈 Ejemplo Completo

```python
from src.arc_prize_adapter import ArcPrizeAgent

# Configurar agente
agent = ArcPrizeAgent(
    game_name="ls20",
    level_idx=0,
    debug=True
)

# Ejecutar benchmark
result = agent.run(max_steps=500, strategy="sequential")

# Analizar resultados
print(f"\n📊 RESULTADOS")
print(f"   Juego: {result['game']}")
print(f"   Nivel: {result['level']}")
print(f"   Pasos: {result['steps']}")
print(f"   Estado: {result['status']}")

if result['scorecard']:
    print(f"\n🏆 SCORECARD")
    for key, value in result['scorecard'].items():
        print(f"   {key}: {value}")
```

---

## ⚠️ Limitaciones Actuales

### 1. Adaptador Básico
- ✅ Conexión al toolkit
- ✅ Ejecución de acciones
- ⏳ Integración inteligente (próxima fase)

### 2. Estrategias Disponibles
- ✅ Random: Acciones aleatorias
- ✅ Sequential: Acciones en secuencia
- ⏳ Learned: Usando planes de ARC-AGENTE02

### 3. Acciones Soportadas
- ✅ ACTION1-ACTION12 básicas
- ⏳ Acciones con parámetros (futuro)

---

## 🔗 Referencias

### Sitio Oficial
- **ARC Prize:** https://arcprize.org/arc-agi/3
- **Toolkit:** https://docs.arcprize.org
- **GitHub:** https://github.com/arcprize/arc-agi

### Información Útil
- **PyPI:** https://pypi.org/project/arc-agi/
- **Kaggle Competition:** https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/
- **Prize Pool:** $850,000 (Grand Prize: $700,000)

---

## 📝 Notas

### API Key
- Opcional para acceso anónimo
- Recomendado para acceso a más juegos
- Se obtiene en: https://arcprize.org/sign-up

### Versión de arc-agi
- Última: 0.9.8 (abril 2026)
- Compatible con Python >= 3.12
- Licencia: MIT

### Próximos Pasos
1. Instalar toolkit: `pip install arc-agi`
2. Obtener API key (opcional)
3. Ejecutar test de conexión
4. Integrar con ARC-AGENTE02

---

## 🎯 Conclusión

ARC-AGENTE02 es compatible con el benchmark oficial de ARC Prize 2026.

**Estado:** Sistema listo para testear  
**Próxima fase:** Integración inteligente de planes

¡Podemos participar en el ARC Prize 2026! 🏆
