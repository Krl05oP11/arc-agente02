#!/usr/bin/env python3
"""
ARC-AGENTE02 Visual Simulator
Simple Flask web interface to watch the agent solve puzzles visually

Run: python3 simulator.py
Then open http://localhost:5555 in your browser
"""

import json
import base64
import io
import sys
from flask import Flask, render_template_string, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import threading

# Try to import ARC Prize toolkit
try:
    from arc_agi import Arcade
    HAS_ARC = True
except ImportError:
    HAS_ARC = False
    print("⚠️  arc-agi not installed. Baseline mode only.")

# Try to import ARC-AGENTE02
try:
    from src.supervisor import create_supervisor
    from src.types import Example, WorldState, Door, KeyState
    from src.arc_integration_bridge import ArcIntegrationBridge
    from src.arc_grid_adapter import GridAdapter
    from src.arc_plan_executor import PlanExecutor
    HAS_AGENT = True
    supervisor = create_supervisor(debug=False)
    bridge = ArcIntegrationBridge(debug=False)
except Exception as e:
    HAS_AGENT = False
    supervisor = None
    bridge = None
    print(f"⚠️  Agent not available: {e}")

app = Flask(__name__)

# Initialize ARC Prize environment (async to avoid blocking server)
arcade = None
current_env = None

def init_arc_async():
    global arcade, current_env
    if not HAS_ARC:
        return
    try:
        arcade = Arcade(environments_dir="~/arc_env_files/ls20")
        current_env = arcade.make("ls20")
        print("✅ ARC Prize environment loaded (ls20)")
    except Exception as e:
        print(f"⚠️  ARC environment failed: {e}")

# Start async load immediately
arc_loader = threading.Thread(target=init_arc_async, daemon=True)
arc_loader.start()

# Global state
lock = threading.Lock()
game_state = {
    "frame": None,
    "env": current_env,
    "current_level": 1,
    "step_count": 0,
    "game_grid": None,
    "history": [],
    "using_agent": False,
    "agent_ready": HAS_AGENT,
    "arc_ready": HAS_ARC and current_env is not None,
}

# Color map (value → RGB)
COLOR_MAP = {
    0: (255, 255, 255),    # White
    1: (204, 204, 204),    # Off-white
    2: (153, 153, 153),    # Light grey
    3: (102, 102, 102),    # Grey (floor)
    4: (51, 51, 51),       # Dark grey (wall)
    5: (0, 0, 0),          # Black
    6: (229, 58, 163),     # Magenta
    7: (255, 123, 204),    # Magenta light
    8: (249, 60, 49),      # Red
    9: (30, 147, 255),     # Blue
    10: (136, 216, 241),   # Blue light
    11: (255, 220, 0),     # Yellow
    12: (255, 133, 27),    # Orange (player)
    13: (146, 18, 49),     # Maroon
    14: (79, 204, 48),     # Green
    15: (163, 86, 214),    # Purple
}

SCALE = 8  # Pixels per grid cell

HTML = r"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>🎮 ARC-AGENTE02 Visual Simulator</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #1a1a2e;
      color: #e0e0e0;
      font-family: 'Courier New', monospace;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }
    h1 { color: #00d4ff; margin: 20px 0; font-size: 1.8em; }
    .container { display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap; }
    #game-canvas { border: 3px solid #00d4ff; image-rendering: pixelated; width: 512px; height: 512px; }
    .panel {
      background: #16213e;
      border: 1px solid #0f3460;
      border-radius: 8px;
      padding: 15px;
      width: 300px;
    }
    .stat-row { display: flex; justify-content: space-between; margin: 8px 0; font-size: 0.9em; }
    .stat-val { color: #ffd700; font-weight: bold; }
    .btn {
      background: #0f3460;
      border: 1px solid #00d4ff;
      color: #e0e0e0;
      padding: 8px 12px;
      border-radius: 4px;
      cursor: pointer;
      margin: 4px;
      font-family: inherit;
    }
    .btn:hover { background: #1a6090; }
    .btn.primary { border-color: #44ff44; color: #44ff44; }
    .controls { margin: 15px 0; }
    #history { height: 400px; overflow-y: auto; background: #0a0a1a; border-radius: 4px; padding: 10px; font-size: 0.8em; }
    .hist-item { padding: 3px 0; border-bottom: 1px solid #111; }
    .error { color: #ff4444; }
    .success { color: #44ff44; }
  </style>
</head>
<body>
  <h1>🎮 ARC-AGENTE02 — Visual Simulator</h1>

  <div class="container">
    <div>
      <canvas id="game-canvas" width="512" height="512"></canvas>
    </div>

    <div class="panel">
      <h2 style="color: #00d4ff; margin-bottom: 15px;">Game Status</h2>

      <div class="stat-row">
        <span>Level:</span>
        <span class="stat-val" id="level">—</span>
      </div>
      <div class="stat-row">
        <span>Steps:</span>
        <span class="stat-val" id="steps">—</span>
      </div>
      <div class="stat-row">
        <span>Status:</span>
        <span class="stat-val" id="status">Initializing...</span>
      </div>

      <div class="controls">
        <button class="btn" onclick="reset()">🔄 Reset</button>
        <button class="btn primary" onclick="step()">▶ Agent Step</button>
        <button class="btn" id="auto-btn" onclick="toggleAuto()">Auto</button>
      </div>

      <div style="margin-top: 15px;">
        <label>Speed: <input type="range" id="speed" min="1" max="10" value="5" style="width: 80%;"></label>
      </div>

      <h3 style="color: #00d4ff; margin: 20px 0 10px 0;">Action History</h3>
      <div id="history"></div>
    </div>
  </div>

<script>
let autoPlay = false;
let gameRunning = true;

async function updateFrame() {
  try {
    const r = await fetch('/api/frame');
    const data = await r.json();

    if (data.error) {
      document.getElementById('status').innerHTML = '<span class="error">' + data.error + '</span>';
      return;
    }

    // Draw canvas
    const canvas = document.getElementById('game-canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => ctx.drawImage(img, 0, 0);
    img.src = 'data:image/png;base64,' + data.image;

    // Update stats
    document.getElementById('level').textContent = data.level || '—';
    document.getElementById('steps').textContent = data.steps || '—';
    document.getElementById('status').textContent = data.status || '—';

    // Update history
    if (data.history && data.history.length) {
      const hist = document.getElementById('history');
      hist.innerHTML = data.history
        .slice(-20)
        .map(h => '<div class="hist-item">' + h + '</div>')
        .join('');
      hist.scrollTop = hist.scrollHeight;
    }
  } catch (e) {
    console.error('Frame update error:', e);
  }
}

async function step() {
  await fetch('/api/step', { method: 'POST' });
  await updateFrame();
}

async function reset() {
  await fetch('/api/reset', { method: 'POST' });
  await updateFrame();
}

function toggleAuto() {
  autoPlay = !autoPlay;
  const btn = document.getElementById('auto-btn');
  btn.classList.toggle('primary');
  btn.textContent = autoPlay ? '⏸ Stop' : 'Auto';
  if (autoPlay) autoLoop();
}

async function autoLoop() {
  if (!autoPlay) return;
  await step();
  const speed = parseInt(document.getElementById('speed').value);
  const ms = 1000 / speed;
  setTimeout(autoLoop, ms);
}

// Keyboard controls
document.addEventListener('keydown', e => {
  if (e.key === ' ') { e.preventDefault(); step(); }
  if (e.key === 'r' || e.key === 'R') { e.preventDefault(); reset(); }
  if (e.key === 'Tab') { e.preventDefault(); toggleAuto(); }
});

// Initial load
updateFrame();
setInterval(updateFrame, 500);
</script>
</body>
</html>
"""

def render_grid(grid_array):
    """Render grid as PNG base64"""
    if grid_array is None:
        # Return blank image
        img = Image.new("RGB", (512, 512), color=(50, 50, 50))
    else:
        H, W = len(grid_array), len(grid_array[0])
        img = Image.new("RGB", (W * SCALE, H * SCALE))
        pixels = img.load()

        for r in range(H):
            for c in range(W):
                try:
                    val = int(grid_array[r][c])
                    rgb = COLOR_MAP.get(val, (0, 0, 0))
                except:
                    rgb = (100, 100, 100)

                for dy in range(SCALE):
                    for dx in range(SCALE):
                        pixels[c * SCALE + dx, r * SCALE + dy] = rgb

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/frame")
def api_frame():
    with lock:
        img_b64 = render_grid(game_state.get("game_grid"))

        return jsonify({
            "image": img_b64,
            "level": game_state.get("current_level", 1),
            "steps": game_state.get("step_count", 0),
            "status": game_state.get("status", "Ready"),
            "history": game_state.get("history", []),
            "error": None,
        })


@app.route("/api/step", methods=["POST"])
def api_step():
    with lock:
        if game_state.get("game_grid") is None:
            # Initialize from ARC Prize or test grid
            if game_state.get("arc_ready") and game_state["env"]:
                try:
                    frame = game_state["env"].reset()
                    if frame and hasattr(frame, 'frame'):
                        game_state["game_grid"] = np.array(frame.frame[0], dtype=np.int8)
                except:
                    game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
            else:
                game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
            game_state["using_agent"] = HAS_AGENT
        else:
            # Execute agent step
            try:
                if HAS_AGENT and supervisor:
                    # Get current grid
                    grid = game_state["game_grid"]

                    # Get player position from grid (color 12 = orange)
                    player_positions = np.where(grid == 12)
                    if len(player_positions[0]) > 0:
                        player_row = int(np.mean(player_positions[0]))
                        player_col = int(np.mean(player_positions[1]))
                    else:
                        player_row, player_col = 32, 32

                    # Get objectives from grid
                    doors = list(GridAdapter.get_doors(grid))

                    # If no doors, try to find unreachable areas
                    if not doors:
                        # Find first non-wall cell that's not player
                        for r in range(64):
                            for c in range(64):
                                if grid[r, c] not in [4, 5, 12] and (r, c) != (player_row, player_col):
                                    doors = [(r, c)]
                                    break
                            if doors:
                                break

                    # Create solution path targeting first door
                    solution_path = [(player_row, player_col)]
                    if doors:
                        solution_path.append(doors[0])

                    # Create example for supervisor
                    world = WorldState(
                        player_pos=(player_row, player_col),
                        walls=GridAdapter.get_walls(grid),
                        doors=[],  # Don't report doors as obstacles
                        rotators=[],
                        refills=[],
                        teleporters=[],
                        key_state=KeyState(0, 0, 0),
                        energy=42
                    )

                    example = Example(
                        input_grid=grid,
                        solution_path=solution_path,
                        world_state=world
                    )

                    # Try supervisor first
                    result = supervisor.run([example], grid, test_world=world)

                    if result.success and result.plan:
                        action_str = f"Plan: {len(result.plan.actions)} steps"
                        game_state["history"].append(f"[{game_state['step_count']}] ✅ {action_str}")
                        game_state["status"] = f"Plan generated: {len(result.plan.actions)} steps"
                    else:
                        # Fallback: Simple exploration towards nearest door
                        if doors:
                            target = doors[0]
                        else:
                            # If no doors, move towards center
                            target = (32, 32)

                        # Calculate direction
                        dr = target[0] - player_row
                        dc = target[1] - player_col

                        # Determine movement
                        action = None
                        new_row, new_col = player_row, player_col

                        if abs(dr) > abs(dc):
                            action = "Down" if dr > 0 else "Up"
                            new_row = player_row + (1 if dr > 0 else -1)
                        else:
                            action = "Right" if dc > 0 else "Left"
                            new_col = player_col + (1 if dc > 0 else -1)

                        # Check if new position is valid (not a wall)
                        if 0 <= new_row < 64 and 0 <= new_col < 64:
                            if grid[new_row, new_col] not in [4, 5]:  # Not a wall
                                # Move player in grid
                                grid[player_row, player_col] = 3  # Replace player with floor
                                grid[new_row, new_col] = 12  # Place player at new position
                                game_state["game_grid"] = grid

                                game_state["history"].append(f"[{game_state['step_count']}] ✅ {action} ({new_row},{new_col})")
                                game_state["status"] = f"Moved {action}"
                            else:
                                # Hit a wall, try different direction
                                game_state["history"].append(f"[{game_state['step_count']}] 🧱 Wall! Cannot {action}")
                                game_state["status"] = "Blocked by wall"
                        else:
                            game_state["history"].append(f"[{game_state['step_count']}] ⚠️ Out of bounds")
                            game_state["status"] = "Out of bounds"
                else:
                    # No agent available
                    game_state["history"].append(f"[{game_state['step_count']}] ℹ️ Agent not available")
                    game_state["status"] = "Agent not available"

                game_state["step_count"] += 1

            except Exception as e:
                game_state["history"].append(f"[{game_state['step_count']}] ❌ Error: {str(e)[:40]}")
                game_state["step_count"] += 1
                game_state["status"] = f"Error: {str(e)[:30]}"

        return jsonify({"ok": True})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    with lock:
        game_state["step_count"] = 0
        game_state["history"] = ["[0] Game Reset"]

        # Load real ARC Prize environment
        if game_state.get("arc_ready") and game_state["env"]:
            try:
                frame = game_state["env"].reset()
                if frame and hasattr(frame, 'frame'):
                    game_state["game_grid"] = np.array(frame.frame[0], dtype=np.int8)
                    game_state["status"] = "Real ARC Prize Level Loaded"
                    game_state["history"].append("[0] ✅ ARC Prize level loaded")
                else:
                    # Fallback to test grid
                    game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
                    game_state["status"] = "Ready (Test Mode)"
            except Exception as e:
                game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
                game_state["status"] = f"Error: {str(e)[:30]}"
                game_state["history"].append(f"[0] ❌ {str(e)[:40]}")
        else:
            # No ARC available - use test grid
            game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
            game_state["status"] = "Ready (Test Mode - arc-agi not available)"

        game_state["current_level"] = 1

        return jsonify({"ok": True})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🎮 ARC-AGENTE02 Visual Simulator")
    print("  Open http://localhost:5555 in your browser")
    print("=" * 60 + "\n")
    print("  ⏳ Loading ARC Prize environment...")

    # Initialize with test grid (will update when ARC loads)
    with lock:
        game_state["game_grid"] = np.zeros((64, 64), dtype=np.int8)
        game_state["status"] = "Loading ARC Prize..."
        game_state["history"] = ["Simulator started, loading environment..."]

    # Wait briefly for ARC to load (max 5 seconds)
    for attempt in range(50):
        if current_env is not None:
            try:
                frame = current_env.reset()
                if frame and hasattr(frame, 'frame'):
                    with lock:
                        game_state["env"] = current_env
                        game_state["game_grid"] = np.array(frame.frame[0], dtype=np.int8)
                        game_state["status"] = "Ready - Real ARC Prize Level"
                        game_state["history"] = ["✅ ARC Prize level loaded"]
                        game_state["arc_ready"] = True
                    print("✅ Loaded real ARC Prize level!")
                    break
            except Exception as e:
                pass
        threading.Event().wait(0.1)  # Wait 100ms

    if game_state["env"] is None:
        print("⚠️  ARC Prize not loaded, using test mode")

    print("🚀 Server starting on http://localhost:5555\n")
    app.run(host="127.0.0.1", port=5555, debug=False, threaded=True)
