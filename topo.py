import tkinter as tk
import math

NODE_RADIUS = 18
DRAG_THRESHOLD = 5

EDGE_COLOR = "#cccccc"
EDGE_WIDTH = 2
EDGE_HIGHLIGHT_COLOR = "#ffd54f"
EDGE_HIGHLIGHT_WIDTH = 4

EDGE_HIT_TOL = 10          # easier to click lines
PREVIEW_DASH = (6, 4)

ZOOM_MIN = 0.2
ZOOM_MAX = 4.0


class TopologyTool:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Fast Network Topology Drawer")

        self.canvas = tk.Canvas(root, bg="#0f1115", width=1200, height=800)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Modes: neutral | router | switch
        self.mode = "neutral"

        # Data
        self.nodes = {}      # node_id -> {"type": "router|switch", "seq": int}
        self.edges = []      # [(line_id, n1, n2), ...]
        self.edge_map = {}   # line_id -> (n1, n2)
        self.node_seq = 0

        # Chain connect (sprout) + preview wire
        self.chain_node = None
        self.preview_line = None
        self.last_cursor = (0, 0)

        # Selection (nodes)
        self.selected_nodes = set()
        self.selection_box = None
        self.selection_start = None

        # Selection (edge)
        self.selected_edge = None

        # Dragging nodes
        self.dragging = False
        self.dragging_group = False
        self.dragging_node = None

        # Placement (router/switch)
        self.pending_place = False
        self.place_start = None

        # Click/drag tracking
        self.mouse_down_pos = None
        self.down_kind = None  # "node" | "edge" | "selectbox" | "place_or_select" | None
        self.down_node = None
        self.down_edge = None
        self.moved_far = False

        # For sprout-on-press safety
        self.pre_press_chain = None
        self.chain_set_on_press = False

        # Pan
        self.panning = False
        self.pan_last = None

        # Zoom
        self.zoom = 1.0

        # Arrow navigation state (neighbor-walk)
        self.nav_curr = None
        self.nav_prev = None

        self.draw_legend()
        self.bind_events()
        self.update_title()

    # ───────────────── UI ─────────────────

    def draw_legend(self):
        self.canvas.create_rectangle(10, 10, 320, 180, fill="#1a1d23", outline="#444", tags="legend")
        self.canvas.create_text(165, 25, text="LEGEND / CONTROLS", fill="white",
                                font=("Arial", 11, "bold"), tags="legend")

        self.canvas.create_oval(30, 45, 60, 75, fill="#4fc3f7", outline="", tags="legend")
        self.canvas.create_text(205, 60, text="Router (R) - click to place", fill="white", tags="legend")

        self.canvas.create_rectangle(30, 80, 60, 110, fill="#81c784", outline="", tags="legend")
        self.canvas.create_text(205, 95, text="Switch (S) - click to place", fill="white", tags="legend")

        self.canvas.create_line(30, 130, 60, 130, fill=EDGE_COLOR, width=EDGE_WIDTH, tags="legend")
        self.canvas.create_text(205, 130, text="Neutral (ESC) - pan/zoom/select", fill="white", tags="legend")

        self.canvas.create_text(165, 155, text="Delete (D) - delete link or node", fill="#cccccc", tags="legend")
        self.canvas.create_text(165, 172, text="Clear (C)", fill="#ff8a80", tags="legend")

    def bind_events(self):
        self.root.bind("r", lambda e: self.set_mode("router"))
        self.root.bind("s", lambda e: self.set_mode("switch"))
        self.root.bind("c", lambda e: self.clear_topology())

        # ESC is the primary "neutral + free pan/zoom" key
        self.root.bind("<Escape>", self.on_escape_to_neutral)

        self.root.bind("d", lambda e: self.delete_selected())
        self.root.bind("D", lambda e: self.delete_selected())

        # Any arrow key: move to a connected neighbor (no jumping)
        def _arrow(_e):
            self.navigate_neighbor()
        for key in ("<Left>", "<Right>", "<Up>", "<Down>"):
            self.root.bind(key, _arrow)

        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Pan (right click drag on empty space) — Button-3 (Windows/Linux), Button-2 (some mac trackpads)
        self.canvas.bind("<Button-3>", self.on_pan_down)
        self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_pan_up)
        self.canvas.bind("<Button-2>", self.on_pan_down)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_up)

        # Zoom
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/macOS
        self.canvas.bind("<Button-4>", lambda e: self.on_linux_wheel(+1, e))  # Linux
        self.canvas.bind("<Button-5>", lambda e: self.on_linux_wheel(-1, e))  # Linux

        # Preview wire follow
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def update_title(self):
        self.root.title(f"Mode: {self.mode.upper()}")

    # ───────────────── ESC => Neutral ─────────────────

    def on_escape_to_neutral(self, event=None):
        # Neutral mode + clear ALL highlights/selections so pan/zoom is always available
        self.mode = "neutral"
        self.cancel_transients(keep_selection=False)
        self.update_title()

    def cancel_transients(self, keep_selection: bool):
        # Stop chain + preview
        self.chain_node = None
        self._remove_preview()

        # Stop placement
        self.pending_place = False
        self.place_start = None

        # Stop drags
        self.dragging = False
        self.dragging_group = False
        self.dragging_node = None

        # Stop selection box
        if self.selection_box:
            self.canvas.delete(self.selection_box)
            self.selection_box = None
        self.selection_start = None

        # Stop edge selection
        self.deselect_edge()

        # Stop click tracking
        self.moved_far = False
        self.mouse_down_pos = None
        self.down_kind = None
        self.down_node = None
        self.down_edge = None

        self.pre_press_chain = None
        self.chain_set_on_press = False

        # Stop pan
        self.panning = False
        self.pan_last = None

        # Clear arrow-nav state (ESC is “free pan/zoom mode”)
        self.nav_curr = None
        self.nav_prev = None

        if not keep_selection:
            self.clear_selection()

    def set_mode(self, mode):
        self.mode = mode
        # keep_selection=True so you can place/return without losing selection unless you press ESC
        self.cancel_transients(keep_selection=True)
        self.update_title()

    # ───────────────── Node selection ─────────────────

    def clear_selection(self):
        for n in list(self.selected_nodes):
            self.set_node_highlight(n, False)
        self.selected_nodes.clear()

    def set_node_highlight(self, node, on: bool):
        if on:
            self.canvas.itemconfigure(node, outline="#ffd54f", width=3)
        else:
            self.canvas.itemconfigure(node, outline="", width=0)

    def _apply_focus(self, node):
        """Highlight node, make it the chain head, but do NOT change nav_prev/nav_curr here."""
        if node not in self.nodes:
            return
        self.deselect_edge()
        self.clear_selection()
        self.selected_nodes.add(node)
        self.set_node_highlight(node, True)
        self.chain_node = node
        self._ensure_preview(*self.last_cursor)

    def _start_selection_box(self, x, y):
        self._remove_preview()
        self.chain_node = None
        self.deselect_edge()
        self.clear_selection()

        self.selection_start = (x, y)
        self.selection_box = self.canvas.create_rectangle(
            x, y, x, y,
            outline="#4fc3f7", dash=(4, 2),
            tags=("ui",)
        )

    # ───────────────── Preview wire ─────────────────

    def _ensure_preview(self, x, y):
        if self.chain_node is None:
            self._remove_preview()
            return
        if self.selection_box or self.dragging or self.panning:
            self._remove_preview()
            return

        x1, y1 = self.get_center(self.chain_node)

        if self.preview_line is None:
            self.preview_line = self.canvas.create_line(
                x1, y1, x, y,
                fill=EDGE_COLOR,
                width=EDGE_WIDTH,
                dash=PREVIEW_DASH,
                tags=("ui",)
            )
            self.canvas.tag_lower(self.preview_line)
        else:
            self.canvas.coords(self.preview_line, x1, y1, x, y)

    def _remove_preview(self):
        if self.preview_line is not None:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

    def on_mouse_move(self, event):
        self.last_cursor = (event.x, event.y)
        self._ensure_preview(event.x, event.y)

    # ───────────────── Arrow navigation (neighbor-walk, no jumping) ─────────────────

    def navigate_neighbor(self):
        if self.selection_box or self.dragging or self.panning:
            return

        # Determine anchor current node
        cur = None
        if self.nav_curr is not None and self.nav_curr in self.nodes:
            cur = self.nav_curr
        elif self.chain_node is not None and self.chain_node in self.nodes:
            cur = self.chain_node
            self.nav_curr = cur
            self.nav_prev = None
        elif len(self.selected_nodes) == 1:
            cur = next(iter(self.selected_nodes))
            if cur in self.nodes:
                self.nav_curr = cur
                self.nav_prev = None
        if cur is None:
            return

        adj = self.build_adjacency()
        neighbors = [n for n in adj.get(cur, []) if n in self.nodes]
        if not neighbors:
            return

        nxt = self._choose_next_neighbor(self.nav_prev, cur, neighbors)
        if nxt is None:
            return

        # Advance nav direction
        self.nav_prev = cur
        self.nav_curr = nxt

        self._apply_focus(nxt)

    def _choose_next_neighbor(self, prev, cur, neighbors):
        cx, cy = self.get_center(cur)

        # First step: bias “to the right” if possible (stable, no jumping)
        if prev is None or prev not in self.nodes:
            def key(n):
                nx, ny = self.get_center(n)
                dx = nx - cx
                dy = abs(ny - cy)
                # Prefer biggest dx (rightward), then smallest vertical offset
                return (dx, -dy)
            return max(neighbors, key=key)

        # Subsequent steps: “go straight” based on previous direction
        px, py = self.get_center(prev)
        vinx, viny = (cx - px), (cy - py)
        vin_norm = math.hypot(vinx, viny)
        if vin_norm == 0:
            # fallback: same as first step
            return max(neighbors, key=lambda n: (self.get_center(n)[0] - cx, -abs(self.get_center(n)[1] - cy)))

        candidates = [n for n in neighbors if n != prev]
        if not candidates:
            return prev  # dead-end: bounce back

        best = None
        best_key = None

        for n in candidates:
            nx, ny = self.get_center(n)
            voutx, vouty = (nx - cx), (ny - cy)
            vout_norm = math.hypot(voutx, vouty)
            if vout_norm == 0:
                continue

            dot = vinx * voutx + viny * vouty
            cross = vinx * vouty - viny * voutx
            angle = abs(math.atan2(cross, dot))  # 0 = straight

            # Tie-breakers:
            # 1) smaller angle (straighter)
            # 2) larger dot (more forward)
            # 3) rightward dx (more left-to-right feel)
            dx = nx - cx
            k = (angle, -dot, -dx)

            if best is None or k < best_key:
                best = n
                best_key = k

        return best

    def build_adjacency(self):
        adj = {n: [] for n in self.nodes}
        for _, n1, n2 in self.edges:
            if n1 in self.nodes and n2 in self.nodes:
                adj[n1].append(n2)
                adj[n2].append(n1)
        return adj

    # ───────────────── Edge selection ─────────────────

    def select_edge(self, line_id):
        if self.selected_edge == line_id:
            return
        self.deselect_edge()
        self.selected_edge = line_id
        self.canvas.itemconfigure(self.selected_edge, fill=EDGE_HIGHLIGHT_COLOR, width=EDGE_HIGHLIGHT_WIDTH)

    def deselect_edge(self):
        if self.selected_edge is not None:
            if self.selected_edge in self.edge_map:
                self.canvas.itemconfigure(self.selected_edge, fill=EDGE_COLOR, width=EDGE_WIDTH)
            self.selected_edge = None

    # ───────────────── Delete (D) ─────────────────

    def delete_selected(self):
        if self.selected_edge is not None:
            self._delete_edge(self.selected_edge)
            self.selected_edge = None
            return

        if self.selected_nodes:
            doomed = set(self.selected_nodes)
            self._delete_nodes(doomed)
            self.clear_selection()
            self.chain_node = None
            self._remove_preview()

            if self.nav_curr in doomed or self.nav_prev in doomed:
                self.nav_curr = None
                self.nav_prev = None
            return

    def _delete_edge(self, line_id):
        self.canvas.delete(line_id)
        self.edge_map.pop(line_id, None)
        self.edges = [(ln, n1, n2) for (ln, n1, n2) in self.edges if ln != line_id]

    def _delete_nodes(self, nodes_to_delete: set):
        self.deselect_edge()

        to_remove = []
        for (ln, n1, n2) in self.edges:
            if n1 in nodes_to_delete or n2 in nodes_to_delete:
                to_remove.append(ln)
        for ln in to_remove:
            self._delete_edge(ln)

        for n in nodes_to_delete:
            if n in self.nodes:
                self.canvas.delete(n)
                self.nodes.pop(n, None)

    # ───────────────── Clear topology ─────────────────

    def clear_topology(self):
        self.canvas.delete("all")
        self.nodes.clear()
        self.edges.clear()
        self.edge_map.clear()
        self.node_seq = 0
        self.zoom = 1.0

        self.mode = "neutral"
        self.chain_node = None
        self._remove_preview()
        self.clear_selection()
        self.deselect_edge()

        self.selection_box = None
        self.selection_start = None
        self.pending_place = False
        self.place_start = None

        self.nav_curr = None
        self.nav_prev = None

        self.draw_legend()
        self.update_title()

    # ───────────────── Pan (right drag empty space) ─────────────────

    def on_pan_down(self, event):
        # Only pan when neutral and nothing selected/active (ESC makes this state easy to enter)
        if self.mode != "neutral":
            return
        if self.chain_node is not None:
            return
        if self.selected_nodes or self.selected_edge is not None or self.selection_box is not None:
            return
        if self.get_node_at(event.x, event.y) is not None:
            return
        if self.get_edge_at(event.x, event.y) is not None:
            return

        self.panning = True
        self.pan_last = (event.x, event.y)

    def on_pan_drag(self, event):
        if not self.panning or self.pan_last is None:
            return

        dx = event.x - self.pan_last[0]
        dy = event.y - self.pan_last[1]
        self.pan_last = (event.x, event.y)

        self.canvas.move("topo", dx, dy)
        self.last_cursor = (event.x, event.y)

    def on_pan_up(self, event):
        if not self.panning:
            return
        self.panning = False
        self.pan_last = None
        self.last_cursor = (event.x, event.y)

    # ───────────────── Zoom ─────────────────

    def on_mouse_wheel(self, event):
        direction = 1 if event.delta > 0 else -1
        self._apply_zoom(direction, event.x, event.y)

    def on_linux_wheel(self, direction, event):
        self._apply_zoom(direction, event.x, event.y)

    def _apply_zoom(self, direction, pivot_x, pivot_y):
        factor = 1.1 if direction > 0 else 0.9

        new_zoom = self.zoom * factor
        if new_zoom < ZOOM_MIN:
            factor = ZOOM_MIN / self.zoom
            new_zoom = ZOOM_MIN
        elif new_zoom > ZOOM_MAX:
            factor = ZOOM_MAX / self.zoom
            new_zoom = ZOOM_MAX

        if abs(factor - 1.0) < 1e-6:
            return

        self.zoom = new_zoom
        self.canvas.scale("topo", pivot_x, pivot_y, factor, factor)

        # Preview is UI (not scaled). Rebuild it.
        self._remove_preview()
        self._ensure_preview(*self.last_cursor)

    # ───────────────── Mouse events (left) ─────────────────

    def on_mouse_down(self, event):
        self.last_cursor = (event.x, event.y)
        self.mouse_down_pos = (event.x, event.y)
        self.moved_far = False

        self.down_kind = None
        self.down_node = None
        self.down_edge = None

        self.pre_press_chain = self.chain_node
        self.chain_set_on_press = False

        node = self.get_node_at(event.x, event.y)
        if node:
            self.down_kind = "node"
            self.down_node = node
            self.deselect_edge()

            # highlight immediately
            if node not in self.selected_nodes:
                self.clear_selection()
                self.selected_nodes.add(node)
                self.set_node_highlight(node, True)

            # set nav anchor on press (refined on mouse_up)
            self.nav_curr = node
            self.nav_prev = None

            # sprout immediately
            if self.chain_node is None:
                self.chain_node = node
                self.chain_set_on_press = True
                self._ensure_preview(event.x, event.y)

            self.dragging = True
            self.dragging_group = (len(self.selected_nodes) > 1)
            self.dragging_node = None if self.dragging_group else node
            return

        edge = self.get_edge_at(event.x, event.y)
        if edge:
            self.down_kind = "edge"
            self.down_edge = edge
            self.clear_selection()
            self.chain_node = None
            self._remove_preview()
            self.select_edge(edge)

            # edge selection disables node nav anchor
            self.nav_curr = None
            self.nav_prev = None
            return

        # Empty space
        self.deselect_edge()

        if self.mode == "neutral":
            self.down_kind = "selectbox"
            self._start_selection_box(event.x, event.y)
            return

        # router/switch click-to-place (drag converts to box-select)
        self.down_kind = "place_or_select"
        self.pending_place = True
        self.place_start = (event.x, event.y)

    def on_mouse_drag(self, event):
        self.last_cursor = (event.x, event.y)
        if self.mouse_down_pos is None:
            self.mouse_down_pos = (event.x, event.y)

        if not self.moved_far:
            if abs(event.x - self.mouse_down_pos[0]) > DRAG_THRESHOLD or abs(event.y - self.mouse_down_pos[1]) > DRAG_THRESHOLD:
                self.moved_far = True

        # If sprouted on press but user is dragging, revert sprout
        if self.down_kind == "node" and self.chain_set_on_press and self.moved_far:
            self.chain_node = self.pre_press_chain
            self.chain_set_on_press = False
            self._remove_preview()

        # router/switch: drag empty space turns place into selection box
        if self.down_kind == "place_or_select" and self.moved_far:
            self.pending_place = False
            self.down_kind = "selectbox"
            if self.selection_box is None and self.place_start is not None:
                self._start_selection_box(self.place_start[0], self.place_start[1])

        # Drag nodes
        if self.down_kind == "node" and self.dragging and self.moved_far and (self.dragging_node or self.dragging_group):
            self._remove_preview()

            dx = event.x - self.mouse_down_pos[0]
            dy = event.y - self.mouse_down_pos[1]
            self.mouse_down_pos = (event.x, event.y)

            if self.dragging_group:
                for n in self.selected_nodes:
                    self.canvas.move(n, dx, dy)
            else:
                self.canvas.move(self.dragging_node, dx, dy)

            self.update_edges()
            return

        # Update selection box
        if self.down_kind == "selectbox" and self.selection_box and self.selection_start:
            x0, y0 = self.selection_start
            self.canvas.coords(self.selection_box, x0, y0, event.x, event.y)
            self.update_group_selection(x0, y0, event.x, event.y)

    def on_mouse_up(self, event):
        self.last_cursor = (event.x, event.y)

        # router/switch placement
        if self.down_kind == "place_or_select":
            if self.pending_place and self.place_start and self.mode in ("router", "switch"):
                new_node = self.create_node(self.place_start[0], self.place_start[1])
                if new_node is not None:
                    self.nav_curr = new_node
                    self.nav_prev = None
                    self._apply_focus(new_node)
            self.pending_place = False
            self.place_start = None

        # Node click (connect chain)
        if self.down_kind == "node":
            if not self.moved_far and self.down_node is not None:
                clicked = self.down_node
                src = self.pre_press_chain

                if src is not None and src in self.nodes and src != clicked:
                    if not self.edge_exists(src, clicked):
                        self.connect_nodes(src, clicked)

                    # After a connect: keep direction (src -> clicked)
                    self.nav_prev = src
                    self.nav_curr = clicked
                    self._apply_focus(clicked)
                else:
                    # Simple focus
                    self.nav_prev = None
                    self.nav_curr = clicked
                    self._apply_focus(clicked)

            self.dragging = False
            self.dragging_group = False
            self.dragging_node = None

        # Finish selection box
        if self.down_kind == "selectbox":
            if self.selection_box and self.selection_start:
                x0, y0 = self.selection_start
                x1, y1 = event.x, event.y

                if abs(x1 - x0) <= DRAG_THRESHOLD and abs(y1 - y0) <= DRAG_THRESHOLD:
                    self.clear_selection()

                self.canvas.delete(self.selection_box)
                self.selection_box = None
                self.selection_start = None

        # Reset click tracking
        self.mouse_down_pos = None
        self.down_kind = None
        self.down_node = None
        self.down_edge = None
        self.moved_far = False
        self.pre_press_chain = None
        self.chain_set_on_press = False

        self._ensure_preview(event.x, event.y)

    # ───────────────── Nodes / edges ─────────────────

    def create_node(self, x, y):
        if self.mode == "router":
            node = self.canvas.create_oval(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill="#4fc3f7", outline="", width=0,
                tags=("topo",)
            )
            self.nodes[node] = {"type": "router", "seq": self.node_seq}
            self.node_seq += 1
            return node

        if self.mode == "switch":
            node = self.canvas.create_rectangle(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill="#81c784", outline="", width=0,
                tags=("topo",)
            )
            self.nodes[node] = {"type": "switch", "seq": self.node_seq}
            self.node_seq += 1
            return node

        return None

    def connect_nodes(self, n1, n2):
        x1, y1 = self.get_center(n1)
        x2, y2 = self.get_center(n2)
        line = self.canvas.create_line(
            x1, y1, x2, y2,
            fill=EDGE_COLOR, width=EDGE_WIDTH,
            tags=("topo",)
        )
        self.edges.append((line, n1, n2))
        self.edge_map[line] = (n1, n2)
        self.canvas.tag_lower(line)

    def update_edges(self):
        for line, n1, n2 in self.edges:
            if n1 not in self.nodes or n2 not in self.nodes:
                continue
            x1, y1 = self.get_center(n1)
            x2, y2 = self.get_center(n2)
            self.canvas.coords(line, x1, y1, x2, y2)

    def edge_exists(self, a, b):
        for _, n1, n2 in self.edges:
            if (n1 == a and n2 == b) or (n1 == b and n2 == a):
                return True
        return False

    # ───────────────── Selection box logic ─────────────────

    def update_group_selection(self, x1, y1, x2, y2):
        new_sel = set()
        minx, maxx = min(x1, x2), max(x1, x2)
        miny, maxy = min(y1, y2), max(y1, y2)

        for node in self.nodes:
            cx, cy = self.get_center(node)
            if minx <= cx <= maxx and miny <= cy <= maxy:
                new_sel.add(node)

        for node in list(self.selected_nodes - new_sel):
            self.set_node_highlight(node, False)
        for node in list(new_sel - self.selected_nodes):
            self.set_node_highlight(node, True)

        self.selected_nodes = new_sel

    # ───────────────── Hit testing helpers ─────────────────

    def get_center(self, node):
        x1, y1, x2, y2 = self.canvas.coords(node)
        return (x1 + x2) / 2, (y1 + y2) / 2

    def get_node_at(self, x, y):
        for item in self.canvas.find_overlapping(x, y, x, y):
            if item in self.nodes:
                return item
        return None

    def _dist_point_to_segment(self, px, py, x1, y1, x2, y2):
        vx, vy = x2 - x1, y2 - y1
        wx, wy = px - x1, py - y1

        c1 = vx * wx + vy * wy
        if c1 <= 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        c2 = vx * vx + vy * vy
        if c2 <= c1:
            return ((px - x2) ** 2 + (py - y2) ** 2) ** 0.5

        b = c1 / c2
        bx, by = x1 + b * vx, y1 + b * vy
        return ((px - bx) ** 2 + (py - by) ** 2) ** 0.5

    def get_edge_at(self, x, y):
        items = self.canvas.find_overlapping(
            x - EDGE_HIT_TOL, y - EDGE_HIT_TOL,
            x + EDGE_HIT_TOL, y + EDGE_HIT_TOL
        )
        candidates = [it for it in items if it in self.edge_map]
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        best = None
        best_d = float("inf")
        for line in candidates:
            x1, y1, x2, y2 = self.canvas.coords(line)
            d = self._dist_point_to_segment(x, y, x1, y1, x2, y2)
            if d < best_d:
                best_d = d
                best = line

        return best if best_d <= EDGE_HIT_TOL else None


if __name__ == "__main__":
    root = tk.Tk()
    app = TopologyTool(root)
    root.mainloop()
