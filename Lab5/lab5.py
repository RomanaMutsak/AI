import heapq
import time
import tkinter as tk
from collections import deque
from tkinter import ttk, messagebox

INF = float("inf")
MAP_W, MAP_H = 1273, 952        

BASE_CITIES = {
    "Київ": (600, 240), "Житомир": (480, 270), "Вінниця": (478, 358),
    "Черкаси": (688, 340), "Чернігів": (650, 130), "Суми": (880, 178),
    "Полтава": (858, 300), "Харків": (990, 282), "Луганськ": (1212, 410),
    "Донецьк": (1128, 482), "Маріуполь": (1098, 598), "Дніпро": (905, 455),
    "Запоріжжя": (922, 530), "Мелітополь": (940, 650), "Кривий Ріг": (808, 522),
    "Кропивницький": (700, 445), "Миколаїв": (722, 632), "Херсон": (742, 672),
    "Одеса": (608, 688), "Сімферополь": (852, 862), "Севастополь": (790, 896),
    "Хмельницький": (360, 330), "Тернопіль": (240, 322), "Івано-Франківськ": (160, 392),
    "Ужгород": (42, 412), "Львів": (140, 282), "Луцьк": (258, 182), "Рівне": (300, 212),
    "Чернівці": (262, 462),
}

BASE_ROADS = [
    ("Вінниця", "Житомир", 127), ("Вінниця", "Київ", 267), ("Вінниця", "Кропивницький", 320),
    ("Вінниця", "Миколаїв", 428), ("Вінниця", "Одеса", 423), ("Вінниця", "Черкаси", 341),
    ("Вінниця", "Чернівці", 276), ("Дніпро", "Донецьк", 248), ("Дніпро", "Запоріжжя", 85),
    ("Дніпро", "Кропивницький", 244), ("Дніпро", "Кривий Ріг", 146), ("Дніпро", "Полтава", 160),
    ("Дніпро", "Харків", 218), ("Донецьк", "Луганськ", 156), ("Донецьк", "Маріуполь", 113),
    ("Донецьк", "Харків", 294), ("Запоріжжя", "Мелітополь", 125),
    ("Івано-Франківськ", "Тернопіль", 133), ("Івано-Франківськ", "Ужгород", 293),
    ("Київ", "Житомир", 140), ("Київ", "Полтава", 340), ("Київ", "Суми", 333),
    ("Київ", "Черкаси", 189), ("Київ", "Чернігів", 148), ("Кропивницький", "Полтава", 246),
    ("Луганськ", "Харків", 325), ("Львів", "Івано-Франківськ", 134), ("Львів", "Луцьк", 151),
    ("Львів", "Рівне", 211), ("Львів", "Тернопіль", 127), ("Львів", "Ужгород", 268),
    ("Львів", "Чернівці", 268), ("Мелітополь", "Маріуполь", 192), ("Мелітополь", "Сімферополь", 250),
    ("Миколаїв", "Херсон", 69), ("Рівне", "Житомир", 188), ("Рівне", "Луцьк", 73),
    ("Рівне", "Тернопіль", 155), ("Харків", "Полтава", 143), ("Херсон", "Мелітополь", 231),
    ("Хмельницький", "Вінниця", 119), ("Хмельницький", "Житомир", 183), ("Хмельницький", "Рівне", 194),
    ("Хмельницький", "Тернопіль", 112), ("Хмельницький", "Чернівці", 187), ("Суми", "Харків", 184),
    ("Черкаси", "Полтава", 233), ("Полтава", "Суми", 175), ("Чернігів", "Суми", 306),
    ("Сімферополь", "Севастополь", 81),
]

UKRAINE_OUTLINE = [
    (150, 78), (235, 58), (330, 62), (420, 48), (505, 42), (580, 45), (622, 18), (690, 30),
    (760, 22), (840, 28), (862, 70), (895, 112), (902, 150), (935, 178), (985, 202),
    (1000, 228), (1060, 236), (1112, 244), (1165, 262), (1215, 284), (1250, 318),
    (1256, 400), (1250, 470), (1232, 520), (1200, 560), (1150, 588), (1100, 612),
    (1040, 640), (985, 676), (935, 712), (905, 735), (960, 770), (1020, 790), (1060, 818),
    (1020, 840), (960, 872), (905, 915), (865, 936), (815, 918), (772, 892), (768, 840),
    (792, 788), (845, 752), (800, 722), (752, 700), (700, 698), (655, 692), (615, 712),
    (575, 735), (548, 790), (515, 845), (468, 828), (432, 782), (452, 742), (488, 705),
    (520, 652), (500, 590), (460, 540), (425, 500), (380, 476), (330, 478), (280, 486),
    (225, 500), (165, 490), (105, 478), (55, 455), (28, 420), (40, 385), (60, 340),
    (95, 300), (70, 255), (115, 215), (155, 170), (165, 120),
]

LABEL_LEFT = {"Севастополь", "Херсон"}

C_SEA, C_LAND, C_BORDER = "#D6E8F5", "#F7F0DC", "#C27C7C"
C_ROAD, C_ARC = "#8D99A6", "#C62828"
C_CITY, C_START, C_GOAL = "#455A64", "#2E7D32", "#C62828"
C_OPEN, C_CLOSED, C_CUR = "#FB8C00", "#43A047", "#D50000"
C_RELAX, C_TREE, C_PATH = "#1E88E5", "#66BB6A", "#FFD600"

class SearchResult:
    def __init__(self):
        self.algo = ""
        self.found = False
        self.path = []          
        self.distance = INF                                                                       
        self.dist = {}          
        self.prev = {}          
        self.closed = []       
        self.events = []       
        self.log = []           
        self.iterations = 0     
        self.relaxations = 0    
        self.updates = 0       
        self.max_queue = 0
        self.time_ms = 0.0


def restore_path(prev, start, goal):
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return list(reversed(path))


def dijkstra(adj, start, goal):
    res = SearchResult()
    res.algo = "Алгоритм Дейкстри"
    t0 = time.perf_counter()
    dist = {v: INF for v in adj}
    dist[start] = 0
    prev = {}
    closed = set()
    heap = [(0, start)]
    while heap:
        res.max_queue = max(res.max_queue, len(heap))
        d, v = heapq.heappop(heap)
        if v in closed or d > dist[v]:
            continue                                
        closed.add(v)
        res.closed.append(v)
        res.iterations += 1
        res.events.append(("extract", v, d))
        entry = [v, d, []]
        if v == goal:
            res.log.append(entry)
            break
        for u, w in sorted(adj[v].items()):
            if u in closed:
                continue
            res.relaxations += 1
            nd = d + w
            better = nd < dist[u]
            if better:
                old = dist[u]
                dist[u] = nd
                prev[u] = v
                heapq.heappush(heap, (nd, u))
                res.updates += 1
                entry[2].append((u, old, nd))
            res.events.append(("relax", v, u, nd, better))
        res.log.append(entry)
    res.time_ms = (time.perf_counter() - t0) * 1000
    res.dist, res.prev = dist, prev
    if goal in closed:
        res.found = True
        res.path = restore_path(prev, start, goal)
        res.distance = dist[goal]
    return res


def bfs(adj, start, goal):
    res = SearchResult()
    res.algo = "Пошук у ширину (мінімум доріг)"
    t0 = time.perf_counter()
    prev, seen = {}, {start}
    queue = deque([start])
    level = {start: 0}
    while queue:
        res.max_queue = max(res.max_queue, len(queue))
        v = queue.popleft()
        res.closed.append(v)
        res.iterations += 1
        res.events.append(("extract", v, level[v]))
        entry = [v, level[v], []]
        if v == goal:
            res.log.append(entry)
            break
        for u in sorted(adj[v]):
            res.relaxations += 1
            if u not in seen:
                seen.add(u)
                prev[u] = v
                level[u] = level[v] + 1
                queue.append(u)
                res.updates += 1
                entry[2].append((u, INF, level[u]))
                res.events.append(("relax", v, u, level[u], True))
        res.log.append(entry)
    res.time_ms = (time.perf_counter() - t0) * 1000
    res.prev = prev
    res.dist = {v: level.get(v, INF) for v in adj}
    if goal in seen:
        res.found = True
        res.path = restore_path(prev, start, goal)
        res.distance = sum(adj[a][b] for a, b in zip(res.path, res.path[1:]))
    return res

class DijkstraMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Системи ШІ - Лабораторна 5 (Алгоритм Дейкстри) - Романа Муцак (ФЕІ-42)")
        self.root.geometry("1440x900")
        self.load_base_graph()
        self.result = None
        self.anim_step = 0
        self.anim_job = None
        self.paused = False
        self.place_mode = False
        self.results_win = None
        self.state = None
        self.setup_ui()
        self.refresh_lists()
        self.start_var.set("Ужгород")
        self.goal_var.set("Луганськ")
        self.redraw()

    def load_base_graph(self):
        self.cities = dict(BASE_CITIES)
        self.adj = {c: {} for c in self.cities}
        for a, b, w in BASE_ROADS:
            self.adj[a][b] = w
            self.adj[b][a] = w

    def road_list(self):
        """Повертає список (a, b, w, тип): тип 'edge' – ребро, 'arc' – дуга a→b."""
        out, seen = [], set()
        for a in self.adj:
            for b, w in self.adj[a].items():
                if (b, a) in seen:
                    continue
                if self.adj.get(b, {}).get(a) == w:
                    out.append((a, b, w, "edge"))
                    seen.add((a, b))
                else:
                    out.append((a, b, w, "arc"))
        return out

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))
        left = ttk.Frame(self.root, padding=6)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right = ttk.Frame(self.root, padding=6)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        f1 = ttk.LabelFrame(left, text="Маршрут", padding=6)
        f1.pack(fill=tk.X, pady=3)
        self.start_var, self.goal_var = tk.StringVar(), tk.StringVar()
        ttk.Label(f1, text="Відправна точка:").grid(row=0, column=0, sticky="w")
        self.start_cb = ttk.Combobox(f1, textvariable=self.start_var, state="readonly", width=17)
        self.start_cb.grid(row=0, column=1, pady=1)
        ttk.Label(f1, text="Цільова точка:").grid(row=1, column=0, sticky="w")
        self.goal_cb = ttk.Combobox(f1, textvariable=self.goal_var, state="readonly", width=17)
        self.goal_cb.grid(row=1, column=1, pady=1)
        for cb in (self.start_cb, self.goal_cb):
            cb.bind("<<ComboboxSelected>>", lambda e: self.reset_search())
        ttk.Button(f1, text="⇅ Поміняти місцями", command=self.swap_points).grid(row=2, column=0, columnspan=2, sticky="we", pady=2)
        ttk.Label(f1, text="(ЛКМ по місту – старт, ПКМ – ціль)", foreground="#555").grid(row=3, column=0, columnspan=2)

        f2 = ttk.LabelFrame(left, text="Пошук", padding=6)
        f2.pack(fill=tk.X, pady=3)
        self.algo_var = tk.StringVar(value="dijkstra")
        ttk.Radiobutton(f2, text="Алгоритм Дейкстри (мінімум км)", value="dijkstra",
                        variable=self.algo_var, command=self.reset_search).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(f2, text="Пошук у ширину (мінімум доріг) – порівняння", value="bfs",
                        variable=self.algo_var, command=self.reset_search).grid(row=1, column=0, columnspan=2, sticky="w")
        self.delay_var = tk.IntVar(value=300)
        ttk.Label(f2, text="Затримка, мс:").grid(row=2, column=0, sticky="w")
        sc = ttk.Frame(f2)
        sc.grid(row=2, column=1, sticky="we")
        ttk.Scale(sc, from_=0, to=1500, variable=self.delay_var, orient=tk.HORIZONTAL, length=120,
                  command=lambda v: self.delay_var.set(int(float(v)))).pack(side=tk.LEFT)
        ttk.Label(sc, textvariable=self.delay_var, width=5).pack(side=tk.LEFT)
        btns = [("▶ Пуск (з анімацією)", self.run_animated), ("⚡ Миттєвий пошук", self.run_instant),
                ("⏸ Пауза / продовжити", self.toggle_pause), ("⏭ Крок", self.step_once),
                ("↺ Скинути", self.reset_search), ("📋 Результати", self.show_results)]
        for i, (t, cmd) in enumerate(btns):
            ttk.Button(f2, text=t, command=cmd).grid(row=3 + i // 2, column=i % 2, sticky="we", padx=1, pady=1)
        self.show_w_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f2, text="Показувати відстані на дорогах", variable=self.show_w_var,
                        command=self.redraw).grid(row=6, column=0, columnspan=2, sticky="w")

        f3 = ttk.LabelFrame(left, text="Вершини графу (міста)", padding=6)
        f3.pack(fill=tk.X, pady=3)
        ttk.Label(f3, text="Назва міста:").grid(row=0, column=0, sticky="w")
        self.city_var = tk.StringVar()
        self.city_cb = ttk.Combobox(f3, textvariable=self.city_var, width=17)
        self.city_cb.grid(row=0, column=1, pady=1)
        self.place_btn = ttk.Button(f3, text="Додати місто (клік на карті)", command=self.toggle_place_mode)
        self.place_btn.grid(row=1, column=0, columnspan=2, sticky="we", pady=1)
        ttk.Button(f3, text="Видалити місто", command=self.delete_city).grid(row=2, column=0, columnspan=2, sticky="we", pady=1)

        f4 = ttk.LabelFrame(left, text="Ребра / дуги графу (дороги)", padding=6)
        f4.pack(fill=tk.X, pady=3)
        self.ra_var, self.rb_var, self.rw_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(f4, text="Місто A:").grid(row=0, column=0, sticky="w")
        self.ra_cb = ttk.Combobox(f4, textvariable=self.ra_var, state="readonly", width=17)
        self.ra_cb.grid(row=0, column=1, pady=1)
        ttk.Label(f4, text="Місто B:").grid(row=1, column=0, sticky="w")
        self.rb_cb = ttk.Combobox(f4, textvariable=self.rb_var, state="readonly", width=17)
        self.rb_cb.grid(row=1, column=1, pady=1)
        ttk.Label(f4, text="Відстань, км:").grid(row=2, column=0, sticky="w")
        ttk.Entry(f4, textvariable=self.rw_var, width=10).grid(row=2, column=1, sticky="w", pady=1)
        self.rtype_var = tk.StringVar(value="edge")
        ttk.Radiobutton(f4, text="ребро (рух в обидва боки)", value="edge", variable=self.rtype_var).grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(f4, text="дуга (рух лише A → B)", value="arc", variable=self.rtype_var).grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Button(f4, text="Додати / змінити дорогу", command=self.add_road).grid(row=5, column=0, columnspan=2, sticky="we", pady=1)
        ttk.Button(f4, text="Видалити дорогу A–B", command=self.delete_road).grid(row=6, column=0, columnspan=2, sticky="we", pady=1)
        ttk.Button(f4, text="Відновити базовий граф", command=self.restore_base).grid(row=7, column=0, columnspan=2, sticky="we", pady=(6, 1))

        self.info_var = tk.StringVar()
        ttk.Label(left, textvariable=self.info_var, foreground="#37474F").pack(fill=tk.X, pady=(4, 0))
        self.status_var = tk.StringVar(value="Оберіть міста та натисніть «Пуск».")
        ttk.Label(left, textvariable=self.status_var, wraplength=330, foreground="#0D47A1",
                  font=("Arial", 9, "bold")).pack(fill=tk.X, pady=6)

        self.canvas = tk.Canvas(right, bg=C_SEA, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        items = [(C_START, "відправна"), (C_GOAL, "цільова"), (C_OPEN, "тимчасова мітка (у черзі)"),
                 (C_CLOSED, "постійна мітка"), (C_CUR, "поточна вершина"),
                 (C_RELAX, "перевірка дуги"), (C_TREE, "дерево найкоротших шляхів"),
                 (C_PATH, "найкоротший шлях"), (C_ARC, "дуга (одностороння дорога)")]
        for row in (items[:5], items[5:]):
            lg = ttk.Frame(right)
            lg.pack(fill=tk.X, pady=(3, 0))
            for color, text in row:
                tk.Label(lg, bg=color, width=2, relief="solid", bd=1).pack(side=tk.LEFT, padx=(8, 2))
                ttk.Label(lg, text=text).pack(side=tk.LEFT)

    def refresh_lists(self):
        names = sorted(self.cities)
        for cb in (self.start_cb, self.goal_cb, self.city_cb, self.ra_cb, self.rb_cb):
            cb["values"] = names
        for var in (self.start_var, self.goal_var, self.ra_var, self.rb_var):
            if var.get() and var.get() not in self.cities:
                var.set("")
        roads = self.road_list()
        self.info_var.set("Порядок графу (міст): %d;  розмір (доріг): %d  (ребер: %d, дуг: %d)" % (
            len(self.cities), len(roads), sum(r[3] == "edge" for r in roads), sum(r[3] == "arc" for r in roads)))

    def transform(self):
        w = max(self.canvas.winfo_width(), 300)
        h = max(self.canvas.winfo_height(), 300)
        x0, y0, x1, y1 = 10, 10, 1265, 945      
        s = min((w - 16) / (x1 - x0), (h - 16) / (y1 - y0))
        ox = (w - (x1 - x0) * s) / 2 - x0 * s
        oy = (h - (y1 - y0) * s) / 2 - y0 * s
        return s, ox, oy

    def to_canvas(self, x, y):
        s, ox, oy = self.transform()
        return ox + x * s, oy + y * s

    def to_map(self, cx, cy):
        s, ox, oy = self.transform()
        return (cx - ox) / s, (cy - oy) / s

    def city_at(self, cx, cy):
        best, bd = None, 15 ** 2
        for name, (x, y) in self.cities.items():
            px, py = self.to_canvas(x, y)
            d = (px - cx) ** 2 + (py - cy) ** 2
            if d < bd:
                best, bd = name, d
        return best

    def redraw(self):
        cv = self.canvas
        cv.delete("all")
        s, ox, oy = self.transform()
        pts = []
        for x, y in UKRAINE_OUTLINE:
            pts += self.to_canvas(x, y)
        cv.create_polygon(*pts, fill=C_LAND, outline=C_BORDER, width=2)
        cv.create_text(*self.to_canvas(560, 860), text="ЧОРНЕ МОРЕ", fill="#5C8DB8", font=("Arial", 14, "italic"))
        cv.create_text(*self.to_canvas(1080, 720), text="АЗОВСЬКЕ\nМОРЕ", fill="#5C8DB8", font=("Arial", 11, "italic"))

        st = self.state or {}
        path = st.get("path", [])
        path_edges = set(zip(path, path[1:])) | set(zip(path[1:], path))
        tree_edges = set((p, c) for c, p in st.get("prev", {}).items())
        relax_edge = st.get("relax")
        font_w = ("Arial", max(7, int(11 * s * 1.15)))

        for a, b, w, kind in self.road_list():
            (x1, y1), (x2, y2) = self.to_canvas(*self.cities[a]), self.to_canvas(*self.cities[b])
            on_path = (a, b) in path_edges
            in_tree = (a, b) in tree_edges or (b, a) in tree_edges
            if on_path:
                cv.create_line(x1, y1, x2, y2, fill=C_PATH, width=9, capstyle=tk.ROUND)
                cv.create_line(x1, y1, x2, y2, fill="#D50000", width=3)
            color, width = (C_ARC, 2) if kind == "arc" else (C_ROAD, 2)
            if in_tree and not on_path:
                color, width = C_TREE, 4
            if relax_edge and {a, b} == set(relax_edge[:2]):
                color, width = C_RELAX, 5
            if not on_path:
                if kind == "arc":
                    dx, dy = x2 - x1, y2 - y1
                    ln = max(1.0, (dx * dx + dy * dy) ** 0.5)
                    cv.create_line(x1, y1, x2 - dx / ln * 9, y2 - dy / ln * 9, fill=color, width=width,
                                   arrow=tk.LAST, arrowshape=(12, 14, 5))
                else:
                    cv.create_line(x1, y1, x2, y2, fill=color, width=width)
            if self.show_w_var.get():
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                t = cv.create_text(mx, my, text=str(w), font=font_w, fill="#37474F")
                bb = cv.bbox(t)
                r = cv.create_rectangle(bb[0] - 2, bb[1] - 1, bb[2] + 2, bb[3] + 1, fill="white", outline="#B0BEC5")
                cv.tag_raise(t, r)

        labels = st.get("labels", {})
        closed = st.get("closed", set())
        cur = st.get("current")
        font_c = ("Arial", max(8, int(12 * s * 1.15)), "bold")
        font_l = ("Arial", max(7, int(11 * s * 1.15)), "bold")
        r = max(5, int(8 * s * 1.2))
        start, goal = self.start_var.get(), self.goal_var.get()
        for name, (x, y) in self.cities.items():
            cx, cy = self.to_canvas(x, y)
            fill = C_CITY
            if name in closed:
                fill = C_CLOSED
            elif name in labels:
                fill = C_OPEN
            if name in path:
                fill = C_PATH
            if name == start:
                fill = C_START
            if name == goal:
                fill = C_GOAL
            if name == cur:
                cv.create_oval(cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6, outline=C_CUR, width=3)
            cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline="black", width=1)
            left = x > 1150 or name in LABEL_LEFT          
            tx = cx - r - 3 if left else cx + r + 3
            tid = cv.create_text(tx, cy - r - 2, text=name, anchor="se" if left else "sw", font=font_c, fill="#212121")
            bb = cv.bbox(tid)
            bg = cv.create_rectangle(bb[0] - 1, bb[1], bb[2] + 1, bb[3], fill="#FFFDF5", outline="")
            cv.tag_raise(tid, bg)
            if st:
                d = labels.get(name, INF)
                txt = "∞" if d == INF else (f"{d:g}" + ("" if st.get("algo") == "bfs" else " км"))
                lc = C_CLOSED if name in closed else (C_OPEN if d != INF else "#90A4AE")
                lid = cv.create_text(tx, cy + 2, text=txt, anchor="ne" if left else "nw", font=font_l, fill="white")
                bb = cv.bbox(lid)
                lb = cv.create_rectangle(bb[0] - 2, bb[1] - 1, bb[2] + 2, bb[3] + 1, fill=lc, outline="")
                cv.tag_raise(lid, lb)

        if self.place_mode:
            cv.create_text(12, 12, anchor="nw", text="Клікніть на карті, щоб розмістити місто «%s»" % self.city_var.get(),
                           font=("Arial", 12, "bold"), fill="#D50000")

    def on_left_click(self, event):
        if self.place_mode:
            name = self.city_var.get().strip()
            x, y = self.to_map(event.x, event.y)
            self.cities[name] = (round(x), round(y))
            self.adj[name] = {}
            self.place_mode = False
            self.place_btn.configure(text="Додати місто (клік на карті)")
            self.refresh_lists()
            self.reset_search()
            self.status_var.set(f"Додано місто «{name}». Тепер з'єднайте його дорогами.")
            return
        c = self.city_at(event.x, event.y)
        if c:
            if c == self.goal_var.get():
                self.goal_var.set(self.start_var.get())
            self.start_var.set(c)
            self.reset_search()

    def on_right_click(self, event):
        c = self.city_at(event.x, event.y)
        if c:
            if c == self.start_var.get():
                self.start_var.set(self.goal_var.get())
            self.goal_var.set(c)
            self.reset_search()

    def toggle_place_mode(self):
        name = self.city_var.get().strip()
        if not self.place_mode:
            if not name:
                messagebox.showerror("Помилка", "Введіть назву нового міста")
                return
            if name in self.cities:
                messagebox.showerror("Помилка", f"Місто «{name}» вже є у графі")
                return
        self.place_mode = not self.place_mode
        self.place_btn.configure(text="Скасувати розміщення" if self.place_mode else "Додати місто (клік на карті)")
        self.redraw()

    def delete_city(self):
        name = self.city_var.get().strip()
        if name not in self.cities:
            messagebox.showerror("Помилка", "Оберіть місто зі списку")
            return
        del self.cities[name]
        del self.adj[name]
        for a in self.adj:
            self.adj[a].pop(name, None)
        self.city_var.set("")
        self.refresh_lists()
        self.reset_search()
        self.status_var.set(f"Місто «{name}» та всі його дороги видалено.")

    def add_road(self):
        a, b = self.ra_var.get(), self.rb_var.get()
        if a not in self.cities or b not in self.cities or a == b:
            messagebox.showerror("Помилка", "Оберіть два різні міста")
            return
        try:
            w = float(self.rw_var.get().replace(",", "."))
            if w <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Помилка", "Відстань має бути додатним числом")
            return
        w = int(w) if w == int(w) else w
        self.adj[a][b] = w
        if self.rtype_var.get() == "edge":
            self.adj[b][a] = w
        else:
            self.adj[b].pop(a, None)
        self.refresh_lists()
        self.reset_search()
        kind = "ребро" if self.rtype_var.get() == "edge" else "дугу"
        self.status_var.set(f"Додано {kind} {a} – {b}: {w} км.")

    def delete_road(self):
        a, b = self.ra_var.get(), self.rb_var.get()
        if b not in self.adj.get(a, {}) and a not in self.adj.get(b, {}):
            messagebox.showerror("Помилка", "Між цими містами немає дороги")
            return
        self.adj[a].pop(b, None)
        self.adj[b].pop(a, None)
        self.refresh_lists()
        self.reset_search()
        self.status_var.set(f"Дорогу {a} – {b} видалено.")

    def restore_base(self):
        self.load_base_graph()
        self.refresh_lists()
        self.reset_search()
        self.status_var.set("Відновлено базовий граф: 29 міст, 50 доріг.")

    def swap_points(self):
        a, b = self.start_var.get(), self.goal_var.get()
        self.start_var.set(b)
        self.goal_var.set(a)
        self.reset_search()

    def stop_animation(self):
        if self.anim_job:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None

    def reset_search(self):
        self.stop_animation()
        self.result = None
        self.state = None
        self.anim_step = 0
        self.paused = False
        self.redraw()

    def compute(self):
        s, g = self.start_var.get(), self.goal_var.get()
        if s not in self.cities or g not in self.cities:
            messagebox.showerror("Помилка", "Оберіть відправну та цільову точки")
            return False
        if s == g:
            messagebox.showwarning("Увага", "Відправна і цільова точки збігаються")
            return False
        algo = self.algo_var.get()
        self.result = dijkstra(self.adj, s, g) if algo == "dijkstra" else bfs(self.adj, s, g)
        self.state = {"algo": algo, "labels": {s: 0}, "closed": set(), "prev": {}, "current": None,
                      "relax": None, "path": []}
        self.anim_step = 0
        return True

    def advance(self):
        """Відтворює наступну подію пошуку (вибір вершини або перевірку дуги)."""
        res, st = self.result, self.state
        if self.anim_step >= len(res.events):
            return False
        ev = res.events[self.anim_step]
        self.anim_step += 1
        if ev[0] == "extract":
            _, v, d = ev
            st["current"], st["relax"] = v, None
            st["closed"].add(v)
            self.status_var.set(f"Ітерація {len(st['closed'])}: вибрано «{v}» з найменшою міткою {d:g}"
                                f"{' км' if st['algo'] == 'dijkstra' else ''} – мітка стає постійною")
        else:
            _, v, u, nd, better = ev
            st["relax"] = (v, u)
            if better:
                st["labels"][u] = nd
                st["prev"][u] = v
                self.status_var.set(f"Дуга {v} → {u}: нова мітка {nd:g} – ЗМЕНШЕНО")
            else:
                self.status_var.set(f"Дуга {v} → {u}: {nd:g} не менше за поточну мітку {st['labels'].get(u, INF):g} – без змін")
        return True

    def finish(self):
        res, st = self.result, self.state
        st["current"], st["relax"] = None, None
        st["path"] = res.path
        if res.found:
            self.status_var.set("Шлях знайдено: %s км, міст у шляху: %d, ітерацій: %d" % (
                f"{res.distance:g}", len(res.path), res.iterations))
        else:
            self.status_var.set("Шлях між обраними містами відсутній")
        self.redraw()
        self.show_results()

    def run_instant(self):
        self.stop_animation()
        if not self.compute():
            return
        while self.advance():
            pass
        self.finish()

    def run_animated(self):
        self.stop_animation()
        if not self.compute():
            return
        self.paused = False
        self.redraw()
        self.anim_job = self.root.after(max(1, self.delay_var.get()), self.anim_tick)

    def anim_tick(self):
        self.anim_job = None
        if self.paused:
            return
        if self.advance():
            self.redraw()
            self.anim_job = self.root.after(max(1, self.delay_var.get()), self.anim_tick)
        else:
            self.finish()

    def toggle_pause(self):
        if not self.result or self.state.get("path"):
            return
        self.paused = not self.paused
        if not self.paused:
            self.anim_tick()

    def step_once(self):
        self.stop_animation()
        if not self.result or self.state.get("path"):
            if not self.compute():
                return
        self.paused = True
        if self.advance():
            self.redraw()
        else:
            self.finish()

    def results_text(self, res):
        s, g = self.start_var.get(), self.goal_var.get()
        unit = " км" if res.algo.startswith("Алгоритм") else " доріг"
        L = ["РЕЗУЛЬТАТ ПОШУКУ НАЙКОРОТШОГО ШЛЯХУ", "=" * 64,
             f"Метод: {res.algo}",
             f"Відправна точка: {s}        Цільова точка: {g}",
             f"Граф: міст (вершин) – {len(self.cities)}, доріг – {len(self.road_list())}", "-" * 64]
        if res.found:
            L += ["Найкоротший шлях:", "  " + " → ".join(res.path), "",
                  f"ВІДДАЛЬ: {res.distance:g} км", f"Міст у шляху: {len(res.path)}, доріг: {len(res.path) - 1}", "",
                  "Ділянки шляху:"]
            total = 0
            for a, b in zip(res.path, res.path[1:]):
                total += self.adj[a][b]
                L.append(f"  {a} → {b}: {self.adj[a][b]:g} км  (разом {total:g} км)")
        else:
            L.append("Шлях між обраними містами відсутній")
        L += ["-" * 64,
              f"Кількість ітерацій (вершин з постійною міткою): {res.iterations}",
              f"Кількість перевірених дуг: {res.relaxations}",
              f"Кількість зменшень міток: {res.updates}",
              f"Максимальний розмір черги: {res.max_queue}",
              f"Час пошуку: {res.time_ms:.4f} мс"]
        other = bfs(self.adj, s, g) if res.algo.startswith("Алгоритм") else dijkstra(self.adj, s, g)
        if other.found:
            L += ["-" * 64, f"Для порівняння – {other.algo.lower()}:",
                  "  " + " → ".join(other.path),
                  f"  віддаль {other.distance:g} км, доріг {len(other.path) - 1}, ітерацій {other.iterations}"]
        L += ["-" * 64, "Протокол роботи алгоритму (ітерація: вибрана вершина [мітка] → оновлення міток):"]
        for i, (v, d, ups) in enumerate(res.log, 1):
            u = ", ".join(f"{x}: {'∞' if o == INF else f'{o:g}'}→{n:g}" for x, o, n in ups) or "оновлень немає"
            L.append(f"  {i:2d}. {v} [{d:g}{' км' if unit == ' км' else ''}]  →  {u}")
        if res.algo.startswith("Алгоритм"):
            L += ["-" * 64, "Мітки вершин наприкінці пошуку:",
                  f"  {'Місто':<18}{'Мітка, км':>10}   {'Попереднє':<18}Статус"]
            for v in sorted(self.cities, key=lambda c: (res.dist.get(c, INF), c)):
                d = res.dist.get(v, INF)
                stt = "постійна" if v in res.closed else ("тимчасова" if d != INF else "—")
                L.append(f"  {v:<18}{('∞' if d == INF else f'{d:g}'):>10}   {res.prev.get(v, '—'):<18}{stt}")
        return "\n".join(L)

    def show_results(self):
        if not self.result:
            messagebox.showinfo("Результати", "Спочатку виконайте пошук")
            return
        if self.results_win and self.results_win.winfo_exists():
            self.results_win.destroy()
        win = tk.Toplevel(self.root)
        win.title("Результати пошуку")
        win.geometry("760x780+%d+%d" % (self.root.winfo_rootx() + 620, self.root.winfo_rooty() + 30))
        self.results_win = win
        txt = tk.Text(win, font=("Courier New", 10), wrap="word")
        sb = ttk.Scrollbar(win, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", self.results_text(self.result))
        txt.tag_add("hdr", "1.0", "1.end")
        txt.tag_configure("hdr", font=("Courier New", 12, "bold"), foreground="#0D47A1")
        idx = txt.search("ВІДДАЛЬ:", "1.0")
        if idx:
            txt.tag_add("dist", idx, f"{idx} lineend")
            txt.tag_configure("dist", font=("Courier New", 12, "bold"), foreground="#C62828")
        txt.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = DijkstraMapApp(root)
    root.mainloop()