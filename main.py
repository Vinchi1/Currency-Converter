import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 500

API_BASE_URL = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"


class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        self.history_path = "history.json"

        self.api_key = None
        self.rates_cache = {}

        self.history = []

        self.currencies = [
            "USD", "EUR", "RUB", "GBP", "JPY", "CNY", "CHF", "CAD", "AUD"
        ]

        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        frame_top = tk.LabelFrame(self.root, text="Параметры конвертации", padx=10, pady=10)
        frame_top.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_top, text="Из валюты:").grid(row=0, column=0, sticky="w")
        self.from_var = tk.StringVar(value="USD")
        self.combo_from = ttk.Combobox(
            frame_top,
            textvariable=self.from_var,
            values=self.currencies,
            state="readonly",
            width=10,
        )
        self.combo_from.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_top, text="В валюту:").grid(row=0, column=2, sticky="w")
        self.to_var = tk.StringVar(value="EUR")
        self.combo_to = ttk.Combobox(
            frame_top,
            textvariable=self.to_var,
            values=self.currencies,
            state="readonly",
            width=10,
        )
        self.combo_to.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(frame_top, text="Сумма:").grid(row=1, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        self.entry_amount = tk.Entry(frame_top, textvariable=self.amount_var, width=20)
        self.entry_amount.grid(row=1, column=1, padx=5, pady=5)

        self.btn_convert = tk.Button(frame_top, text="Конвертировать", command=self.convert)
        self.btn_convert.grid(row=1, column=2, padx=5, pady=5)

        self.btn_set_key = tk.Button(frame_top, text="Указать API-ключ", command=self.set_api_key)
        self.btn_set_key.grid(row=1, column=3, padx=5, pady=5)

        frame_result = tk.LabelFrame(self.root, text="Результат", padx=10, pady=10)
        frame_result.pack(fill="x", padx=10, pady=5)

        self.result_var = tk.StringVar()
        self.lbl_result = tk.Label(frame_result, textvariable=self.result_var, font=("Arial", 11, "bold"))
        self.lbl_result.pack(anchor="w")

        frame_history = tk.LabelFrame(self.root, text="История конвертаций", padx=10, pady=10)
        frame_history.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("datetime", "from_curr", "to_curr", "amount", "result", "rate")
        self.tree = ttk.Treeview(
            frame_history,
            columns=columns,
            show="headings",
            height=10,
            selectmode="browse",
        )

        headers = {
            "datetime": "Дата и время",
            "from_curr": "Из",
            "to_curr": "В",
            "amount": "Сумма",
            "result": "Результат",
            "rate": "Курс",
        }
        widths = {
            "datetime": 140,
            "from_curr": 60,
            "to_curr": 60,
            "amount": 80,
            "result": 100,
            "rate": 80,
        }

        for col, text in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(frame_history, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        frame_history.grid_rowconfigure(0, weight=1)
        frame_history.grid_columnconfigure(0, weight=1)

    def set_api_key(self):
        win = tk.Toplevel(self.root)
        win.title("Указание API-ключа")
        tk.Label(win, text="Введите API-ключ ExchangeRate-API:").pack(padx=10, pady=5)
        key_var = tk.StringVar(value=self.api_key or "")
        entry = tk.Entry(win, textvariable=key_var, width=40)
        entry.pack(padx=10, pady=5)

        def save_key():
            self.api_key = key_var.get().strip()
            if not self.api_key:
                messagebox.showwarning("API-ключ", "API-ключ не может быть пустым.")
                return
            messagebox.showinfo("API-ключ", "API-ключ сохранён на время работы программы.")
            win.destroy()

        btn_save = tk.Button(win, text="Сохранить", command=save_key)
        btn_save.pack(pady=10)

    def fetch_rates(self, base):
        if not self.api_key:
            messagebox.showwarning(
                "API-ключ",
                "Сначала укажите API-ключ с помощью кнопки 'Указать API-ключ'."
            )
            return None

        cache_key = base
        if cache_key in self.rates_cache:
            return self.rates_cache[cache_key]

        url = API_BASE_URL.format(api_key=self.api_key, base=base)
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить курсы валют: {e}")
            return None

        if data.get("result") != "success":
            messagebox.showerror("Ошибка API", f"Ответ API: {data.get('error-type', 'неизвестная ошибка')}")
            return None

        rates = data.get("conversion_rates", {})
        self.rates_cache[cache_key] = rates
        return rates

    def convert(self):
        from_curr = self.from_var.get()
        to_curr = self.to_var.get()
        amount_str = self.amount_var.get().strip()

        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showwarning("Ошибка ввода", "Сумма должна быть числом.")
            return

        if amount <= 0:
            messagebox.showwarning("Ошибка ввода", "Сумма должна быть положительным числом.")
            return

        if from_curr == to_curr:
            messagebox.showwarning("Ошибка", "Валюты должны отличаться.")
            return

        rates = self.fetch_rates(from_curr)
        if rates is None:
            return

        rate = rates.get(to_curr)
        if rate is None:
            messagebox.showerror("Ошибка", f"Нет курса для валюты {to_curr}.")
            return

        result_amount = amount * rate
        self.result_var.set(f"{amount:.2f} {from_curr} = {result_amount:.2f} {to_curr} (курс: {rate:.4f})")

        record = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_curr": from_curr,
            "to_curr": to_curr,
            "amount": amount,
            "result": result_amount,
            "rate": rate,
        }
        self.history.append(record)
        self.add_record_to_tree(record)
        self.save_history()

    def add_record_to_tree(self, record):
        values = (
            record["datetime"],
            record["from_curr"],
            record["to_curr"],
            f"{record['amount']:.2f}",
            f"{record['result']:.2f}",
            f"{record['rate']:.4f}",
        )
        self.tree.insert("", 0, values=values)

    def load_history(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.history = data
                        for record in self.history:
                            self.add_record_to_tree(record)
            except Exception:
                self.history = []

    def save_history(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")


if __name__ == "__main__":
    app = CurrencyConverterApp(tk.Tk())
    app.root.mainloop()
