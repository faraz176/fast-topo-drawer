# fast-topo-drawer

## Quick way to draw your topology!

A lightweight, keyboard-driven tool for **rapid network topology sketching**.  
Built for engineers who want to map ideas fast without opening Visio, draw.io, or EVE-NG.

---

## Features

- **Router nodes** (circles) and **Switch nodes** (squares)
- **Fast node placement** (keyboard + click)
- **Chain linking**: click a node to “sprout” a link, then keep clicking nodes to build a path
- **Live link preview** while connecting
- **Drag nodes** and the **links stretch with them**
- **Box-select** sections of the topology, then **drag to move the whole selection**
- **Delete nodes or links** (select → `D`)
- **Pan and zoom** for large topologies
- Built-in legend
- Instant launch on Windows (Win + R)

---

## Controls

### Placement
| Key | Action |
|---|---|
| `R` | Router placement mode (click to place) |
| `S` | Switch placement mode (click to place) |

### Neutral / Editing
| Key / Mouse | Action |
|---|---|
| `ESC` | Neutral mode + clears highlights/selection (your “free pan/zoom mode”) |
| Click node | Select node + start a “sprouting” link |
| Click another node | Create a link and keep chaining from the last node |
| Drag node | Move node (links stretch) |
| Click + drag empty space (in neutral) | Box-select nodes |
| Drag selected nodes | Move the selected section (links stretch) |
| Click a link | Select/highlight link |
| `D` | Delete selected link **or** selected node(s) |
| `C` | Clear / destroy entire topology |

### Navigation
| Key | Action |
|---|---|
| Arrow Keys (`← ↑ → ↓`) | Step through **connected** nodes (no random jumping) |

### View Controls
| Mouse | Action |
|---|---|
| Scroll Wheel | Zoom in / out |
| Right-click + drag (empty space) | Pan the canvas |

---

## Steps

## Windows

### Download
1. Go to **Releases**
2. Download `topo.exe`

### Run (recommended)
1. Move `topo.exe` to a tools folder (example: `C:\Tools\topo.exe`)
2. Add `C:\Tools` to your **PATH**
3. Press **Win + R**
4. Type: `topo`
5. Press **Enter**

The application launches instantly.

---
## macOS / Linux

### Build and Install (Recommended)

1. **Clone the repository:**
   
   ```bash
   git clone [https://github.com/faraz176/fast-topo-drawer.git](https://github.com/faraz176/fast-topo-drawer.git)

   
3. **Enter the project directory:**
   
   ```bash
   cd fast-topo-drawer


5. **Install PyInstaller:**

   ```bash
   pip install pyinstaller

6. **Build a single-file binary:**

   ```bash
   pyinstaller --onefile topo.py

7. **Install it into your PATH:**

   ```bash
   sudo mv dist/topo /usr/local/bin/topo


 8. **Run from terminal:**

   ```bash
         topo
