import tkinter as tk

NODE_RADIUS = 18

class TopologyTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast Network Topology Drawer")

        self.canvas = tk.Canvas(root, bg="#0f1115", width=1200, height=800)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.mode = "neutral"  # neutral | router | switch
        self.nodes = {}
        self.edges = []
        self.node_id = 0

        self.selected_node = None
        self.dragging = None

        self.draw_legend()
        self.bind_events()
        self.update_title()

    def draw_legend(self):
        self.canvas.create_rectangle(10, 10, 260, 170, fill="#1a1d23", outline="#444", tags="legend")
        self.canvas.create_text(130, 25, text="LEGEND / CONTROLS", fill="white",
                                font=("Arial", 11, "bold"), tags="legend")

        self.canvas.create_oval(30, 45, 60, 75, fill="#4fc3f7", outline="", tags="legend")
        self.canvas.create_text(160, 60, text="Router (R)", fill="white", tags="legend")

        self.canvas.create_rectangle(30, 80, 60, 110, fill="#81c784", outline="", tags="legend")
        self.canvas.create_text(160, 95, text="Switch (S)", fill="white", tags="legend")

        self.canvas.create_line(30, 130, 60, 130, fill="#ccc", width=2, tags="legend")
        self.canvas.create_text(160, 130, text="Connect Mode (N)", fill="white", tags="legend")

        self.canvas.create_text(130, 155, text="Clear Topology (C)", fill="#ff8a80", tags="legend")

    def bind_events(self):
        self.root.bind("r", lambda e: self.set_mode("router"))
        self.root.bind("s", lambda e: self.set_mode("switch"))
        self.root.bind("n", lambda e: self.set_mode("neutral"))
        self.root.bind("c", lambda e: self.clear_topology())
        self.root.bind("<Escape>", self.cancel_link)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def set_mode(self, mode):
        self.mode = mode
        self.selected_node = None
        self.update_title()

    def update_title(self):
        self.root.title(f"Mode: {self.mode.upper()}")

    def cancel_link(self, event=None):
        self.selected_node = None

    # ───────── TOPO DESTRUCTION ─────────
    def clear_topology(self):
        self.canvas.delete("all")
        self.nodes.clear()
        self.edges.clear()
        self.node_id = 0
        self.selected_node = None
        self.dragging = None
        self.draw_legend()

    def on_click(self, event):
        node = self.get_node_at(event.x, event.y)

        if self.mode == "neutral":
            if node:
                if not self.selected_node:
                    self.selected_node = node
                    self.dragging = node
                else:
                    if self.selected_node != node:
                        self.connect_nodes(self.selected_node, node)
                    self.selected_node = None
            return

        if node:
            self.dragging = node
            return

        self.create_node(event.x, event.y)

    def on_drag(self, event):
        if self.dragging:
            x, y = event.x, event.y
            self.canvas.coords(
                self.dragging,
                x - NODE_RADIUS,
                y - NODE_RADIUS,
                x + NODE_RADIUS,
                y + NODE_RADIUS
            )
            self.update_edges()

    def on_release(self, event):
        self.dragging = None

    def create_node(self, x, y):
        if self.mode == "router":
            shape = self.canvas.create_oval(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill="#4fc3f7", outline=""
            )
        elif self.mode == "switch":
            shape = self.canvas.create_rectangle(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill="#81c784", outline=""
            )
        else:
            return

        self.nodes[shape] = {"id": self.node_id}
        self.node_id += 1

    def connect_nodes(self, n1, n2):
        x1, y1 = self.get_center(n1)
        x2, y2 = self.get_center(n2)
        line = self.canvas.create_line(x1, y1, x2, y2, fill="#cccccc", width=2)
        self.edges.append((line, n1, n2))
        self.canvas.tag_lower(line)

    def update_edges(self):
        for line, n1, n2 in self.edges:
            x1, y1 = self.get_center(n1)
            x2, y2 = self.get_center(n2)
            self.canvas.coords(line, x1, y1, x2, y2)

    def get_center(self, node):
        x1, y1, x2, y2 = self.canvas.coords(node)
        return (x1 + x2) / 2, (y1 + y2) / 2

    def get_node_at(self, x, y):
        for item in self.canvas.find_overlapping(x, y, x, y):
            if item in self.nodes:
                return item
        return None


if __name__ == "__main__":
    root = tk.Tk()
    app = TopologyTool(root)
    root.mainloop()
