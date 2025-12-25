import tkinter as tk
from tkinter import ttk
import webbrowser
import json
import os
from datetime import datetime

CONFIG_FILE = "tabs_config.json"

class TradeTab:
    def __init__(self, notebook, app, data=None):
        self.notebook = notebook
        self.app = app 
        self.frame = ttk.Frame(notebook, padding="30")
        
        defaults = {
            "tv_symbol": "gold",
            "direction": "BEAR",
            "leverage": "5",
            "underlying_buy": "4525.0",
            "cert_price_buy": "39.0",
            "tp_underlying": "4461.0",
            "sl_underlying": "4530.0",
            "spread": "0.12",
            "portfolio_total": "50000",
            "risk_pct": "1.0",
            "max_pos_pct": "100.0"
        }
        if data: defaults.update(data)

        self.notebook.add(self.frame, text="Laddar...")
        
        # --- INPUTS ---
        input_frame = ttk.LabelFrame(self.frame, text=" Inmatning ", padding=15)
        input_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.entries = {}
        row_dir = ttk.Frame(input_frame)
        row_dir.pack(fill="x", pady=5)
        ttk.Label(row_dir, text="Riktning:", width=25).pack(side="left")
        self.dir_var = tk.StringVar(value=defaults["direction"])
        dir_combo = ttk.Combobox(row_dir, textvariable=self.dir_var, values=["BULL", "BEAR"], state="readonly")
        dir_combo.pack(side="right", fill="x", expand=True)
        dir_combo.bind("<<ComboboxSelected>>", self.on_change)

        fields = [
            ("tv_symbol", "TradingView Symbol:", defaults["tv_symbol"]),
            ("leverage", "Hävstång:", defaults["leverage"]),
            ("underlying_buy", "Underliggande köp:", defaults["underlying_buy"]),
            ("cert_price_buy", "Certifikat köp (SEK):", defaults["cert_price_buy"]),
            ("tp_underlying", "Take Profit (Und):", defaults["tp_underlying"]),
            ("sl_underlying", "Stop Loss (Und):", defaults["sl_underlying"]),
            ("spread", "Spread (%):", defaults["spread"]),
            ("portfolio_total", "Portfölj (SEK):", defaults["portfolio_total"]),
            ("risk_pct", "Risk per trade (%):", defaults["risk_pct"]),
            ("max_pos_pct", "Max position (%):", defaults["max_pos_pct"]),
        ]

        for key, label_text, default_val in fields:
            row = ttk.Frame(input_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label_text, width=25).pack(side="left")
            entry = ttk.Entry(row)
            entry.pack(side="right", fill="x", expand=True)
            entry.insert(0, str(default_val))
            self.entries[key] = entry
            entry.bind("<KeyRelease>", self.on_change)

        # --- RESULTS ---
        res_container = ttk.Frame(self.frame)
        res_container.pack(side="right", fill="both", expand=True, padx=5)

        self.res_pos = ttk.LabelFrame(res_container, text=" Positionering ", padding=15)
        self.res_pos.pack(fill="x", pady=5)
        self.label_qty = ttk.Label(self.res_pos, text="-", font=("Helvetica", 12, "bold"))
        self.label_qty.pack(anchor="w")
        self.label_cost = ttk.Label(self.res_pos, text="-")
        self.label_cost.pack(anchor="w")
        self.label_warn = ttk.Label(self.res_pos, text="", foreground="orange")
        self.label_warn.pack(anchor="w")

        self.res_money = ttk.LabelFrame(res_container, text=" Resultat vid Mål/Stopp (SEK) ", padding=15)
        self.res_money.pack(fill="x", pady=5)
        self.label_total_vinst = ttk.Label(self.res_money, text="-", font=("Helvetica", 11, "bold"), foreground="green")
        self.label_total_vinst.pack(anchor="w")
        self.label_total_förlust = ttk.Label(self.res_money, text="-", font=("Helvetica", 11), foreground="red")
        self.label_total_förlust.pack(anchor="w")

        self.res_levels = ttk.LabelFrame(res_container, text=" Certifikat Prisnivåer ", padding=15)
        self.res_levels.pack(fill="x", pady=5)
        self.label_tp_cert = ttk.Label(self.res_levels, text="-")
        self.label_tp_cert.pack(anchor="w")
        self.label_sl_cert = ttk.Label(self.res_levels, text="-")
        self.label_sl_cert.pack(anchor="w")
        self.label_rr = ttk.Label(self.res_levels, text="-", font=("Helvetica", 11, "bold"))
        self.label_rr.pack(anchor="w", pady=5)

        self.update_tab_name()
        self.calculate()

    def on_change(self, event=None):
        self.update_tab_name()
        self.calculate()
        self.app.save_all_data()

    def update_tab_name(self):
        prefix = "Short" if self.dir_var.get() == "BEAR" else "Long"
        self.notebook.tab(self.frame, text=f"{self.entries['tv_symbol'].get()} {prefix}")

    def get_data(self):
        d = {k: v.get() for k, v in self.entries.items()}
        d["direction"] = self.dir_var.get()
        return d

    def calculate(self):
        try:
            und_e = float(self.entries["underlying_buy"].get())
            cert_e = float(self.entries["cert_price_buy"].get())
            tp_u = float(self.entries["tp_underlying"].get())
            sl_u = float(self.entries["sl_underlying"].get())
            spr = float(self.entries["spread"].get()) / 100
            port = float(self.entries["portfolio_total"].get())
            risk_p = float(self.entries["risk_pct"].get()) / 100
            max_p = float(self.entries["max_pos_pct"].get()) / 100
            lev = float(self.entries["leverage"].get()) * (1 if self.dir_var.get() == "BULL" else -1)

            def get_p(target):
                pct = (target / und_e) - 1
                return max(0, cert_e * (1 + lev * pct) * (1 - spr))

            tp_c = get_p(tp_u)
            sl_c = get_p(sl_u)
            loss_per_cert = cert_e - sl_c
            
            if (self.dir_var.get() == "BULL" and sl_u >= und_e) or (self.dir_var.get() == "BEAR" and sl_u <= und_e) or loss_per_cert <= 0:
                self.label_qty.config(text="Ogiltig SL!", foreground="red")
                return

            qty = (port * risk_p) / loss_per_cert
            cost = qty * cert_e
            self.label_warn.config(text="")
            if cost > (port * max_p):
                qty = (port * max_p) / cert_e
                cost = port * max_p
                self.label_warn.config(text=f"⚠ Capped till {max_p*100:.0f}%")

            tot_vinst = (tp_c - cert_e) * qty
            tot_förlust = (sl_c - cert_e) * qty

            self.label_qty.config(text=f"Köp Antal: {qty:.0f} st", foreground="#007fff")
            self.label_cost.config(text=f"Investering: {cost:.2f} SEK ({(cost/port)*100:.1f}%)")
            self.label_total_vinst.config(text=f"Vinst vid mål: +{tot_vinst:.2f} SEK")
            self.label_total_förlust.config(text=f"Förlust vid stopp: {tot_förlust:.2f} SEK")
            self.label_tp_cert.config(text=f"Säljpris Cert: {tp_c:.4f} SEK")
            self.label_sl_cert.config(text=f"Stopp-pris Cert: {sl_c:.4f} SEK")
            rr = (tp_c - cert_e) / loss_per_cert
            self.label_rr.config(text=f"R/R: 1 : {rr:.2f}", foreground="green" if rr >= 2 else "orange")
        except: pass

class CertApp:
    def __init__(self, root):
        self.root = root
        root.title("Cert Optimizer v3")
        root.geometry("1100x800")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.status = ttk.Label(root, text="Redo", relief="sunken", padding=5)
        self.status.pack(fill="x", side="bottom")
        self.tabs = []
        self.load_all_data()
        ttk.Button(root, text="+ Ny trade", command=lambda: self.add_tab()).pack(pady=5)

    def add_tab(self, data=None):
        t = TradeTab(self.notebook, self, data)
        self.tabs.append(t)
        self.notebook.select(t.frame)

    def save_all_data(self):
        data = [t.get_data() for t in self.tabs]
        with open(CONFIG_FILE, "w") as f: json.dump(data, f)
        self.status.config(text=f"✓ Sparat {datetime.now().strftime('%H:%M:%S')}", foreground="green")

    def load_all_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    for d in json.load(f): self.add_tab(d)
            except: self.add_tab()
        else: self.add_tab()

if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use('clam')
    CertApp(root)
    root.mainloop()
