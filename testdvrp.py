import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
import time
from data import EXPERIMENT_SET, CUSTOM_MAPS

# =============================================================================
# PHẦN 1: THUẬT TOÁN GA LAI
# =============================================================================
def calculate_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def split_procedure(n, W, L, q, c, d, S):
    V = [float('inf')] * (n + 1); P = [0] * (n + 1); V[0] = 0
    for i in range(1, n + 1):
        load, cost, j = 0, 0, i
        while j <= n:
            cust_j = S[j]; load += q[cust_j]
            if load > W: break
            if i == j: cost = c[0][cust_j] + d[cust_j] + c[cust_j][0]
            else:
                p = S[j-1]
                cost = cost - c[p][0] + c[p][cust_j] + d[cust_j] + c[cust_j][0]
            if cost <= L:
                if V[i-1] + cost < V[j]: V[j], P[j] = V[i-1] + cost, i - 1
                j += 1
            else: break
    return V, P

def extract_routes(n, S, P):
    routes = []; curr = n
    while curr > 0:
        prev = P[curr]
        if prev == curr: break
        routes.append([S[k] for k in range(prev + 1, curr + 1)])
        curr = prev
    routes.reverse(); return routes

def get_total_cost(routes, c, d):
    total = 0
    for r in routes:
        if not r: continue
        cost = c[0][r[0]] + d[r[0]]
        for i in range(len(r) - 1): cost += c[r[i]][r[i+1]] + d[r[i+1]]
        cost += c[r[-1]][0]; total += cost
    return total

def two_opt_route(route, c, d):
    best_r = route[:]
    best_c = 0
    if len(best_r) < 2: return best_r
    
    def r_cost(r):
        cost = c[0][r[0]] + d[r[0]]
        for i in range(len(r)-1): cost += c[r[i]][r[i+1]] + d[r[i+1]]
        return cost + c[r[-1]][0]

    best_c = r_cost(best_r)
    improved = True
    while improved:
        improved = False
        for i in range(len(best_r) - 1):
            for j in range(i + 1, len(best_r)):
                new_r = best_r[:i] + best_r[i:j+1][::-1] + best_r[j+1:]
                new_c = r_cost(new_r)
                if new_c < best_c - 0.001:
                    best_r, best_c, improved = new_r, new_c, True
    return best_r

def local_search_prins(n, W, L, q, c, d, routes):
    # Tối ưu từng tuyến bằng 2-Opt
    curr_routes = [two_opt_route(r, c, d) for r in routes]
    best_routes = [r[:] for r in curr_routes]
    best_cost = get_total_cost(best_routes, c, d)
    
    
    nodes = []
    for r_idx, r in enumerate(best_routes):
        for pos, cust in enumerate(r): nodes.append((cust, r_idx, pos))
    random.shuffle(nodes)
    
    for u, r_u, p_u in nodes:
        if r_u >= len(best_routes): continue 
        for v_r_idx in range(-1, len(best_routes)):
            new_routes = [r[:] for r in best_routes]
            if p_u >= len(new_routes[r_u]): continue
            new_routes[r_u].pop(p_u)
            
            
            target_v = v_r_idx
            if not new_routes[r_u]:
                new_routes.pop(r_u)
                if v_r_idx > r_u: target_v -= 1
                elif v_r_idx == r_u: continue 
            
            if target_v == -1: new_routes.append([u])
            else: new_routes[target_v].append(u)
            
            
            valid = True
            for r in new_routes:
                load = sum(q[cid] for cid in r)
                cost = c[0][r[0]] + d[r[0]]
                for i in range(len(r)-1): cost += c[r[i]][r[i+1]] + d[r[i+1]]
                cost += c[r[-1]][0]
                if load > W or cost > L:
                    valid = False; break
            
            if valid:
                new_cost = get_total_cost(new_routes, c, d)
                if new_cost < best_cost - 0.01:
                    return [two_opt_route(r, c, d) for r in new_routes]
    return best_routes

# =============================================================================
# PHẦN 2: GIAO DIỆN NGƯỜI DÙNG
# =============================================================================
class DVRP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Thực nghiệm DVRP")
        self.root.geometry("1100x680")

        self.root.configure(bg="#F0F2F5")
        self.CLR = {'bg': "#F0F2F5", 'sidebar': "#1E293B", 'card': "#FFFFFF", 'primary': "#6366F1", 'success': "#10B981", 'accent': "#F59E0B"}
        
       
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=("Segoe UI", 9))
        style.map("Treeview", background=[('selected', '#6366F1')])
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E2E8F0", relief="flat")
        
        self.zoom, self.pan_x, self.pan_y = 4.5, 100, 80
        self.last_x, self.last_y = 0, 0
        self.population = []
        self.current_id = None
        
        self.setup_ui()
        self.root.update()
        self.load_benchmark("P1")

    def setup_ui(self):
        # Sidebar
        self.sb = tk.Frame(self.root, bg=self.CLR['sidebar'], width=220)
        self.sb.pack(side=tk.LEFT, fill=tk.Y); self.sb.pack_propagate(False)
        
        tk.Label(self.sb, text="THAM SỐ HGA", font=("Segoe UI", 11, "bold"), bg=self.sb['bg'], fg="white").pack(pady=15)
        self.ent_pop = self.create_input("Quần thể (σ)", "30")
        self.ent_gen = self.create_input("Vòng lặp", "1000")
        self.ent_pm = self.create_input("Đột biến (pm)", "0.2")
        
        tk.Button(self.sb, text="CHẠY THUẬT TOÁN", bg=self.CLR['success'], fg="white", font=("Segoe UI", 9, "bold"), command=self.run_ga, cursor="hand2").pack(fill=tk.X, padx=15, pady=15)
        
        # Thống kê nhanh dưới nút chạy
        self.lbl_info = tk.Label(self.sb, text="Ready", bg=self.sb['bg'], fg="#888", font=("Arial", 8))
        self.lbl_info.pack(pady=10)

        # Main Area
        self.tabs = ttk.Notebook(self.root); self.tabs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tab_viz = tk.Frame(self.tabs, bg=self.CLR['bg']); self.tabs.add(self.tab_viz, text=" Trực quan hóa ")
        self.tab_bench = tk.Frame(self.tabs, bg=self.CLR['bg']); self.tabs.add(self.tab_bench, text=" Bảng kết quả ")
        self.setup_tab_viz(); self.setup_tab_bench()

    def create_input(self, txt, val):
        tk.Label(self.sb, text=txt, bg=self.sb['bg'], fg="#AAA", font=("Arial", 8)).pack(anchor="w", padx=15)
        e = tk.Entry(self.sb, bg="#0F172A", fg="white", insertbackground="white", relief="flat"); e.insert(0, val); e.pack(fill=tk.X, padx=15, pady=(0, 10)); return e

    def setup_tab_viz(self):
        tool = tk.Frame(self.tab_viz, bg=self.CLR['bg']); tool.pack(fill=tk.X, pady=2)
        self.cb_pb = ttk.Combobox(tool, values=list(EXPERIMENT_SET.keys()), state="readonly", width=5)
        self.cb_pb.set("P1"); self.cb_pb.pack(side=tk.LEFT, padx=10)
        tk.Button(tool, text="TẢI BẢN ĐỒ", command=lambda: self.load_benchmark(self.cb_pb.get())).pack(side=tk.LEFT)
        self.lbl_stats = tk.Label(tool, text="", font=("Arial", 8, "italic"), bg=self.CLR['bg']); self.lbl_stats.pack(side=tk.RIGHT, padx=10)

        stat_f = tk.Frame(self.tab_viz, bg="white", height=40, highlightthickness=1, highlightbackground="#DDD")
        stat_f.pack(fill=tk.X, pady=5, padx=5); stat_f.pack_propagate(False)
        self.lbl_cost = tk.Label(stat_f, text="Cost: 0.00", font=("Segoe UI", 10, "bold"), fg=self.CLR['primary'], bg="white"); self.lbl_cost.pack(side=tk.LEFT, padx=15)
        self.lbl_gap = tk.Label(stat_f, text="Cải thiện: 0.00%", font=("Segoe UI", 10, "bold"), fg=self.CLR['accent'], bg="white"); self.lbl_gap.pack(side=tk.RIGHT, padx=15)

        self.prog = ttk.Progressbar(self.tab_viz, length=100, mode='determinate'); self.prog.pack(fill=tk.X, pady=2, padx=5)
        self.canv = tk.Canvas(self.tab_viz, bg="white", highlightthickness=1, highlightbackground="#EEE"); self.canv.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canv.bind("<Button-1>", lambda e: self.set_mouse(e)); self.canv.bind("<B1-Motion>", self.pan); self.canv.bind("<MouseWheel>", self.zoom_map)

    def setup_tab_bench(self):
        container = tk.Frame(self.tab_bench, bg="white", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(container, text="BẢNG SO SÁNH KẾT QUẢ THỰC NGHIỆM", font=("Segoe UI", 12, "bold"), bg="white", fg=self.sb['bg']).pack(pady=(0, 15))
        
        cols = ("Pb", "n", "W", "L", "F(Pi1)", "Best GA", "Improve", "Time")
        self.tree = ttk.Treeview(container, columns=cols, show='headings', height=15)
        
        # Cấu hình cột
        col_widths = {"Pb": 60, "n": 60, "W": 80, "L": 80, "F(Pi1)": 110, "Best GA": 110, "Improve": 100, "Time": 100}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=col_widths.get(c, 80), anchor="center")
        
        # Thêm Scrollbar
        scrolly = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hàng xen kẽ màu
        self.tree.tag_configure('oddrow', background='#F8FAFC')
        self.tree.tag_configure('evenrow', background='white')
        
        for i, (pid, d) in enumerate(EXPERIMENT_SET.items()):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(pid, d['n'], d['W'], d['L'], "-", "-", "-", "Wait"), tags=(tag,))

    def set_mouse(self, e): self.last_x, self.last_y = e.x, e.y
    def pan(self, e):
        self.pan_x += (e.x-self.last_x); self.pan_y += (e.y-self.last_y); self.last_x, self.last_y = e.x, e.y; self.draw()
    def zoom_map(self, e):
        if e.delta > 0: self.zoom *= 1.1
        else: self.zoom /= 1.1
        self.draw()

    def load_benchmark(self, pid):
        conf = EXPERIMENT_SET[pid]; map_d = CUSTOM_MAPS[conf['map']]
        self.n, self.W, self.L = conf['n'], conf['W'], conf['L']
        self.raw_nodes = [map_d['depot']] + [(n[0], n[1]) for n in map_d['nodes'][:self.n]]
        self.q = [0] + [n[2] for n in map_d['nodes'][:self.n]]
        self.c = [[calculate_distance(self.raw_nodes[i], self.raw_nodes[j]) for j in range(self.n+1)] for i in range(self.n+1)]
        
        # Khởi tạo Baseline NN
        unvisited = list(range(1, self.n + 1)); tour_nn = [0]; curr = 0
        while unvisited:
            nxt = min(unvisited, key=lambda node: self.c[curr][node])
            unvisited.remove(nxt); tour_nn.append(nxt); curr = nxt
        V_nn, P_nn = split_procedure(self.n, self.W, self.L, self.q, self.c, [0]*(self.n+1), tour_nn)
        # Tối ưu hóa baseline
        base_routes = extract_routes(self.n, tour_nn, P_nn)
        opt_base_routes = [two_opt_route(r, self.c, [0]*(self.n+1)) for r in base_routes]
        self.baseline_cost = get_total_cost(opt_base_routes, self.c, [0]*(self.n+1))
        self.baseline_tour = [0]; [self.baseline_tour.append(c) for r in opt_base_routes for c in r]
        self.baseline_P = P_nn 
        
        self.current_id = pid; self.lbl_stats.config(text=f"n: {self.n}, W: {self.W}, L: {self.L}")
        self.population = []
        
        # Logic Auto-fit
        self.canv.update()
        cw, ch = self.canv.winfo_width(), self.canv.winfo_height()
        if cw < 100: cw, ch = 800, 500 # Dự phòng
        
        xs = [p[0] for p in self.raw_nodes]; ys = [p[1] for p in self.raw_nodes]
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        rx, ry = max(1, max_x - min_x), max(1, max_y - min_y)
        
        self.zoom = min((cw - 160) / rx, (ch - 160) / ry)
        self.pan_x = (cw - (max_x + min_x) * self.zoom) / 2
        self.pan_y = (ch - (max_y + min_y) * self.zoom) / 2
        
        self.draw()

    def draw(self):
        best = min(self.population, key=lambda x: x['cost']) if self.population else None
        routes = extract_routes(self.n, best['S'], best['P']) if best else []
        self.canv.delete("all")
        def ts(p): return (p[0]*self.zoom + self.pan_x, p[1]*self.zoom + self.pan_y)
        sn = [ts(p) for p in self.raw_nodes]
        cols = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4']
        for idx, r in enumerate(routes):
            pts = [sn[0]] + [sn[c] for c in r] + [sn[0]]
            for i in range(len(pts)-1): self.canv.create_line(pts[i], pts[i+1], fill=cols[idx%len(cols)], width=2, arrow=tk.LAST)
        for i in range(1, self.n+1): self.canv.create_oval(sn[i][0]-2, sn[i][1]-2, sn[i][0]+2, sn[i][1]+2, fill="white", outline="#6366F1")
        self.canv.create_rectangle(sn[0][0]-5, sn[0][1]-5, sn[0][0]+5, sn[0][1]+5, fill="#1E293B")
        
        # Chú thích linh hoạt theo chiều rộng Canvas
        cw = self.canv.winfo_width()
        lx = cw - 200 if cw > 250 else 600
        self.canv.create_rectangle(lx, 10, lx + 190, 100, fill="#F8FAFC", outline="#DDD")
        self.canv.create_rectangle(lx+10, 20, lx+25, 35, fill="#1E293B"); self.canv.create_text(lx+35, 27, text="Kho hàng (Depot)", anchor="w", font=("Arial", 8))
        self.canv.create_oval(lx+10, 45, lx+25, 60, outline="#6366F1"); self.canv.create_text(lx+35, 52, text="Khách hàng", anchor="w", font=("Arial", 8))
        self.canv.create_line(lx+10, 75, lx+25, 75, fill="#6366F1", width=2); self.canv.create_text(lx+35, 75, text="Lộ trình xe", anchor="w", font=("Arial", 8))

        if best:
            self.lbl_cost.config(text=f"Chi phí: {best['cost']:.2f}")
            gap = ((self.baseline_cost - best['cost'])/self.baseline_cost)*100
            self.lbl_gap.config(text=f"Cải thiện: {max(0, gap):.2f}%")

    def run_ga(self):
        try: pop_sz, max_gn, pm = int(self.ent_pop.get()), int(self.ent_gen.get()), float(self.ent_pm.get())
        except: return
        start_t = time.time(); self.population = []; no_improve = 0; best_ever = float('inf')
        
        # Khởi tạo quần thể đa dạng
        self.population.append({'S': self.baseline_tour, 'cost': self.baseline_cost, 'P': self.baseline_P})
        while len(self.population) < pop_sz:
            S = [0] + random.sample(range(1, self.n + 1), self.n)
            V, P = split_procedure(self.n, self.W, self.L, self.q, self.c, [0]*(self.n+1), S)
            if not any(abs(V[self.n]-p['cost']) < 0.1 for p in self.population):
                self.population.append({'S': S, 'cost': V[self.n], 'P': P})
        
        self.prog['maximum'] = max_gn
        for gen in range(max_gn):
            # Chọn lọc cha mẹ (Tournament Selection)
            def get_parent():
                p_cand = random.sample(self.population, 3)
                return min(p_cand, key=lambda x: x['cost'])['S']
            
            p1, p2 = get_parent(), get_parent()
            
            # Crossover (OX)
            a, b = sorted(random.sample(range(1, self.n+1), 2))
            child_S = [0] + [-1]*self.n; child_S[a:b+1] = p1[a:b+1]
            p2f = [x for x in p2[1:] if x not in child_S]; idx = 0
            for i in range(1, self.n+1):
                if child_S[i] == -1: child_S[i] = p2f[idx]; idx += 1
            
            # Local Search & Mutation
            if random.random() < pm or gen % 10 == 0:
                V, P = split_procedure(self.n, self.W, self.L, self.q, self.c, [0]*(self.n+1), child_S)
                improved_routes = local_search_prins(self.n, self.W, self.L, self.q, self.c, [0]*(self.n+1), extract_routes(self.n, child_S, P))
                child_S = [0]; [child_S.append(c) for r in improved_routes for c in r]
            
            V, P = split_procedure(self.n, self.W, self.L, self.q, self.c, [0]*(self.n+1), child_S)
            new_cost = V[self.n]
            
            # Cơ chế cập nhật quản lý đa dạng
            worst_idx = max(range(len(self.population)), key=lambda i: self.population[i]['cost'])
            is_duplicate = any(abs(new_cost - p['cost']) < 0.05 for p in self.population)
            
            if new_cost < self.population[worst_idx]['cost'] and not is_duplicate:
                self.population[worst_idx] = {'S': child_S, 'cost': new_cost, 'P': P}
                if new_cost < best_ever: best_ever = new_cost; no_improve = 0
                else: no_improve += 1
            else:
                no_improve += 1

            # Đột biến tái tạo nếu hội tụ quá lâu
            if no_improve > 100:
                self.lbl_info.config(text="Shaking population...", fg=self.CLR['accent'])
                for i in range(len(self.population)//2):
                    idx = max(range(len(self.population)), key=lambda i: self.population[i]['cost'])
                    S_rand = [0] + random.sample(range(1, self.n + 1), self.n)
                    V_rand, P_rand = split_procedure(self.n, self.W, self.L, self.q, self.c, [0]*(self.n+1), S_rand)
                    self.population[idx] = {'S': S_rand, 'cost': V_rand[self.n], 'P': P_rand}
                no_improve = 0

            if gen % 20 == 0:
                self.prog['value'] = gen; self.draw()
                self.lbl_info.config(text=f"Gen {gen}/{max_gn} | Best: {best_ever:.2f}", fg="#888")
                self.root.update()
        
        self.prog['value'] = max_gn
        best = min(self.population, key=lambda x: x['cost'])
        gap = ((self.baseline_cost - best['cost'])/self.baseline_cost)*100
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == self.current_id:
                self.tree.item(item, values=(self.current_id, self.n, self.W, self.L, f"{self.baseline_cost:.2f}", f"{best['cost']:.2f}", f"{max(0, gap):.2f}%", f"{time.time()-start_t:.1f}s"))
        self.lbl_info.config(text="Hoàn thành thực nghiệm", fg=self.CLR['success'])

if __name__ == "__main__":
    root = tk.Tk(); app = DVRP_GUI(root); root.mainloop()
