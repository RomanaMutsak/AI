"""
Лабораторна робота №3 з курсу «Системи штучного інтелекту»
Тема: Одно-направлений пошук на графі. Дослідження особливостей використання
хвильового алгоритму для знаходження найкоротшого шляху у одиничних графах.

Одиничний граф задається у вигляді лабіринту (матриці), де
    -1  – непрохідна клітинка (вершина виключена з графу),
     0  – прохідна клітинка (вершина графу, ще не досягнута хвилею),
     k  – номер хвилі (k >= 1), яким позначено вершину під час пошуку.

Програма використовує лише стандартну бібліотеку Python (tkinter, random, time).
Запуск:  python lab3_wave_search.py
"""

import random
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------------------------------------------------------
#  Константи
# ----------------------------------------------------------------------------
WALL = -1   # непрохідна ділянка лабіринту
FREE = 0    # прохідна ділянка лабіринту

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

# Кольори клітинок
C_WALL = "#37474F"
C_FREE = "#FFFFFF"
C_START = "#2E7D32"
C_GOAL = "#C62828"
C_FRONT = "#FFA726"
C_PATH = "#FFEB3B"
C_WAVE_LIGHT = (227, 242, 253)   # #E3F2FD
C_WAVE_DARK = (30, 136, 229)     # #1E88E5

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
    """Генерує лабіринт rows x cols із заданою часткою непрохідних клітинок.

    Кількість стін рахується точно: round(rows*cols*wall_percent/100),
    клітинки з keep_free (старт і ціль) завжди лишаються прохідними.
    """
    rnd = random.Random(seed)
    grid = [[FREE] * cols for _ in range(rows)]
    cells = [(r, c) for r in range(rows) for c in range(cols)
             if (r, c) not in keep_free]
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
    # Заборона «зрізання кута»: діагональний крок можливий лише тоді,
    # коли обидві прилеглі ортогональні клітинки прохідні
    if no_corner_cut and dr != 0 and dc != 0:
        if grid[r + dr][c] == WALL or grid[r][c + dc] == WALL:
            return False
    return True


# ----------------------------------------------------------------------------
#  Однонаправлений хвильовий пошук (алгоритм Лі)
# ----------------------------------------------------------------------------
class WaveResult:
    """Результати одного запуску хвильового пошуку."""

    def __init__(self):
        self.found = False
        self.path = []          # список вершин (r, c) від старту до цілі
        self.marks = []         # матриця хвильових позначок
        self.fronts = []        # для анімації: (фронт, що розкривається, нова хвиля)
        self.cycles = 0         # кількість циклів розкриття (фронтів хвилі)
        self.expanded = 0       # кількість розкритих вершин
        self.labeled = 0        # кількість позначених вершин
        self.max_front = 0      # максимальний розмір фронту хвилі
        self.time_ms = 0.0      # час пошуку, мс

    @property
    def length(self):
        """Довжина шляху в кроках (кількість переходів)."""
        return len(self.path) - 1 if self.path else 0


def wave_search(grid, start, goal, moves, no_corner_cut=False):
    """Однонаправлений хвильовий пошук від start до goal.

    1) Пряма хвиля: старт отримує позначку 1; на кожному циклі всі вершини
       поточного фронту (позначка k) розкриваються, а їхні непозначені сусіди
       отримують позначку k + 1 і утворюють новий фронт. Пошук зупиняється,
       щойно позначено цільову вершину, або коли новий фронт порожній.
    2) Зворотний хід: від цілі послідовно переходимо до сусіда з позначкою,
       меншою на 1, доки не досягнемо старту.
    """
    res = WaveResult()
    t0 = time.perf_counter()

    rows, cols = len(grid), len(grid[0])
    marks = [row[:] for row in grid]
    sr, sc = start
    marks[sr][sc] = 1
    front = [start]
    res.labeled = 1
    res.max_front = 1
    found = start == goal

    # ---------------- пряма хвиля ----------------
    while front and not found:
        res.cycles += 1
        new_front = []
        for (r, c) in front:
            res.expanded += 1
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
        res.fronts.append((front, new_front))
        res.max_front = max(res.max_front, len(new_front))
        front = new_front

    # ---------------- зворотний хід ----------------
    if found:
        path = [goal]
        r, c = goal
        while (r, c) != start:
            k = marks[r][c]
            for dr, dc in moves:
                pr, pc = r - dr, c - dc
                if (0 <= pr < rows and 0 <= pc < cols and marks[pr][pc] == k - 1
                        and can_move(grid, pr, pc, dr, dc, no_corner_cut)):
                    r, c = pr, pc
                    path.append((r, c))
                    break
        path.reverse()
        res.path = path

    res.time_ms = (time.perf_counter() - t0) * 1000
    res.found = found
    res.marks = marks
    return res


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return "#%02X%02X%02X" % tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ----------------------------------------------------------------------------
#  Графічний інтерфейс
# ----------------------------------------------------------------------------
class WaveSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Системи ШІ - Лабораторна 3 (Хвильовий пошук) - Романа Муцак (ФЕІ-42)")
        self.root.geometry("1320x840")

        self.grid = maze_from_strings(BASE_MAZE)
        self.start = (0, 0)
        self.goal = (14, 14)

        # стан візуалізації
        self.result = None
        self.disp_marks = None       # позначки, що вже показані на полотні
        self.front_cells = set()
        self.path_cells = set()
        self.max_mark = 1
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

        # --- параметри графу ---
        f1 = ttk.LabelFrame(left, text="Параметри графу (лабіринту)", padding=6)
        f1.pack(fill=tk.X, pady=3)
        self.rows_var = tk.IntVar(value=15)
        self.cols_var = tk.IntVar(value=15)
        self.wall_var = tk.IntVar(value=30)
        self.seed_var = tk.IntVar(value=42)
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
        ttk.Button(f1, text="Інвертувати стіни", command=self.invert_walls).grid(row=4, column=2, columnspan=3, sticky="we")

        # --- початкова і цільова вершини ---
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
        ttk.Radiobutton(rf, text="стіну (-1/0)", value="wall", variable=self.click_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(rf, text="початкову", value="start", variable=self.click_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(rf, text="цільову", value="goal", variable=self.click_mode).pack(side=tk.LEFT)

        # --- оператор переходу ---
        f3 = ttk.LabelFrame(left, text="Оператор переходу", padding=6)
        f3.pack(fill=tk.X, pady=3)
        self.op_var = tk.StringVar(value=list(OPERATORS)[0])
        for name in OPERATORS:
            ttk.Radiobutton(f3, text=name, value=name, variable=self.op_var,
                            command=self.reset_wave).pack(anchor="w")
        self.nocut_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f3, text="Заборонити зрізання кутів (діагоналі)",
                        variable=self.nocut_var, command=self.reset_wave).pack(anchor="w", pady=(3, 0))

        # --- візуалізація ---
        f4 = ttk.LabelFrame(left, text="Візуалізація", padding=6)
        f4.pack(fill=tk.X, pady=3)
        self.delay_var = tk.IntVar(value=150)
        ttk.Label(f4, text="Затримка, мс:").grid(row=0, column=0, sticky="w")
        ttk.Scale(f4, from_=0, to=1000, variable=self.delay_var, orient=tk.HORIZONTAL, length=150,
                  command=lambda v: self.delay_var.set(int(float(v)))).grid(row=0, column=1, sticky="we")
        ttk.Label(f4, textvariable=self.delay_var, width=4).grid(row=0, column=2)
        self.values_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f4, text="Показувати значення клітинок (-1 / 0 / k)",
                        variable=self.values_var, command=self.redraw_cells).grid(row=1, column=0, columnspan=3, sticky="w")

        # --- керування пошуком ---
        f5 = ttk.LabelFrame(left, text="Керування пошуком", padding=6)
        f5.pack(fill=tk.X, pady=3)
        ttk.Button(f5, text="▶ Пуск (з анімацією)", command=self.run_animated).grid(row=0, column=0, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="⚡ Миттєвий пошук", command=self.run_instant).grid(row=0, column=1, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="⏸ Пауза / продовжити", command=self.toggle_pause).grid(row=1, column=0, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="⏭ Крок хвилі", command=self.step_once).grid(row=1, column=1, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="↺ Скинути хвилю", command=self.reset_wave).grid(row=2, column=0, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="📋 Результати", command=self.show_results).grid(row=2, column=1, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="Порівняти оператори переходу", command=self.compare_operators).grid(row=3, column=0, columnspan=2, sticky="we", padx=1, pady=1)
        ttk.Button(f5, text="Дослідження: розмір і щільність", command=self.open_research).grid(row=4, column=0, columnspan=2, sticky="we", padx=1, pady=1)
        f5.columnconfigure(0, weight=1)
        f5.columnconfigure(1, weight=1)

        # --- статус ---
        self.status_var = tk.StringVar(value="Готово. Оберіть параметри та натисніть «Пуск».")
        ttk.Label(left, textvariable=self.status_var, wraplength=330, foreground="#0D47A1",
                  font=("Arial", 9, "bold")).pack(fill=tk.X, pady=6)

        # --- полотно ---
        self.canvas = tk.Canvas(right, bg="#FAFAFA", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag_value", None))
        self.canvas.bind("<Configure>", lambda e: self.draw_grid())

        # --- легенда ---
        lg = ttk.Frame(right)
        lg.pack(fill=tk.X, pady=(4, 0))
        for color, text in [(C_WALL, "непрохідна (-1)"), (C_FREE, "прохідна (0)"),
                            (C_START, "початкова"), (C_GOAL, "цільова"),
                            (C_FRONT, "фронт хвилі"), ("#90CAF9", "позначені хвилею (k)"),
                            (C_PATH, "найкоротший шлях")]:
            tk.Label(lg, bg=color, width=2, relief="solid", bd=1).pack(side=tk.LEFT, padx=(8, 2))
            ttk.Label(lg, text=text).pack(side=tk.LEFT)

    # ------------------------------------------------------------ малювання
    def cell_geometry(self):
        rows, cols = len(self.grid), len(self.grid[0])
        w = max(self.canvas.winfo_width(), 200)
        h = max(self.canvas.winfo_height(), 200)
        margin = 26
        size = int(min((w - margin - 6) / cols, (h - margin - 6) / rows))
        size = max(8, min(size, 48))
        return size, margin, margin

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
        mark = self.disp_marks[r][c] if self.disp_marks else val
        show = self.values_var.get()
        if (r, c) == self.start:
            fill, text, fg = C_START, "П", "white"
        elif (r, c) == self.goal:
            fill, text, fg = C_GOAL, "Ц", "white"
        elif val == WALL:
            fill, text, fg = C_WALL, "-1", "#CFD8DC"
        elif mark > 0:
            if (r, c) in self.path_cells:
                fill, fg = C_PATH, "black"
            elif (r, c) in self.front_cells:
                fill, fg = C_FRONT, "black"
            else:
                t = (mark - 1) / max(1, self.max_mark - 1)
                fill = lerp_color(C_WAVE_LIGHT, C_WAVE_DARK, 0.15 + 0.85 * t)
                fg = "white" if t > 0.55 else "black"
            text = str(mark)
        else:
            fill, text, fg = C_FREE, "0", "#9E9E9E"
        if not show and text not in ("П", "Ц"):
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
            self.canvas.tag_raise("pathline")

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

    def fix_points(self):
        """Переносить старт/ціль у межі матриці та робить їх прохідними."""
        rows, cols = len(self.grid), len(self.grid[0])
        self.start = (min(self.start[0], rows - 1), min(self.start[1], cols - 1))
        self.goal = (min(self.goal[0], rows - 1), min(self.goal[1], cols - 1))
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
        self.grid = resize_maze(self.grid, *size)
        self.fix_points()
        self.full_reset()

    def generate(self):
        size = self.read_size()
        if not size:
            return
        rows, cols = size
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

    def invert_walls(self):
        self.grid = [[FREE if v == WALL else WALL for v in row] for row in self.grid]
        self.fix_points()
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

    # ------------------------------------------------------------ пошук
    def stop_animation(self):
        if self.anim_job:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None

    def reset_wave(self):
        self.stop_animation()
        self.result = None
        self.disp_marks = None
        self.front_cells, self.path_cells = set(), set()
        self.anim_step = 0
        self.paused = False
        self.redraw_cells()
        self.status_var.set("Хвилю скинуто. Граф: %d×%d, стін: %d." % (
            len(self.grid), len(self.grid[0]), sum(v == WALL for row in self.grid for v in row)))

    def full_reset(self):
        self.stop_animation()
        self.result = None
        self.disp_marks = None
        self.draw_grid()
        self.reset_wave()

    def compute(self):
        moves = OPERATORS[self.op_var.get()]
        self.result = wave_search(self.grid, self.start, self.goal, moves, self.nocut_var.get())
        self.max_mark = max(max(row) for row in self.result.marks)
        self.disp_marks = [row[:] for row in self.grid]
        self.disp_marks[self.start[0]][self.start[1]] = 1
        self.front_cells, self.path_cells = set(), set()
        self.anim_step = 0

    def run_instant(self):
        self.stop_animation()
        self.compute()
        self.disp_marks = [row[:] for row in self.result.marks]
        self.finish()

    def run_animated(self):
        self.stop_animation()
        self.compute()
        self.paused = False
        self.redraw_cells()
        self.anim_job = self.root.after(max(1, self.delay_var.get()), self.anim_tick)

    def advance(self):
        """Показує наступну хвилю. Повертає False, якщо хвиль більше немає."""
        res = self.result
        if self.anim_step >= len(res.fronts):
            return False
        _, new_front = res.fronts[self.anim_step]
        old = self.front_cells
        self.front_cells = set(new_front)
        for r, c in new_front:
            self.disp_marks[r][c] = res.marks[r][c]
        for r, c in old | self.front_cells:
            self.refresh_cell(r, c)
        self.anim_step += 1
        shown = sum(len(nf) for _, nf in res.fronts[:self.anim_step]) + 1
        self.status_var.set("Цикл (хвиля) %d з %d | розмір фронту: %d | позначено вершин: %d" % (
            self.anim_step, res.cycles, len(new_front), shown))
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
        if not self.result:
            return
        self.paused = not self.paused
        if not self.paused and self.anim_step <= len(self.result.fronts) and not self.path_cells:
            self.anim_tick()
        else:
            self.status_var.set(self.status_var.get() + "  [пауза]")

    def step_once(self):
        self.stop_animation()
        if not self.result or self.path_cells:
            self.compute()
            self.redraw_cells()
        self.paused = True
        if not self.advance():
            self.finish()

    def finish(self):
        res = self.result
        self.front_cells = set()
        self.path_cells = set(res.path)
        self.redraw_cells()
        if res.found:
            self.status_var.set("Шлях знайдено: %d кроків, циклів: %d, розкрито вершин: %d, час: %.3f мс" % (
                res.length, res.cycles, res.expanded, res.time_ms))
        else:
            self.status_var.set("Шлях НЕ знайдено: хвиля згасла після %d циклів (розкрито %d вершин)" % (
                res.cycles, res.expanded))
        self.show_results()

    # ------------------------------------------------------------ вікно результатів
    def results_text(self, res):
        rows, cols = len(self.grid), len(self.grid[0])
        walls = sum(v == WALL for row in self.grid for v in row)
        lines = [
            "РЕЗУЛЬТАТИ ОДНОНАПРАВЛЕНОГО ХВИЛЬОВОГО ПОШУКУ",
            "=" * 52,
            f"Розмір матриці (лабіринту): {rows} × {cols}",
            f"Прохідних вершин (0): {rows * cols - walls},  непрохідних (-1): {walls} ({walls / (rows * cols) * 100:.1f} %)",
            f"Оператор переходу: {self.op_var.get()}",
            f"Зрізання кутів по діагоналі: {'заборонено' if self.nocut_var.get() else 'дозволено'}",
            f"Початкова вершина: {self.start}     Цільова вершина: {self.goal}",
            "-" * 52,
            f"Шлях знайдено: {'ТАК' if res.found else 'НІ'}",
            f"Довжина шляху (кроків): {res.length if res.found else '—'}",
            f"Кількість вершин у шляху: {len(res.path) if res.found else '—'}",
            f"Кількість циклів розкриття вершин (хвиль): {res.cycles}",
            f"Кількість розкритих вершин: {res.expanded}",
            f"Кількість позначених хвилею вершин: {res.labeled}",
            f"Максимальний розмір фронту хвилі: {res.max_front}",
            f"Час, витрачений на пошук: {res.time_ms:.4f} мс",
            "-" * 52,
            "Вершини знайденого шляху (рядок, стовпець):",
        ]
        if res.found:
            chunk = []
            for i, p in enumerate(res.path):
                chunk.append(f"({p[0]},{p[1]})")
            for i in range(0, len(chunk), 7):
                lines.append("  " + " → ".join(chunk[i:i + 7]))
        else:
            lines.append("  шлях відсутній — цільова вершина недосяжна")
        lines += ["-" * 52,
                  "Матриця хвильових позначок",
                  "(-1 – стіна, 0 – не досягнута, k – номер хвилі, [k] – вершина шляху):"]
        path = set(res.path)
        for r in range(rows):
            row = []
            for c in range(cols):
                v = res.marks[r][c]
                row.append(f"[{v}]".rjust(4) if (r, c) in path else str(v).rjust(4))
            lines.append("".join(row))
        return "\n".join(lines)

    def show_results(self):
        if not self.result:
            messagebox.showinfo("Результати", "Спочатку виконайте пошук")
            return
        if self.results_win and self.results_win.winfo_exists():
            self.results_win.destroy()
        win = tk.Toplevel(self.root)
        win.title("Результати пошуку")
        win.geometry("640x700+%d+%d" % (self.root.winfo_rootx() + 690, self.root.winfo_rooty() + 40))
        self.results_win = win
        txt = tk.Text(win, font=("Courier New", 10), wrap="none")
        sb = ttk.Scrollbar(win, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", self.results_text(self.result))
        txt.tag_add("hdr", "1.0", "1.end")
        txt.tag_configure("hdr", font=("Courier New", 11, "bold"), foreground="#0D47A1")
        txt.configure(state="disabled")

    # ------------------------------------------------------------ порівняння операторів
    def compare_operators(self):
        win = tk.Toplevel(self.root)
        win.title("Порівняння операторів переходу на поточному графі")
        win.geometry("1060x560")
        cols = ("op", "found", "len", "nodes", "cycles", "exp", "lab", "front", "time")
        heads = ("Оператор", "Знайдено", "Довжина", "Вершин у шляху", "Циклів",
                 "Розкрито", "Позначено", "Макс. фронт", "Час, мс")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=3)
        for c, h in zip(cols, heads):
            tree.heading(c, text=h)
            tree.column(c, width=100 if c != "op" else 230, anchor="center")
        tree.pack(fill=tk.X, padx=6, pady=6)
        maps = ttk.Frame(win)
        maps.pack(fill=tk.BOTH, expand=True)
        rows, ncols = len(self.grid), len(self.grid[0])
        size = max(6, min(22, 330 // max(rows, ncols)))
        for i, name in enumerate(OPERATORS):
            res = wave_search(self.grid, self.start, self.goal, OPERATORS[name], self.nocut_var.get())
            tree.insert("", tk.END, values=(name, "так" if res.found else "ні",
                                            res.length if res.found else "—",
                                            len(res.path) if res.found else "—",
                                            res.cycles, res.expanded, res.labeled, res.max_front,
                                            f"{res.time_ms:.4f}"))
            fr = ttk.Frame(maps)
            fr.grid(row=0, column=i, padx=8, sticky="n")
            ttk.Label(fr, text=f"{OP_SHORT[name]}: {name}", foreground=OP_COLORS[name],
                      font=("Arial", 10, "bold")).pack()
            cv = tk.Canvas(fr, width=ncols * size + 2, height=rows * size + 2, bg="white", highlightthickness=0)
            cv.pack()
            self.draw_mini(cv, res, size)
            ttk.Label(fr, text=("Довжина: %d, розкрито: %d, циклів: %d" % (res.length, res.expanded, res.cycles))
                      if res.found else "Шлях не знайдено (розкрито: %d)" % res.expanded).pack()

    def draw_mini(self, cv, res, size):
        mx = max(max(row) for row in res.marks)
        path = set(res.path)
        for r, row in enumerate(res.marks):
            for c, v in enumerate(row):
                if (r, c) == self.start:
                    fill = C_START
                elif (r, c) == self.goal:
                    fill = C_GOAL
                elif v == WALL:
                    fill = C_WALL
                elif (r, c) in path:
                    fill = C_PATH
                elif v > 0:
                    fill = lerp_color(C_WAVE_LIGHT, C_WAVE_DARK, 0.15 + 0.85 * (v - 1) / max(1, mx - 1))
                else:
                    fill = C_FREE
                cv.create_rectangle(1 + c * size, 1 + r * size, 1 + (c + 1) * size, 1 + (r + 1) * size,
                                    fill=fill, outline="#B0BEC5")
        if res.found and len(res.path) > 1:
            pts = []
            for r, c in res.path:
                pts += [1 + c * size + size / 2, 1 + r * size + size / 2]
            cv.create_line(*pts, fill="#D50000", width=2)

    # ------------------------------------------------------------ дослідження
    def open_research(self):
        ResearchWindow(self.root, self.nocut_var.get())


class ResearchWindow:
    """Серійні досліди: вплив розміру графу та частки непрохідних клітинок."""

    METRICS = {
        "Розкрито вершин (середнє)": "exp",
        "Довжина шляху (середня)": "len",
        "Кількість циклів (середня)": "cyc",
        "Частка успішних пошуків, %": "succ",
        "Час пошуку, мс (середній)": "time",
    }

    def __init__(self, root, no_corner_cut):
        self.no_corner_cut = no_corner_cut
        self.win = tk.Toplevel(root)
        self.win.title("Дослідження впливу розміру графу та співвідношення прохідних/непрохідних клітинок")
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
        cb = ttk.Combobox(top, textvariable=self.metric, state="readonly", width=28, values=list(self.METRICS))
        cb.grid(row=0, column=9)
        cb.bind("<<ComboboxSelected>>", lambda e: self.plot())

        cols = ("x", "op", "succ", "len", "cyc", "exp", "time")
        heads = ("Значення", "Оператор", "Успіх, %", "Сер. довжина", "Сер. циклів", "Сер. розкрито", "Сер. час, мс")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings", height=18)
        for c, h in zip(cols, heads):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=110 if c != "op" else 240, anchor="center")
        self.tree.pack(fill=tk.X, padx=6)
        self.chart = tk.Canvas(self.win, bg="white", height=380)
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
        self.data = {name: {k: [] for k in ("succ", "len", "cyc", "exp", "time")} for name in OPERATORS}
        for i in self.tree.get_children():
            self.tree.delete(i)
        for x in xs:
            n, d = (x, fixed_d) if by_size else (fixed_n, x)
            start, goal = (0, 0), (n - 1, n - 1)
            # однакові лабіринти для всіх операторів – умови порівняння ідентичні
            grids = [generate_maze(n, n, d, seed + t, keep_free=(start, goal)) for t in range(trials)]
            for name, moves in OPERATORS.items():
                rs = [wave_search(g, start, goal, moves, self.no_corner_cut) for g in grids]
                ok = [r for r in rs if r.found]
                succ = 100 * len(ok) / len(rs)
                ln = sum(r.length for r in ok) / len(ok) if ok else 0
                cyc = sum(r.cycles for r in rs) / len(rs)
                ex = sum(r.expanded for r in rs) / len(rs)
                tm = sum(r.time_ms for r in rs) / len(rs)
                for k, v in zip(("succ", "len", "cyc", "exp", "time"), (succ, ln, cyc, ex, tm)):
                    self.data[name][k].append(v)
                label = f"{x}×{x}" if by_size else f"{x} %"
                self.tree.insert("", tk.END, values=(label, name, f"{succ:.0f}", f"{ln:.1f}" if ok else "—",
                                                     f"{cyc:.1f}", f"{ex:.1f}", f"{tm:.4f}"))
        self.plot()

    def plot(self):
        cv = self.chart
        cv.delete("all")
        if not self.data:
            return
        cv.update_idletasks()
        w, h = cv.winfo_width(), cv.winfo_height()
        key = self.METRICS[self.metric.get()]
        L, R, T, B = 70, 230, 34, 50
        allv = [v for name in self.data for v in self.data[name][key]]
        ymax = max(allv) * 1.1 if allv and max(allv) > 0 else 1
        xs = self.xs
        xmin, xmax = min(xs), max(xs) if max(xs) > min(xs) else min(xs) + 1

        def px(x): return L + (x - xmin) / (xmax - xmin) * (w - L - R)
        def py(y): return h - B - y / ymax * (h - T - B)

        cv.create_text(w / 2 - R / 2 + L / 2, 14, text=self.metric.get() + (
            " залежно від розміру графу" if self.by_size else " залежно від частки стін"),
            font=("Arial", 11, "bold"))
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
        for j, name in enumerate(self.data):
            ys = self.data[name][key]
            pts = []
            succ = self.data[name]["succ"]
            for x, y, sc in zip(xs, ys, succ):
                if key == "len" and sc == 0:
                    continue        # шлях не знайдено в жодному лабіринті – точки немає
                pts += [px(x), py(y)]
                cv.create_oval(px(x) - 4, py(y) - 4, px(x) + 4, py(y) + 4, fill=OP_COLORS[name], outline="")
            if len(pts) >= 4:
                cv.create_line(*pts, fill=OP_COLORS[name], width=3)
            ly = T + 10 + j * 24
            cv.create_line(w - R + 15, ly, w - R + 45, ly, fill=OP_COLORS[name], width=3)
            cv.create_text(w - R + 52, ly, text=OP_SHORT[name], anchor="w", font=("Arial", 10, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = WaveSearchApp(root)
    root.mainloop()
