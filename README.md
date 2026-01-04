# fast-topo-drawer

## Quick way to draw your topology!

A lightweight, keyboard-driven tool for **rapid network topology sketching**.  
Designed for engineers who want to visualize ideas quickly without opening Visio, draw.io, or EVE-NG.

---

## Features

- Router nodes (circles)
- Switch nodes (squares)
- Click-to-connect links
- Drag-and-drop repositioning
- One-key topology reset
- Built-in legend
- Instant launch (Win + R)

---

## Controls

| Key | Action |
|---|---|
| `R` | Place Router |
| `S` | Place Switch |
| `N` | Neutral mode (connect / move only) |
| Click node → click node | Create link |
| Drag node | Move node |
| `C` | Clear / destroy topology |
| `ESC` | Cancel link |

---

## Steps

### Windows

#### Download
- Go to **Releases**
- Download `topo.exe`

#### Run (recommended)
1. Move `topo.exe` to:
2. Add `C:\Tools` to your **PATH**
3. Press **Win + R**
4. Type: topo
5. Press **Enter**

The application launches instantly.

---

### macOS / Linux

#### Build and install (recommended)

This tool runs natively on macOS and Linux by building a local binary.

1. Clone the repository:
   ```bash
   git clone https://github.com/faraz176/fast-topo-drawer.git
2. cd fast-topo-drawer
3. pip install pyinstaller
4. pyinstaller --onefile topo.py
5. sudo mv dist/topo /usr/local/bin
6. topo





