"""
Лабораторна робота №4 з курсу «Системи штучного інтелекту»
Тема: Двонаправлений пошук на графі. Реалізація двонаправленого пошуку
у хвильовому алгоритмі для знаходження найкоротшого шляху у одиничних графах.

Одиничний граф задається матрицею-лабіринтом, де
    -1  – непрохідна вершина графу (клітинка лабіринту),
     0  – прохідна вершина графу,
     k  – номер хвилі (k >= 1), яким позначено вершину під час пошуку.

Двонаправлений пошук: одночасно запускаються дві хвилі – пряма (від
початкової вершини) та зустрічна (від цільової). Пошук завершується, коли
хвилі зустрілися; найкоротший шлях складається з двох половин.

"""

import random
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------------------------------------------------------
#  Константи
# ----------------------------------------------------------------------------
WALL = -1   # непрохідна вершина (клітинка лабіринту)
FREE = 0    # прохідна вершина

# Оператори переходу: зміщення (dr, dc) по рядках і стовпцях
ORTHO = [(-1, 0), (0, 1), (1, 0), (0, -1)]       # вверх, вправо, вниз, вліво
DIAG = [(-1, 1), (1, 1), (1, -1), (-1, -1)]      # чотири діагональні напрямки

OPERATORS = {
    "Вверх-вниз-вправо-вліво": ORTHO,
    "Перехід по діагоналях": DIAG,
    "Комбінований (прямі + діагоналі)": ORTHO + DIAG,
}
OP_SHORT = {
    "Вверх-вниз-вправо-вліво": "ORTHO-4",
    "Перехід по діагоналях": "DIAG-4",
    "Комбінований (прямі + діагоналі)": "COMB-8",
}
OP_COLORS = {
    "Вверх-вниз-вправо-вліво": "#1E88E5",
    "Перехід по діагоналях": "#FB8C00",
    "Комбінований (прямі + діагоналі)": "#43A047",
}
ALGOS = ["Двонаправлений (зустрічні хвилі)", "Однонаправлений (для порівняння)"]

# Кольори клітинок
C_WALL = "#37474F"
C_FREE = "#FFFFFF"
C_START = "#2E7D32"
C_GOAL = "#C62828"
C_FRONT_F = "#FFA726"           # фронт прямої хвилі
C_FRONT_B = "#F06292"           # фронт зустрічної хвилі
C_MEET = "#76FF03"              # точка зустрічі хвиль
C_PATH = "#FFEB3B"
C_F_LIGHT, C_F_DARK = (227, 242, 253), (30, 136, 229)    # пряма хвиля – синя
C_B_LIGHT, C_B_DARK = (243, 229, 245), (142, 36, 170)    # зустрічна – фіолетова

# Базовий (явно заданий) лабіринт 15 x 15:  '#' – стіна (-1), '.' – прохід (0)
BASE_MAZE = [
    "....#..........",
    "..#.#.#####.##.",
    ".#..#.....#..#.",
    ".#.####.#.##.#.",
    ".#......#....#.",
    ".######.####.#.",
    "......#....#...",
    "####..#.##.###.",
    "...#..#..#.....",
    ".#.#.###.#.###.",
    ".#...#...#...#.",
    ".#####.#####.#.",
    ".....#.....#.#.",
    ".###.#####.#.#.",
    "...#.......#...",
]


# ----------------------------------------------------------------------------
#  Робота з матрицею лабіринту
# ----------------------------------------------------------------------------
def maze_from_strings(lines):
    """Перетворює текстовий опис лабіринту на матрицю -1/0."""
    return [[WALL if ch == "#" else FREE for ch in line] for line in lines]


def generate_maze(rows, cols, wall_percent, seed, keep_free=()):
    """Генерує лабіринт rows x cols із точно заданою часткою непрохідних клітинок."""
    rnd = random.Random(seed)
    grid = [[FREE] * cols for _ in range(rows)]
    cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in keep_free]
    n_walls = min(len(cells), round(rows * cols * wall_percent / 100))
    for r, c in rnd.sample(cells, n_walls):
        grid[r][c] = WALL
    return grid


def resize_maze(grid, rows, cols):
    """Змінює розмір матриці, зберігаючи наявний вміст (нові клітинки = 0)."""
    new = [[FREE] * cols for _ in range(rows)]
    for r in range(min(rows, len(grid))):
        for c in range(min(cols, len(grid[0]))):
            new[r][c] = grid[r][c]
    return new


def can_move(grid, r, c, dr, dc, no_corner_cut):
    """Перевіряє допустимість застосування оператора переходу (dr, dc)."""
    rows, cols = len(grid), len(grid[0])
    nr, nc = r + dr, c + dc
    if not (0 <= nr < rows and 0 <= nc < cols):
        return False
    if grid[nr][nc] == WALL:
        return False
    if no_corner_cut and dr != 0 and dc != 0:
        if grid[r + dr][c] == WALL or grid[r][c + dc] == WALL:
            return False
    return True


def adjacency_matrix(grid, moves, no_corner_cut=False):
    """Будує матрицю суміжності одиничного графу, заданого лабіринтом.

    Повертає (список вершин [(r, c), ...], матриця 0/1 розміром V x V)."""
    verts = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != WALL]
    index = {v: i for i, v in enumerate(verts)}
    n = len(verts)
    adj = [[0] * n for _ in range(n)]
    for (r, c) in verts:
        for dr, dc in moves:
            if can_move(grid, r, c, dr, dc, no_corner_cut):
                adj[index[(r, c)]][index[(r + dr, c + dc)]] = 1
    return verts, adj


def trace_back(grid, marks, cell, moves, no_corner_cut):
    """Зворотний хід: від cell до вершини з позначкою 1 по позначках, що зменшуються."""
    rows, cols = len(grid), len(grid[0])
    path = [cell]
    r, c = cell
    while marks[r][c] > 1:
        k = marks[r][c]
        for dr, dc in moves:
            pr, pc = r - dr, c - dc
            if (0 <= pr < rows and 0 <= pc < cols and marks[pr][pc] == k - 1
                    and can_move(grid, pr, pc, dr, dc, no_corner_cut)):
                r, c = pr, pc
                path.append((r, c))
                break
    return path


# ----------------------------------------------------------------------------
#  Результати пошуку
# ----------------------------------------------------------------------------
class SearchResult:
    def __init__(self):
        self.algo = ""
        self.found = False
        self.path = []              # вершини (r, c) від старту до цілі
        self.fmarks = []            # матриця позначок прямої хвилі
        self.bmarks = None          # матриця позначок зустрічної хвилі (лише для двонаправленого)
        self.events = []            # для анімації: (сторона 'f'/'b', номер циклу, нові вершини)
        self.meet = None            # (u, v) – ребро, на якому зустрілися хвилі
        self.cycles = 0             # кількість циклів роботи
        self.steps_f = 0            # кроків прямої хвилі
        self.steps_b = 0            # кроків зустрічної хвилі
        self.expanded_f = 0
        self.expanded_b = 0
        self.labeled = 0
        self.max_front = 0
        self.time_ms = 0.0

    @property
    def expanded(self):
        return self.expanded_f + self.expanded_b

    @property
    def length(self):
        """Віддаль у кроках (кількість переходів)."""
        return len(self.path) - 1 if self.path else 0


# ----------------------------------------------------------------------------
#  Однонаправлений хвильовий пошук (з ЛР3, для порівняння)
# ----------------------------------------------------------------------------
def wave_search(grid, start, goal, moves, no_corner_cut=False):
    res = SearchResult()
    res.algo = ALGOS[1]
    t0 = time.perf_counter()
    marks = [row[:] for row in grid]
    marks[start[0]][start[1]] = 1
    front = [start]
    res.labeled = res.max_front = 1
    found = start == goal
    while front and not found:
        res.cycles += 1
        new_front = []
        for (r, c) in front:
            res.expanded_f += 1
            k = marks[r][c]
            for dr, dc in moves:
                if can_move(grid, r, c, dr, dc, no_corner_cut):
                    nr, nc = r + dr, c + dc
                    if marks[nr][nc] == FREE:
                        marks[nr][nc] = k + 1
                        new_front.append((nr, nc))
                        res.labeled += 1
                        if (nr, nc) == goal:
                            found = True
                            break
            if found:
                break
        res.events.append(("f", res.cycles, new_front))
        res.max_front = max(res.max_front, len(new_front))
        front = new_front
    res.steps_f = res.cycles
    if found:
        res.path = list(reversed(trace_back(grid, marks, goal, moves, no_corner_cut)))
    res.time_ms = (time.perf_counter() - t0) * 1000
    res.found, res.fmarks = found, marks
    return res


# ----------------------------------------------------------------------------
#  Двонаправлений хвильовий пошук
# ----------------------------------------------------------------------------
def bidirectional_wave_search(grid, start, goal, moves, no_corner_cut=False):
    """Двонаправлений хвильовий пошук від start і від goal назустріч одна одній.

    Пряма хвиля нумерує вершини у матриці F (старт = 1), зустрічна – у матриці
    B (ціль = 1). Один цикл роботи = крок прямої хвилі + крок зустрічної хвилі.
    Коли під час розкриття фронту одна хвиля натрапляє на вершину, вже позначену
    іншою хвилею, фіксується зустріч. Фронт добудовується до кінця, і з усіх
    знайдених точок дотику обирається та, що дає найменшу довжину шляху
    F[u] + B[v] - 1. Шлях = (старт ... u) + (v ... ціль).
    """
    res = SearchResult()
    res.algo = ALGOS[0]
    t0 = time.perf_counter()
    F = [row[:] for row in grid]
    B = [row[:] for row in grid]
    F[start[0]][start[1]] = 1
    B[goal[0]][goal[1]] = 1
    res.labeled = 2 if start != goal else 1
    res.max_front = 1
    if start == goal:
        res.found, res.path = True, [start]
        res.fmarks, res.bmarks = F, B
        res.time_ms = (time.perf_counter() - t0) * 1000
        return res

    ffront, bfront = [start], [goal]
    best = None                         # (довжина, u – вершина прямої хвилі, v – зустрічної)

    def expand(front, own, other, side):
        """Один крок хвилі: розкрити всі вершини фронту. Повертає (новий фронт, кандидати)."""
        new_front, cands = [], []
        for (r, c) in front:
            if side == "f":
                res.expanded_f += 1
            else:
                res.expanded_b += 1
            k = own[r][c]
            for dr, dc in moves:
                if not can_move(grid, r, c, dr, dc, no_corner_cut):
                    continue
                nr, nc = r + dr, c + dc
                if other[nr][nc] > 0:                       # хвилі зустрілися
                    length = k + other[nr][nc] - 1
                    if side == "f":
                        cands.append((length, (r, c), (nr, nc)))
                    else:
                        cands.append((length, (nr, nc), (r, c)))
                elif own[nr][nc] == FREE:
                    own[nr][nc] = k + 1
                    new_front.append((nr, nc))
                    res.labeled += 1
        return new_front, cands

    while ffront and bfront and best is None:
        res.cycles += 1
        # ---- крок прямої хвилі
        ffront, cands = expand(ffront, F, B, "f")
        res.steps_f += 1
        res.events.append(("f", res.cycles, ffront))
        res.max_front = max(res.max_front, len(ffront))
        if cands:
            best = min(cands)
            break
        if not ffront:
            break
        # ---- крок зустрічної хвилі
        bfront, cands = expand(bfront, B, F, "b")
        res.steps_b += 1
        res.events.append(("b", res.cycles, bfront))
        res.max_front = max(res.max_front, len(bfront))
        if cands:
            best = min(cands)

    if best:
        _, u, v = best
        first = list(reversed(trace_back(grid, F, u, moves, no_corner_cut)))   # старт ... u
        second = trace_back(grid, B, v, moves, no_corner_cut)                   # v ... ціль
        res.path = first + second
        res.meet = (u, v)
        res.found = True
    res.time_ms = (time.perf_counter() - t0) * 1000
    res.fmarks, res.bmarks = F, B
    return res


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return "#%02X%02X%02X" % tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def run_search(algo, grid, start, goal, moves, no_corner_cut):
    if algo == ALGOS[0]:
        return bidirectional_wave_search(grid, start, goal, moves, no_corner_cut)
    return wave_search(grid, start, goal, moves, no_corner_cut)


# ----------------------------------------------------------------------------
#  Графічний інтерфейс
# ----------------------------------------------------------------------------
class BiWaveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Системи ШІ - Лабораторна 4 (Двонаправлений пошук) - Романа Муцак (ФЕІ-42)")
        self.root.geometry("1320x860")

        self.grid = maze_from_strings(BASE_MAZE)
        self.start = (0, 0)
        self.goal = (14, 14)

        self.result = None
        self.disp_f = None          # позначки прямої хвилі, вже показані на полі
        self.disp_b = None          # позначки зустрічної хвилі, вже показані на полі
        self.front_f, self.front_b = set(), set()
        self.path_cells, self.meet_cells = set(), set()
        self.max_f = self.max_b = 1
        self.anim_step = 0
        self.anim_job = None
        self.paused = False
        self.drag_value = None
        self.results_win = None

        self.setup_ui()
        self.draw_grid()

    # ------------------------------------------------------------ інтерфейс
    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("Arial", 10, "bold"))
        style.configure("TButton", font=("Arial", 9))

        left = ttk.Frame(self.root, padding=6)
        left.pack(side=tk.LEFT, fill=tk.Y)
        right = ttk.Frame(self.root, padding=6)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- параметри графу
        f1 = ttk.LabelFrame(left, text="Параметри графу (матриці-лабіринту)", padding=6)
        f1.pack(fill=tk.X, pady=3)
        self.rows_var, self.cols_var = tk.IntVar(value=15), tk.IntVar(value=15)
        self.wall_var, self.seed_var = tk.IntVar(value=30), tk.IntVar(value=42)
        ttk.Label(f1, text="Рядків:").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(f1, from_=3, to=30, width=5, textvariable=self.rows_var).grid(row=0, column=1, sticky="w")
        ttk.Label(f1, text="Стовпців:").grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Spinbox(f1, from_=3, to=30, width=5, textvariable=self.cols_var).grid(row=0, column=3, sticky="w")
        ttk.Label(f1, text="Частка стін, %:").grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Scale(f1, from_=0, to=70, variable=self.wall_var, orient=tk.HORIZONTAL,
                  command=lambda v: self.wall_var.set(int(float(v)))).grid(row=1, column=2, columnspan=2, sticky="we")
        ttk.Label(f1, textvariable=self.wall_var, width=3).grid(row=1, column=4)
        ttk.Label(f1, text="Seed:").grid(row=2, column=0, sticky="w")
        ttk.Entry(f1, width=7, textvariable=self.seed_var).grid(row=2, column=1, sticky="w")
        ttk.Button(f1, text="Змінити розмір", command=self.apply_size).grid(row=2, column=2, columnspan=3, sticky="we", pady=2)
        ttk.Button(f1, text="Згенерувати лабіринт", command=self.generate).grid(row=3, column=0, columnspan=2, sticky="we", pady=2)
        ttk.Button(f1, text="Базовий лабіринт", command=self.load_base).grid(row=3, column=2, columnspan=3, sticky="we", pady=2)
        ttk.Button(f1, text="Очистити (усі 0)", command=self.clear_walls).grid(row=4, column=0, columnspan=2, sticky="we")
        ttk.Button(f1, text="Матриця суміжності", command=self.show_adjacency).grid(row=4, column=2, columnspan=3, sticky="we")

        # --- вершини
        f2 = ttk.LabelFrame(left, text="Початкова та цільова вершини", padding=6)
        f2.pack(fill=tk.X, pady=3)
        self.sr_var, self.sc_var = tk.IntVar(value=0), tk.IntVar(value=0)
        self.gr_var, self.gc_var = tk.IntVar(value=14), tk.IntVar(value=14)
        ttk.Label(f2, text="Початкова (рядок, стовпець):").grid(row=0, column=0, sticky="w")
        ttk.Entry(f2, width=4, textvariable=self.sr_var).grid(row=0, column=1)
        ttk.Entry(f2, width=4, textvariable=self.sc_var).grid(row=0, column=2)
        ttk.Label(f2, text="Цільова (рядок, стовпець):").grid(row=1, column=0, sticky="w")
        ttk.Entry(f2, width=4, textvariable=self.gr_var).grid(row=1, column=1)
        ttk.Entry(f2, width=4, textvariable=self.gc_var).grid(row=1, column=2)
        ttk.Button(f2, text="Застосувати вершини", command=self.apply_points).grid(row=2, column=0, sticky="we", pady=2)
        ttk.Button(f2, text="Поміняти місцями", command=self.swap_points).grid(row=2, column=1, columnspan=2, sticky="we", pady=2)
        ttk.Label(f2, text="Клік мишею по полю задає:").grid(row=3, column=0, columnspan=3, sticky="w")
        self.click_mode = tk.StringVar(value="wall")
        rf = ttk.Frame(f2)
        rf.grid(row=4, column=0, columnspan=3, sticky="w")
        for t, v in (("стіну (-1/0)", "wall"), ("початкову", "start"), ("цільову", "goal")):
            ttk.Radiobutton(rf, text=t, value=v, variable=self.click_mode).pack(side=tk.LEFT)

        # --- метод пошуку та оператор переходу
        f3 = ttk.LabelFrame(left, text="Метод пошуку та оператор переходу", padding=6)
        f3.pack(fill=tk.X, pady=3)
        self.algo_var = tk.StringVar(value=ALGOS[0])
        for a in ALGOS:
            ttk.Radiobutton(f3, text=a, value=a, variable=self.algo_var, command=self.reset_wave).pack(anchor="w")
        ttk.Separator(f3).pack(fill=tk.X, pady=3)
        self.op_var = tk.StringVar(value=list(OPERATORS)[0])
        for name in OPERATORS:
            ttk.Radiobutton(f3, text=name, value=name, variable=self.op_var, command=self.reset_wave).pack(anchor="w")
        self.nocut_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f3, text="Заборонити зрізання кутів (діагоналі)", variable=self.nocut_var,
                        command=self.reset_wave).pack(anchor="w", pady=(3, 0))

        # --- візуалізація
        f4 = ttk.LabelFrame(left, text="Візуалізація", padding=6)
        f4.pack(fill=tk.X, pady=3)
        self.delay_var = tk.IntVar(value=200)
        ttk.Label(f4, text="Затримка, мс:").grid(row=0, column=0, sticky="w")
        ttk.Scale(f4, from_=0, to=1000, variable=self.delay_var, orient=tk.HORIZONTAL, length=150,
                  command=lambda v: self.delay_var.set(int(float(v)))).grid(row=0, column=1, sticky="we")
        ttk.Label(f4, textvariable=self.delay_var, width=4).grid(row=0, column=2)
        self.values_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f4, text="Показувати значення клітинок (-1 / 0 / k)", variable=self.values_var,
                        command=self.redraw_cells).grid(row=1, column=0, columnspan=3, sticky="w")

        # --- керування
        f5 = ttk.LabelFrame(left, text="Керування пошуком", padding=6)
        f5.pack(fill=tk.X, pady=3)
        btns = [("▶ Пуск (з анімацією)", self.run_animated), ("⚡ Миттєвий пошук", self.run_instant),
                ("⏸ Пауза / продовжити", self.toggle_pause), ("⏭ Крок хвилі", self.step_once),
                ("↺ Скинути хвилі", self.reset_wave), ("📋 Результати", self.show_results)]
        for i, (t, cmd) in enumerate(btns):
            ttk.Button(f5, text=t, command=cmd).grid(row=i // 2, column=i % 2, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="Порівняти оператори та методи", command=self.compare).grid(
            row=3, column=0, columnspan=2, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="Дослідження: розмір і щільність", command=self.open_research).grid(
            row=4, column=0, columnspan=2, sticky="we", padx=1, pady=1)
        f5.columnconfigure(0, weight=1)
        f5.columnconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Готово. Оберіть параметри та натисніть «Пуск».")
        ttk.Label(left, textvariable=self.status_var, wraplength=340, foreground="#0D47A1",
                  font=("Arial", 9, "bold")).pack(fill=tk.X, pady=6)

        # --- полотно
        self.canvas = tk.Canvas(right, bg="#FAFAFA", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag_value", None))
        self.canvas.bind("<Configure>", lambda e: self.draw_grid())

        # --- легенда
        items = [(C_WALL, "непрохідна (-1)"), (C_FREE, "прохідна (0)"), (C_START, "початкова (П)"),
                 (C_GOAL, "цільова (Ц)"), (C_PATH, "найкоротший шлях"),
                 ("#90CAF9", "пряма хвиля (від П)"), ("#CE93D8", "зустрічна хвиля (від Ц)"),
                 (C_FRONT_F, "фронт прямої"), (C_FRONT_B, "фронт зустрічної"), (C_MEET, "зустріч хвиль")]
        for row_items in (items[:5], items[5:]):
            lg = ttk.Frame(right)
            lg.pack(fill=tk.X, pady=(3, 0))
            for color, text in row_items:
                tk.Label(lg, bg=color, width=2, relief="solid", bd=1).pack(side=tk.LEFT, padx=(8, 2))
                ttk.Label(lg, text=text).pack(side=tk.LEFT)

    # ------------------------------------------------------------ малювання
    def cell_geometry(self):
        rows, cols = len(self.grid), len(self.grid[0])
        w = max(self.canvas.winfo_width(), 200)
        h = max(self.canvas.winfo_height(), 200)
        margin = 26
        size = int(min((w - margin - 6) / cols, (h - margin - 6) / rows))
        return max(8, min(size, 48)), margin, margin

    def draw_grid(self):
        self.canvas.delete("all")
        rows, cols = len(self.grid), len(self.grid[0])
        size, ox, oy = self.cell_geometry()
        self.cell_size, self.ox, self.oy = size, ox, oy
        font_idx = ("Arial", max(7, min(10, size // 3)))
        for c in range(cols):
            self.canvas.create_text(ox + c * size + size / 2, oy - 12, text=str(c), font=font_idx, fill="#555")
        for r in range(rows):
            self.canvas.create_text(ox - 12, oy + r * size + size / 2, text=str(r), font=font_idx, fill="#555")
        self.rects = [[None] * cols for _ in range(rows)]
        self.texts = [[None] * cols for _ in range(rows)]
        self.cell_font = ("Arial", max(6, min(12, int(size / 2.8))), "bold")
        for r in range(rows):
            for c in range(cols):
                x0, y0 = ox + c * size, oy + r * size
                self.rects[r][c] = self.canvas.create_rectangle(x0, y0, x0 + size, y0 + size, outline="#B0BEC5")
                self.texts[r][c] = self.canvas.create_text(x0 + size / 2, y0 + size / 2, font=self.cell_font)
        self.redraw_cells()

    def redraw_cells(self):
        for r in range(len(self.grid)):
            for c in range(len(self.grid[0])):
                self.refresh_cell(r, c)
        self.draw_path_line()

    def refresh_cell(self, r, c):
        val = self.grid[r][c]
        fm = self.disp_f[r][c] if self.disp_f else 0
        bm = self.disp_b[r][c] if self.disp_b else 0
        if (r, c) == self.start:
            fill, text, fg = C_START, "П", "white"
        elif (r, c) == self.goal:
            fill, text, fg = C_GOAL, "Ц", "white"
        elif val == WALL:
            fill, text, fg = C_WALL, "-1", "#CFD8DC"
        elif fm > 0 or bm > 0:
            text = str(fm if fm > 0 else bm)
            fg = "black"
            if (r, c) in self.meet_cells:
                fill = C_MEET
            elif (r, c) in self.path_cells:
                fill = C_PATH
            elif (r, c) in self.front_f:
                fill = C_FRONT_F
            elif (r, c) in self.front_b:
                fill = C_FRONT_B
            elif fm > 0:
                t = (fm - 1) / max(1, self.max_f - 1)
                fill = lerp_color(C_F_LIGHT, C_F_DARK, 0.15 + 0.85 * t)
                fg = "white" if t > 0.55 else "black"
            else:
                t = (bm - 1) / max(1, self.max_b - 1)
                fill = lerp_color(C_B_LIGHT, C_B_DARK, 0.15 + 0.85 * t)
                fg = "white" if t > 0.55 else "black"
        else:
            fill, text, fg = C_FREE, "0", "#9E9E9E"
        if not self.values_var.get() and text not in ("П", "Ц"):
            text = ""
        self.canvas.itemconfigure(self.rects[r][c], fill=fill)
        self.canvas.itemconfigure(self.texts[r][c], text=text, fill=fg)

    def cell_center(self, r, c):
        s = self.cell_size
        return self.ox + c * s + s / 2, self.oy + r * s + s / 2

    def draw_path_line(self):
        self.canvas.delete("pathline")
        if self.result and self.result.found and self.path_cells and len(self.result.path) > 1:
            pts = []
            for r, c in self.result.path:
                pts.extend(self.cell_center(r, c))
            self.canvas.create_line(*pts, fill="#D50000", width=max(2, self.cell_size // 9),
                                    tag="pathline", capstyle=tk.ROUND, joinstyle=tk.ROUND)

    # ------------------------------------------------------------ редагування
    def event_cell(self, event):
        s = self.cell_size
        c = int((event.x - self.ox) // s)
        r = int((event.y - self.oy) // s)
        if 0 <= r < len(self.grid) and 0 <= c < len(self.grid[0]):
            return r, c
        return None

    def on_click(self, event):
        cell = self.event_cell(event)
        if not cell:
            return
        r, c = cell
        mode = self.click_mode.get()
        if mode == "wall":
            if cell in (self.start, self.goal):
                return
            self.drag_value = FREE if self.grid[r][c] == WALL else WALL
            self.grid[r][c] = self.drag_value
        elif self.grid[r][c] != WALL:
            if mode == "start" and cell != self.goal:
                self.start = cell
            elif mode == "goal" and cell != self.start:
                self.goal = cell
            self.sync_point_vars()
        self.reset_wave()

    def on_drag(self, event):
        if self.click_mode.get() != "wall" or self.drag_value is None:
            return
        cell = self.event_cell(event)
        if cell and cell not in (self.start, self.goal) and self.grid[cell[0]][cell[1]] != self.drag_value:
            self.grid[cell[0]][cell[1]] = self.drag_value
            self.reset_wave()

    def sync_point_vars(self):
        self.sr_var.set(self.start[0]); self.sc_var.set(self.start[1])
        self.gr_var.set(self.goal[0]); self.gc_var.set(self.goal[1])

    def read_point_vars(self):
        """Зчитує координати з полів (якщо вони коректні) у self.start / self.goal."""
        try:
            s = (int(self.sr_var.get()), int(self.sc_var.get()))
            g = (int(self.gr_var.get()), int(self.gc_var.get()))
        except (tk.TclError, ValueError):
            return
        if s != g:
            self.start, self.goal = s, g

    def fix_points(self):
        rows, cols = len(self.grid), len(self.grid[0])
        self.start = (min(max(self.start[0], 0), rows - 1), min(max(self.start[1], 0), cols - 1))
        self.goal = (min(max(self.goal[0], 0), rows - 1), min(max(self.goal[1], 0), cols - 1))
        for r, c in (self.start, self.goal):
            self.grid[r][c] = FREE
        self.sync_point_vars()

    def read_size(self):
        try:
            rows, cols = int(self.rows_var.get()), int(self.cols_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Помилка", "Некоректний розмір матриці")
            return None
        return max(3, min(30, rows)), max(3, min(30, cols))

    def apply_size(self):
        size = self.read_size()
        if not size:
            return
        self.read_point_vars()
        self.grid = resize_maze(self.grid, *size)
        self.fix_points()
        self.full_reset()

    def generate(self):
        size = self.read_size()
        if not size:
            return
        rows, cols = size
        self.read_point_vars()          # координати беруться прямо з полів
        self.start = (min(self.start[0], rows - 1), min(self.start[1], cols - 1))
        self.goal = (min(self.goal[0], rows - 1), min(self.goal[1], cols - 1))
        self.grid = generate_maze(rows, cols, self.wall_var.get(), self.seed_var.get(),
                                  keep_free=(self.start, self.goal))
        self.fix_points()
        self.full_reset()

    def load_base(self):
        self.grid = maze_from_strings(BASE_MAZE)
        self.rows_var.set(len(self.grid)); self.cols_var.set(len(self.grid[0]))
        self.start, self.goal = (0, 0), (14, 14)
        self.sync_point_vars()
        self.full_reset()

    def clear_walls(self):
        self.grid = [[FREE] * len(self.grid[0]) for _ in self.grid]
        self.full_reset()

    def apply_points(self):
        rows, cols = len(self.grid), len(self.grid[0])
        try:
            s = (int(self.sr_var.get()), int(self.sc_var.get()))
            g = (int(self.gr_var.get()), int(self.gc_var.get()))
        except (tk.TclError, ValueError):
            messagebox.showerror("Помилка", "Координати мають бути цілими числами")
            return
        for p in (s, g):
            if not (0 <= p[0] < rows and 0 <= p[1] < cols):
                messagebox.showerror("Помилка", f"Вершина {p} поза межами матриці {rows}×{cols}")
                return
            if self.grid[p[0]][p[1]] == WALL:
                messagebox.showerror("Помилка", f"Вершина {p} непрохідна (-1)")
                return
        if s == g:
            messagebox.showwarning("Увага", "Початкова і цільова вершини збігаються")
        self.start, self.goal = s, g
        self.reset_wave()

    def swap_points(self):
        self.start, self.goal = self.goal, self.start
        self.sync_point_vars()
        self.reset_wave()

    # ------------------------------------------------------------ пошук та анімація
    def stop_animation(self):
        if self.anim_job:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None

    def reset_wave(self):
        self.stop_animation()
        self.result = None
        self.disp_f = self.disp_b = None
        self.front_f, self.front_b = set(), set()
        self.path_cells, self.meet_cells = set(), set()
        self.anim_step = 0
        self.paused = False
        self.redraw_cells()
        self.status_var.set("Хвилі скинуто. Граф: %d×%d, вершин: %d, стін: %d." % (
            len(self.grid), len(self.grid[0]), sum(v != WALL for row in self.grid for v in row),
            sum(v == WALL for row in self.grid for v in row)))

    def full_reset(self):
        self.stop_animation()
        self.result = None
        self.disp_f = self.disp_b = None
        self.draw_grid()
        self.reset_wave()

    def compute(self):
        moves = OPERATORS[self.op_var.get()]
        self.result = run_search(self.algo_var.get(), self.grid, self.start, self.goal, moves, self.nocut_var.get())
        res = self.result
        self.max_f = max(max(row) for row in res.fmarks)
        self.max_b = max(max(row) for row in res.bmarks) if res.bmarks else 1
        self.disp_f = [[v if v < 0 else 0 for v in row] for row in self.grid]
        self.disp_b = [[v if v < 0 else 0 for v in row] for row in self.grid]
        self.disp_f[self.start[0]][self.start[1]] = 1
        if res.bmarks:
            self.disp_b[self.goal[0]][self.goal[1]] = 1
        self.front_f, self.front_b = set(), set()
        self.path_cells, self.meet_cells = set(), set()
        self.anim_step = 0

    def run_instant(self):
        self.stop_animation()
        self.compute()
        while self.advance(update_status=False):
            pass
        self.finish()

    def run_animated(self):
        self.stop_animation()
        self.compute()
        self.paused = False
        self.redraw_cells()
        self.anim_job = self.root.after(max(1, self.delay_var.get()), self.anim_tick)

    def advance(self, update_status=True):
        """Показує наступний крок хвилі (прямої або зустрічної)."""
        res = self.result
        if self.anim_step >= len(res.events):
            return False
        side, cycle, cells = res.events[self.anim_step]
        marks, disp = (res.fmarks, self.disp_f) if side == "f" else (res.bmarks, self.disp_b)
        changed = set(self.front_f) | set(self.front_b)
        if side == "f":
            self.front_f = set(cells)
        else:
            self.front_b = set(cells)
        for r, c in cells:
            disp[r][c] = marks[r][c]
        if update_status:
            for r, c in changed | set(cells):
                self.refresh_cell(r, c)
            name = "пряма хвиля (від П)" if side == "f" else "зустрічна хвиля (від Ц)"
            self.status_var.set("Цикл %d з %d: %s, нових вершин у фронті: %d" % (cycle, res.cycles, name, len(cells)))
        self.anim_step += 1
        return True

    def anim_tick(self):
        self.anim_job = None
        if self.paused:
            return
        if self.advance():
            self.anim_job = self.root.after(max(1, self.delay_var.get()), self.anim_tick)
        else:
            self.finish()

    def toggle_pause(self):
        if not self.result or self.path_cells:
            return
        self.paused = not self.paused
        if not self.paused:
            self.anim_tick()
        else:
            self.status_var.set(self.status_var.get() + "  [пауза]")

    def step_once(self):
        self.stop_animation()
        if not self.result or self.path_cells or self.meet_cells:
            self.compute()
            self.redraw_cells()
        self.paused = True
        if not self.advance():
            self.finish()

    def finish(self):
        res = self.result
        self.front_f, self.front_b = set(), set()
        self.path_cells = set(res.path)
        self.meet_cells = set(res.meet) if res.meet else set()
        self.redraw_cells()
        if res.found:
            self.status_var.set("Шлях знайдено: %d кроків (%d вершин), циклів: %d, розкрито: %d, час: %.3f мс" % (
                res.length, len(res.path), res.cycles, res.expanded, res.time_ms))
        else:
            self.status_var.set("Шлях НЕ знайдено: хвиля згасла після %d циклів (розкрито %d вершин)" % (
                res.cycles, res.expanded))
        self.show_results()

    # ------------------------------------------------------------ вікно результатів
    def matrix_lines(self, marks, path):
        lines = []
        for r, row in enumerate(marks):
            lines.append("".join((f"[{v}]" if (r, c) in path and v > 0 else str(v)).rjust(5)
                                 for c, v in enumerate(row)))
        return lines

    def results_text(self, res):
        rows, cols = len(self.grid), len(self.grid[0])
        walls = sum(v == WALL for row in self.grid for v in row)
        moves = OPERATORS[self.op_var.get()]
        L = [
            "РЕЗУЛЬТАТИ ПОШУКУ НАЙКОРОТШОГО ШЛЯХУ",
            "=" * 60,
            f"Метод: {res.algo}",
            f"Оператор переходу: {self.op_var.get()}",
            f"Зрізання кутів по діагоналі: {'заборонено' if self.nocut_var.get() else 'дозволено'}",
            f"Матриця-лабіринт: {rows} × {cols};  вершин графу (0): {rows * cols - walls},  стін (-1): {walls}",
            f"Початкова вершина: {self.start}     Цільова вершина: {self.goal}",
            "-" * 60,
            f"Шлях знайдено: {'ТАК' if res.found else 'НІ'}",
        ]
        if res.found:
            L += [f"Віддаль між вершинами: {res.length} кроків (переходів)",
                  f"Кількість вершин у шляху: {len(res.path)}"]
            if res.meet:
                u, v = res.meet
                L.append(f"Точка зустрічі хвиль: {u} (пряма, k={res.fmarks[u[0]][u[1]]}) — "
                         f"{v} (зустрічна, k={res.bmarks[v[0]][v[1]]})")
        L += [f"Кількість циклів роботи: {res.cycles}",
              f"   кроків прямої хвилі: {res.steps_f},  кроків зустрічної хвилі: {res.steps_b}",
              f"Кількість розкритих вершин: {res.expanded}"
              + (f"  (пряма: {res.expanded_f}, зустрічна: {res.expanded_b})" if res.bmarks else ""),
              f"Кількість позначених вершин: {res.labeled}",
              f"Максимальний розмір фронту: {res.max_front}",
              f"Час пошуку: {res.time_ms:.4f} мс"]
        # порівняння з іншим методом на цьому ж графі
        other_algo = ALGOS[1] if res.bmarks is not None else ALGOS[0]
        o = run_search(other_algo, self.grid, self.start, self.goal, moves, self.nocut_var.get())
        L += ["-" * 60, f"Для порівняння — {other_algo.split(' (')[0].lower()} пошук на тому ж графі:",
              f"   довжина: {o.length if o.found else '—'},  циклів: {o.cycles},  розкрито: {o.expanded},  "
              f"позначено: {o.labeled},  час: {o.time_ms:.4f} мс"]
        if res.bmarks is not None and res.expanded:
            L.append(f"   виграш двонаправленого пошуку за розкритими вершинами: у {o.expanded / res.expanded:.2f} раза")
        L += ["-" * 60, "Координати вершин найкоротшого шляху (рядок, стовпець):"]
        if res.found:
            ch = [f"({p[0]},{p[1]})" for p in res.path]
            for i in range(0, len(ch), 7):
                L.append("  " + " → ".join(ch[i:i + 7]))
        else:
            L.append("  шлях відсутній — цільова вершина недосяжна")
        path = set(res.path)
        L += ["-" * 60, "Матриця позначок прямої хвилі (від початкової вершини)",
              "(-1 – стіна, 0 – не досягнута, k – номер хвилі, [k] – вершина шляху):"]
        L += self.matrix_lines(res.fmarks, path)
        if res.bmarks is not None:
            L += ["", "Матриця позначок зустрічної хвилі (від цільової вершини):"]
            L += self.matrix_lines(res.bmarks, path)
        return "\n".join(L)

    def show_results(self):
        if not self.result:
            messagebox.showinfo("Результати", "Спочатку виконайте пошук")
            return
        if self.results_win and self.results_win.winfo_exists():
            self.results_win.destroy()
        win = tk.Toplevel(self.root)
        win.title("Результати пошуку")
        win.geometry("720x760+%d+%d" % (self.root.winfo_rootx() + 600, self.root.winfo_rooty() + 30))
        self.results_win = win
        txt = tk.Text(win, font=("Courier New", 10), wrap="none")
        sb = ttk.Scrollbar(win, command=txt.yview)
        sbx = ttk.Scrollbar(win, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=sb.set, xscrollcommand=sbx.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        sbx.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", self.results_text(self.result))
        txt.tag_add("hdr", "1.0", "1.end")
        txt.tag_configure("hdr", font=("Courier New", 11, "bold"), foreground="#0D47A1")
        txt.configure(state="disabled")

    # ------------------------------------------------------------ матриця суміжності
    def show_adjacency(self):
        moves = OPERATORS[self.op_var.get()]
        verts, adj = adjacency_matrix(self.grid, moves, self.nocut_var.get())
        names = [f"v{i + 1}" for i in range(len(verts))]
        edges = sum(map(sum, adj)) // 2
        win = tk.Toplevel(self.root)
        win.title("Матриця суміжності графу")
        win.geometry("900x620")
        L = [f"Оператор переходу: {self.op_var.get()}",
             f"Порядок графу (кількість вершин): {len(verts)};  розмір графу (кількість ребер): {edges}",
             "Вершини графу (прохідні клітинки матриці-лабіринту):"]
        row = []
        for i, v in enumerate(verts):
            row.append(f"{names[i]}={v}")
            if len(row) == 8:
                L.append("  " + "  ".join(row)); row = []
        if row:
            L.append("  " + "  ".join(row))
        w = max(len(n) for n in names) + 1 if names else 3
        L += ["", "Матриця суміжності (1 – вершини з'єднані ребром, 0 – не з'єднані):", "",
              " " * w + "".join(n.rjust(w) for n in names)]
        for i, n in enumerate(names):
            L.append(n.rjust(w) + "".join(str(x).rjust(w) for x in adj[i]))
        txt = tk.Text(win, font=("Courier New", 10), wrap="none")
        sb = ttk.Scrollbar(win, command=txt.yview)
        sbx = ttk.Scrollbar(win, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=sb.set, xscrollcommand=sbx.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        sbx.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", "\n".join(L))
        txt.configure(state="disabled")

    # ------------------------------------------------------------ порівняння
    def compare(self):
        win = tk.Toplevel(self.root)
        win.title("Порівняння операторів переходу та методів пошуку на поточному графі")
        win.geometry("1100x900")
        cols = ("algo", "op", "found", "len", "cyc", "exp", "lab", "front", "time")
        heads = ("Метод", "Оператор", "Знайдено", "Довжина", "Циклів", "Розкрито", "Позначено", "Макс. фронт", "Час, мс")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=6)
        for c, h in zip(cols, heads):
            tree.heading(c, text=h)
            tree.column(c, width={"algo": 150, "op": 230}.get(c, 90), anchor="center")
        tree.pack(fill=tk.X, padx=6, pady=6)
        maps = ttk.Frame(win)
        maps.pack(fill=tk.BOTH, expand=True)
        rows, ncols = len(self.grid), len(self.grid[0])
        size = max(5, min(20, 300 // max(rows, ncols)))
        for ai, algo in enumerate(ALGOS):
            for oi, name in enumerate(OPERATORS):
                res = run_search(algo, self.grid, self.start, self.goal, OPERATORS[name], self.nocut_var.get())
                tree.insert("", tk.END, values=(algo.split(" (")[0], name, "так" if res.found else "ні",
                                                res.length if res.found else "—", res.cycles, res.expanded,
                                                res.labeled, res.max_front, f"{res.time_ms:.4f}"))
                fr = ttk.Frame(maps)
                fr.grid(row=ai, column=oi, padx=8, pady=2, sticky="n")
                ttk.Label(fr, text=f"{algo.split(' (')[0]} · {OP_SHORT[name]}", foreground=OP_COLORS[name],
                          font=("Arial", 10, "bold")).pack()
                cv = tk.Canvas(fr, width=ncols * size + 2, height=rows * size + 2, bg="white", highlightthickness=0)
                cv.pack()
                self.draw_mini(cv, res, size)
                ttk.Label(fr, text=("Довжина: %d, розкрито: %d, циклів: %d" % (res.length, res.expanded, res.cycles))
                          if res.found else "Шлях не знайдено (розкрито: %d)" % res.expanded).pack()

    def draw_mini(self, cv, res, size):
        mf = max(max(row) for row in res.fmarks)
        mb = max(max(row) for row in res.bmarks) if res.bmarks else 1
        path = set(res.path)
        meet = set(res.meet) if res.meet else set()
        for r, row in enumerate(res.fmarks):
            for c, v in enumerate(row):
                b = res.bmarks[r][c] if res.bmarks else 0
                if (r, c) == self.start:
                    fill = C_START
                elif (r, c) == self.goal:
                    fill = C_GOAL
                elif v == WALL:
                    fill = C_WALL
                elif (r, c) in meet:
                    fill = C_MEET
                elif (r, c) in path:
                    fill = C_PATH
                elif v > 0:
                    fill = lerp_color(C_F_LIGHT, C_F_DARK, 0.15 + 0.85 * (v - 1) / max(1, mf - 1))
                elif b > 0:
                    fill = lerp_color(C_B_LIGHT, C_B_DARK, 0.15 + 0.85 * (b - 1) / max(1, mb - 1))
                else:
                    fill = C_FREE
                cv.create_rectangle(1 + c * size, 1 + r * size, 1 + (c + 1) * size, 1 + (r + 1) * size,
                                    fill=fill, outline="#B0BEC5")
        if res.found and len(res.path) > 1:
            pts = []
            for r, c in res.path:
                pts += [1 + c * size + size / 2, 1 + r * size + size / 2]
            cv.create_line(*pts, fill="#D50000", width=2)

    def open_research(self):
        ResearchWindow(self.root, self.nocut_var.get())


class ResearchWindow:
    """Серійні досліди: двонаправлений і однонаправлений пошук на однакових лабіринтах."""

    METRICS = {
        "Розкрито вершин (середнє)": "exp",
        "Кількість циклів (середня)": "cyc",
        "Довжина шляху (середня)": "len",
        "Частка успішних пошуків, %": "succ",
        "Час пошуку, мс (середній)": "time",
        "Виграш: розкрито одно / розкрито дво": "gain",
    }

    def __init__(self, root, no_corner_cut):
        self.no_corner_cut = no_corner_cut
        self.win = tk.Toplevel(root)
        self.win.title("Дослідження: двонаправлений та однонаправлений пошук на графах різного розміру і щільності")
        self.win.geometry("1180x900")
        top = ttk.Frame(self.win, padding=6)
        top.pack(fill=tk.X)
        self.mode = tk.StringVar(value="Розмір графу N×N")
        self.sizes = tk.StringVar(value="10,12,14,16,18,20")
        self.fixed_density = tk.IntVar(value=25)
        self.densities = tk.StringVar(value="0,10,20,30,40,50")
        self.fixed_size = tk.IntVar(value=15)
        self.trials = tk.IntVar(value=30)
        self.seed = tk.IntVar(value=1)
        self.metric = tk.StringVar(value=list(self.METRICS)[0])
        ttk.Label(top, text="Змінний параметр:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(top, textvariable=self.mode, state="readonly", width=26,
                     values=["Розмір графу N×N", "Частка непрохідних клітинок"]).grid(row=0, column=1, sticky="w")
        ttk.Label(top, text="Розміри N:").grid(row=0, column=2, padx=(10, 0))
        ttk.Entry(top, textvariable=self.sizes, width=18).grid(row=0, column=3)
        ttk.Label(top, text="при частці стін, %:").grid(row=0, column=4, padx=(6, 0))
        ttk.Entry(top, textvariable=self.fixed_density, width=5).grid(row=0, column=5)
        ttk.Label(top, text="Частки стін, %:").grid(row=1, column=2, padx=(10, 0))
        ttk.Entry(top, textvariable=self.densities, width=18).grid(row=1, column=3)
        ttk.Label(top, text="при розмірі N:").grid(row=1, column=4, padx=(6, 0))
        ttk.Entry(top, textvariable=self.fixed_size, width=5).grid(row=1, column=5)
        ttk.Label(top, text="Лабіринтів на точку:").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.trials, width=6).grid(row=1, column=1, sticky="w")
        ttk.Label(top, text="Seed:").grid(row=0, column=6, padx=(10, 0))
        ttk.Entry(top, textvariable=self.seed, width=6).grid(row=0, column=7)
        ttk.Button(top, text="▶ Виконати серію", command=self.run).grid(row=1, column=6, columnspan=2, padx=(10, 0), sticky="we")
        ttk.Label(top, text="Графік:").grid(row=0, column=8, padx=(14, 0))
        cb = ttk.Combobox(top, textvariable=self.metric, state="readonly", width=34, values=list(self.METRICS))
        cb.grid(row=0, column=9)
        cb.bind("<<ComboboxSelected>>", lambda e: self.plot())

        cols = ("x", "op", "succ", "len", "cyc_b", "cyc_u", "exp_b", "exp_u", "gain")
        heads = ("Значення", "Оператор", "Успіх, %", "Сер. довжина", "Циклів дво", "Циклів одно",
                 "Розкрито дво", "Розкрито одно", "Виграш, раз")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings", height=18)
        for c, h in zip(cols, heads):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=230 if c == "op" else 105, anchor="center")
        self.tree.pack(fill=tk.X, padx=6)
        self.chart = tk.Canvas(self.win, bg="white", height=400)
        self.chart.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.data = None

    @staticmethod
    def parse_list(s):
        return [int(x) for x in s.replace(";", ",").split(",") if x.strip()]

    def run(self):
        try:
            by_size = self.mode.get().startswith("Розмір")
            xs = self.parse_list(self.sizes.get() if by_size else self.densities.get())
            trials, seed = int(self.trials.get()), int(self.seed.get())
            fixed_d, fixed_n = int(self.fixed_density.get()), int(self.fixed_size.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Помилка", "Некоректні параметри серії", parent=self.win)
            return
        self.xs, self.by_size = xs, by_size
        keys = ("succ", "len", "cyc", "exp", "time")
        self.data = {(a, n): {k: [] for k in keys} for a in ALGOS for n in OPERATORS}
        for i in self.tree.get_children():
            self.tree.delete(i)
        for x in xs:
            n, d = (x, fixed_d) if by_size else (fixed_n, x)
            start, goal = (0, 0), (n - 1, n - 1)
            grids = [generate_maze(n, n, d, seed + t, keep_free=(start, goal)) for t in range(trials)]
            for name, moves in OPERATORS.items():
                row = {}
                for algo in ALGOS:
                    rs = [run_search(algo, g, start, goal, moves, self.no_corner_cut) for g in grids]
                    ok = [r for r in rs if r.found]
                    vals = (100 * len(ok) / len(rs),
                            sum(r.length for r in ok) / len(ok) if ok else 0,
                            sum(r.cycles for r in rs) / len(rs),
                            sum(r.expanded for r in rs) / len(rs),
                            sum(r.time_ms for r in rs) / len(rs))
                    for k, v in zip(keys, vals):
                        self.data[(algo, name)][k].append(v)
                    row[algo] = vals
                b, u = row[ALGOS[0]], row[ALGOS[1]]
                gain = u[3] / b[3] if b[3] else 0
                label = f"{x}×{x}" if by_size else f"{x} %"
                self.tree.insert("", tk.END, values=(label, name, f"{b[0]:.0f}", f"{b[1]:.1f}" if b[1] else "—",
                                                     f"{b[2]:.1f}", f"{u[2]:.1f}", f"{b[3]:.1f}", f"{u[3]:.1f}",
                                                     f"{gain:.2f}"))
        self.plot()

    def series(self, key):
        """Повертає список (назва, колір, штрих, значення) для побудови графіка."""
        out = []
        for name in OPERATORS:
            if key == "gain":
                b = self.data[(ALGOS[0], name)]["exp"]
                u = self.data[(ALGOS[1], name)]["exp"]
                out.append((OP_SHORT[name], OP_COLORS[name], None,
                            [uu / bb if bb else 0 for uu, bb in zip(u, b)], [1] * len(b)))
            else:
                for algo, dash, tag in ((ALGOS[0], None, "дво"), (ALGOS[1], (6, 4), "одно")):
                    d = self.data[(algo, name)]
                    out.append((f"{OP_SHORT[name]} {tag}", OP_COLORS[name], dash, d[key], d["succ"]))
        return out

    def plot(self):
        cv = self.chart
        cv.delete("all")
        if not self.data:
            return
        cv.update_idletasks()
        w, h = cv.winfo_width(), cv.winfo_height()
        key = self.METRICS[self.metric.get()]
        L, R, T, B = 70, 200, 34, 50
        ser = self.series(key)
        allv = [v for s in ser for v in s[3]]
        ymax = max(allv) * 1.1 if allv and max(allv) > 0 else 1
        xs = self.xs
        xmin, xmax = min(xs), (max(xs) if max(xs) > min(xs) else min(xs) + 1)

        def px(x): return L + (x - xmin) / (xmax - xmin) * (w - L - R)
        def py(y): return h - B - y / ymax * (h - T - B)

        cv.create_text((L + w - R) / 2, 14, text=self.metric.get() + (
            " залежно від розміру графу" if self.by_size else " залежно від частки стін"), font=("Arial", 11, "bold"))
        cv.create_line(L, h - B, w - R, h - B, width=2)
        cv.create_line(L, T, L, h - B, width=2)
        for i in range(6):
            y = ymax * i / 5
            cv.create_line(L - 4, py(y), w - R, py(y), fill="#E0E0E0")
            cv.create_text(L - 8, py(y), text=f"{y:.1f}" if ymax < 10 else f"{y:.0f}", anchor="e", font=("Arial", 9))
        for x in xs:
            cv.create_text(px(x), h - B + 14, text=(f"{x}×{x}" if self.by_size else f"{x}%"), font=("Arial", 9))
        cv.create_text((L + w - R) / 2, h - 14, text="Розмір графу N×N" if self.by_size else
                       "Частка непрохідних клітинок, %", font=("Arial", 10))
        for j, (label, color, dash, ys, succ) in enumerate(ser):
            pts = []
            for x, y, sc in zip(xs, ys, succ):
                if key == "len" and sc == 0:
                    continue
                pts += [px(x), py(y)]
                cv.create_oval(px(x) - 4, py(y) - 4, px(x) + 4, py(y) + 4, fill=color, outline="")
            if len(pts) >= 4:
                cv.create_line(*pts, fill=color, width=3, dash=dash)
            ly = T + 10 + j * 22
            cv.create_line(w - R + 12, ly, w - R + 44, ly, fill=color, width=3, dash=dash)
            cv.create_text(w - R + 50, ly, text=label, anchor="w", font=("Arial", 10, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = BiWaveApp(root)
    root.mainloop()
