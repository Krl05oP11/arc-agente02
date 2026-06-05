# 🎮 Visual Simulator Guide

**Watch your agent solve ARC puzzles VISUALLY in real-time**

---

## ✨ What's New

A **fresh, lightweight visual simulator** built specifically for ARC-AGENTE02:

- ✅ Runs on **localhost:5555**
- ✅ **Real-time rendering** of game grid (512x512px)
- ✅ **Game state display** (level, steps, status)
- ✅ **Action history** logging
- ✅ **Keyboard controls** for manual play or auto-play
- ✅ **Zero dependencies** (just Flask)
- ✅ **Ready for integration** with agent

---

## 🚀 Quick Start

### 1. Start the Simulator

```bash
cd ~/Projects/arc-agente02
source .venv/bin/activate
python3 simulator.py
```

You should see:

```
============================================================
  🎮 ARC-AGENTE02 Visual Simulator
  Open http://localhost:5555 in your browser
============================================================
```

### 2. Open Browser

Visit: **http://localhost:5555**

You'll see:
- 512x512px game grid on the left
- Control panel on the right with game stats
- Action history at the bottom

### 3. Play!

**Keyboard Controls:**
- `Space` — Agent takes one step
- `R` — Reset game
- `Tab` — Toggle auto-play
- Slider — Adjust auto-play speed

---

## 🎯 Current Status

### What Works NOW ✅

- [x] Web interface rendering
- [x] Canvas grid display  
- [x] Game state tracking
- [x] Action history
- [x] Keyboard controls
- [x] Auto-play with speed control
- [x] Reset functionality

### What Comes Next (Integration) ⏳

```
Phase 1: Connect to ARC-AGENTE02 Agent (2-3 hours)
├── Import supervisor module
├── Get real game grid from ARC Prize
├── Execute agent pipeline (infer → plan → render)
└── Display results visually

Phase 2: Full ARC Prize Integration (4-6 hours)
├── Load actual ARC Prize environments
├── Map agent actions to game actions
├── Show live game progression
├── Display metrics (steps, success rate)
└── Support all game levels (L1-L7)
```

---

## 📋 API Endpoints

If you want to build against the simulator programmatically:

### GET `/api/frame`

Get current game state and rendered frame:

```json
{
  "image": "base64-encoded-png",
  "level": 1,
  "steps": 25,
  "status": "Playing",
  "history": ["[1] Move UP", "[2] Move LEFT", ...],
  "error": null
}
```

### POST `/api/step`

Execute one game step:

```bash
curl -X POST http://localhost:5555/api/step
```

### POST `/api/reset`

Reset the game:

```bash
curl -X POST http://localhost:5555/api/reset
```

---

## 🔧 Code Structure

```python
simulator.py:
├── Flask app setup
├── game_state = {
│   ├── frame: current game frame
│   ├── game_grid: 64x64 grid array
│   ├── current_level: level number
│   ├── step_count: total steps taken
│   ├── status: game status string
│   └── history: list of actions
├── render_grid(): Convert grid to PNG
├── /api/frame: Get game state
├── /api/step: Execute step
├── /api/reset: Reset game
└── HTML UI: Interactive web interface
```

---

## 🎨 Color Mapping

The grid colors are:

| Value | Color | Meaning |
|-------|-------|---------|
| 0 | White | Empty space |
| 1 | Off-white | - |
| 2 | Light grey | - |
| 3 | Grey | Floor (passable) |
| 4 | Dark grey | Wall (obstacle) |
| 5 | Black | Door |
| 6-7 | Magenta | Shape (object) |
| 8 | Red | - |
| 9-10 | Blue | - |
| 11 | Yellow | - |
| 12 | Orange | **Player** |
| 13 | Maroon | - |
| 14 | Green | - |
| 15 | Purple | - |

---

## 💡 Integration Checklist

When ready to integrate with ARC-AGENTE02:

- [ ] Import `Arcade` from `arc_agi`
- [ ] Import `Supervisor` from `src.supervisor`
- [ ] Modify `/api/step` to:
  1. Get frame from environment
  2. Call supervisor.run()
  3. Get action from plan
  4. Execute action in environment
  5. Update game_grid
- [ ] Replace test grid with real game grid
- [ ] Add support for level changes
- [ ] Test with actual ARC Prize environments
- [ ] Display agent recommendations

---

## 📝 Example Integration Code (Future)

```python
from arc_agi import Arcade
from src.supervisor import create_supervisor

# Initialize
supervisor = create_supervisor(debug=False)
arcade = Arcade(environments_dir="~/arc_env_files/ls20")
env = arcade.make("ls20")

@app.route("/api/step", methods=["POST"])
def api_step():
    global game_state
    
    with lock:
        # Get current frame
        frame = game_state["frame"]
        grid = frame.frame[0]  # ARC Prize format
        
        # Convert to ARC-AGENTE02 format
        arc_agente_grid = convert_grid(grid)
        
        # Run agent pipeline
        result = supervisor.run([example], arc_agente_grid)
        
        # Execute action
        if result.plan:
            action = result.plan.actions[0]
            game_state["frame"] = env.step(action)
            game_state["step_count"] += 1
            game_state["game_grid"] = game_state["frame"].frame[0]
        
        return jsonify({"ok": True})
```

---

## 🐛 Troubleshooting

### "Port 5555 already in use"

```bash
# Kill existing process
kill $(lsof -t -i:5555)

# Or use a different port
# Edit simulator.py, change port 5555 to something else
```

### Grid not rendering

Check that `game_state["game_grid"]` is a numpy array:

```python
import numpy as np
game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
```

### Controls not working

Make sure you're focused on the page (not in address bar):
- Click on the canvas
- Try keyboard controls again

---

## 🎯 Next Steps

1. **Test the simulator** (right now!)
   ```bash
   python3 simulator.py
   # Open http://localhost:5555
   ```

2. **Read the integration code** (when ready to connect agent)
   - Check the "Integration Checklist" section
   - Look at "Example Integration Code"

3. **Integrate step by step**
   - Start with simple grid conversion
   - Then add supervisor calls
   - Finally, add game logic

4. **Debug visually**
   - Watch pathfinding work in real-time
   - See where agent gets stuck
   - Identify rotator/door logic issues

---

## 📊 Metrics You'll See

Once integrated with ARC-AGENTE02, you'll track:

```
Level:          Current game level (L1-L7)
Steps:          Total steps taken
Status:         Current action or result
History:        Log of recent actions
├── [0] Game Reset
├── [1] Move UP
├── [2] Move LEFT
├── [3] Interact (Rotator)
├── [4] Move DOWN
└── ...
```

---

## 🏆 What This Enables

With the visual simulator, you can:

✅ **Debug** agent behavior step-by-step  
✅ **Visualize** pathfinding and planning  
✅ **Identify** stuck/looping patterns  
✅ **Test** different strategies  
✅ **Validate** game mechanics  
✅ **Demonstrate** agent capabilities  
✅ **Analyze** performance  

---

## 📝 Summary

You now have a **fresh, lightweight, working visual simulator** that:

- Runs locally with minimal dependencies
- Provides a clean web interface
- Is ready for agent integration
- Enables visual debugging

**Next:** Integrate with your ARC-AGENTE02 supervisor to watch it solve puzzles in real-time! 🚀

---

**Created:** 2026-06-05  
**Status:** Ready for Integration  
**Purpose:** Visual Testing & Debugging
