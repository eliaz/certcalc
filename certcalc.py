import tkinter as tk
from tkinter import ttk
import webbrowser

class TradeTab:
    def __init__(self, notebook, symbol="OMXS30", leverage="10"):
        self.notebook = notebook

        # Skapa fliken med tillfälligt namn
        self.frame = ttk.Frame(notebook, padding="30")
        self.notebook.add(self.frame, text="Ny trade...")

        # Titel i fliken
        ttk.Label(self.frame, text="Trade detaljer", font=("Helvetica", 16, "bold")).pack(pady=(0, 20))

        # Inputs
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill="x", pady=10)

        self.entries = {}

        fields = [
            ("underlying_buy", "Underliggande pris vid köp:", "1000.0"),
            ("cert_price_buy", "Certifikat pris vid köp:", "10.0"),
            ("num_certs", "Antal certifikat:", "1"),
            ("leverage", "Hävstång (t.ex. 10, -5):", leverage),
            ("spread", "Spread (%):", "0.12"),
            ("new_underlying", "Nytt underliggande pris (simulering):", "1050.0"),
            ("tv_symbol", "TradingView symbol:", symbol),
        ]

        for key, label_text, default in fields:
            row = ttk.Frame(input_frame)
            row.pack(fill="x", pady=10)

            ttk.Label(row, text=label_text, width=38, anchor="w").pack(side="left")
            entry = ttk.Entry(row, font=("Helvetica", 11))
            entry.pack(side="right", fill="x", expand=True, padx=(15, 0))
            entry.insert(0, default)
            self.entries[key] = entry

            # Live-uppdatering av fliknamn
            if key in ["tv_symbol", "leverage"]:
                entry.bind("<KeyRelease>", self.update_tab_name)

        # Knappar
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=30)

        calc_btn = tk.Button(btn_frame, text="Beräkna P/L", font=("Helvetica", 12, "bold"),
                             bg="#4CAF50", fg="white", padx=20, pady=10, command=self.calculate)
        calc_btn.pack(pady=10)

        tv_btn = ttk.Button(btn_frame, text="Öppna i TradingView", command=self.open_tradingview)
        tv_btn.pack(pady=10)

        # Resultat
        result_frame = ttk.LabelFrame(self.frame, text=" Resultat ", padding=25)
        result_frame.pack(pady=30, fill="x", padx=30)

        self.label_theory = ttk.Label(result_frame, text="Teoretiskt cert-pris: -", font=("Helvetica", 13))
        self.label_theory.pack(pady=8)

        self.label_real = ttk.Label(result_frame, text="Realistiskt säljpris (med spread): -", font=("Helvetica", 14, "bold"))
        self.label_real.pack(pady=10)

        self.label_per = ttk.Label(result_frame, text="Per cert: -", font=("Helvetica", 13))
        self.label_per.pack(pady=8)

        self.label_total = ttk.Label(result_frame, text="TOTALT: -", font=("Helvetica", 18, "bold"))
        self.label_total.pack(pady=15)

        # Uppdatera namn och beräkna vid start
        self.update_tab_name()
        self.calculate()

    def get_tab_name(self):
        try:
            symbol = self.entries["tv_symbol"].get().strip() or "Symbol"
            lev = self.entries["leverage"].get().strip().upper()
            if lev.startswith('X'):
                lev = lev[1:]
            sign = "-" if lev.startswith('-') else ""
            lev = lev.lstrip('-X ')
            if not lev:
                lev = "?"
            return f"{symbol} {sign}x{lev}"
        except:
            return "Ny trade"

    def update_tab_name(self, event=None):
        new_name = self.get_tab_name()
        self.notebook.tab(self.frame, text=new_name)

    def calculate(self):
        try:
            underlying_buy = float(self.entries["underlying_buy"].get())
            cert_price_buy = float(self.entries["cert_price_buy"].get())
            num_certs = float(self.entries["num_certs"].get() or "1")
            spread_pct = float(self.entries["spread"].get() or "0.12") / 100

            lev_str = self.entries["leverage"].get().strip().upper()
            if lev_str.startswith('X'):
                lev_str = lev_str[1:]
            sign = -1 if '-' in lev_str else 1
            lev_str = lev_str.strip('-X ')
            leverage = sign * float(lev_str or 1)

            new_und_str = self.entries["new_underlying"].get().strip()
            new_underlying = float(new_und_str) if new_und_str else underlying_buy

            pct_change = (new_underlying / underlying_buy) - 1
            theory_price = cert_price_buy * (1 + leverage * pct_change)
            real_price = theory_price * (1 - spread_pct)

            pl_per = real_price - cert_price_buy
            pl_per_pct = (pl_per / cert_price_buy) * 100 if cert_price_buy else 0

            total_pl = pl_per * num_certs
            total_pct = (total_pl / (cert_price_buy * num_certs)) * 100 if cert_price_buy else 0

            self.label_theory.config(text=f"Teoretiskt cert-pris: {theory_price:.4f} SEK")
            self.label_real.config(text=f"Realistiskt säljpris: {real_price:.4f} SEK")
            self.label_per.config(text=f"Per cert: {pl_per:+.4f} SEK ({pl_per_pct:+.2f}%)")

            color = "#d00000" if total_pl < 0 else "#008000"
            self.label_total.config(text=f"TOTALT ({num_certs:.0f} cert): {total_pl:+.2f} SEK ({total_pct:+.2f}%)",
                                    foreground=color)

        except Exception:
            self.label_theory.config(text="Ogiltig inmatning!")
            self.label_real.config(text="")
            self.label_per.config(text="")
            self.label_total.config(text="")

    def open_tradingview(self):
        symbol = self.entries["tv_symbol"].get().strip()
        if symbol:
            webbrowser.open(f"https://www.tradingview.com/chart/?symbol={symbol}")

class CertCalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Avanza Multi-Trade Certifikat Calculator")

        # Basstorlek
        base_width = 800
        base_height = 900

        # 30% större i båda riktningar
        width = int(base_width * 1.3)   # ca 1040
        height = int(base_height * 1.3) # ca 1170

        # Centrera på skärmen
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)

        # Första fliken
        self.add_new_tab()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        new_tab_btn = tk.Button(btn_frame, text="+ Ny trade", font=("Helvetica", 12, "bold"),
                                bg="#2196F3", fg="white", padx=20, pady=10,
                                command=self.add_new_tab)
        new_tab_btn.pack()

        note = (
            "Fliknamnet uppdateras automatiskt i realtid när du skriver i 'TradingView symbol' eller 'Hävstång'!\n"
            "Perfekt för att hålla koll på flera Bull/Bear-positioner samtidigt."
        )
        ttk.Label(main_frame, text=note, foreground="gray", justify="center").pack(pady=20)

    def add_new_tab(self):
        if self.notebook.tabs():
            current_tab_widget = self.notebook.nametowidget(self.notebook.select())
            symbol = "OMXS30"
            leverage = "10"
            for child in current_tab_widget.winfo_children():
                if len(current_tab_widget.winfo_children()) > 1:
                    input_frame = current_tab_widget.winfo_children()[1]
                    for row in input_frame.winfo_children():
                        if len(row.winfo_children()) == 2:
                            label_text = row.winfo_children()[0].cget("text").lower()
                            entry = row.winfo_children()[1]
                            if "symbol" in label_text:
                                symbol = entry.get().strip()
                            if "hävstång" in label_text:
                                leverage = entry.get().strip()
            TradeTab(self.notebook, symbol, leverage)
        else:
            TradeTab(self.notebook)

if __name__ == "__main__":
    root = tk.Tk()
    app = CertCalculatorApp(root)
    root.mainloop()
