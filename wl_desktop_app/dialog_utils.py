# -*- coding: utf-8 -*-
"""大きめの入力ダイアログ（名前・メール入力で共通利用）。"""
import tkinter as tk
from tkinter import ttk


# ダイアログ内のフォント・入力幅を揃えて見やすくする
DIALOG_FONT_SIZE = 16
ENTRY_WIDTH = 50


def ask_string_large(title: str, prompt: str, parent=None, initial_value: str = "") -> str | None:
    """大きめの1行入力ダイアログを表示し、入力文字列を返す。キャンセル時は None。"""
    result = [None]  # クロージャで代入するためリストで保持

    def on_ok():
        result[0] = entry.get().strip()
        win.destroy()

    def on_cancel():
        win.destroy()

    win = tk.Toplevel(parent) if parent else tk.Tk()
    if not parent:
        win.withdraw()
    win.title(title)
    win.attributes("-topmost", True)
    win.resizable(True, False)

    f = ttk.Frame(win, padding=16)
    f.pack(fill=tk.BOTH, expand=True)

    label = ttk.Label(f, text=prompt, font=("", DIALOG_FONT_SIZE), wraplength=480)
    label.pack(anchor=tk.W, pady=(0, 10))

    entry = ttk.Entry(f, width=ENTRY_WIDTH, font=("", DIALOG_FONT_SIZE))
    entry.pack(fill=tk.X, pady=(0, 16))
    if initial_value:
        entry.insert(0, initial_value)
        entry.select_range(0, tk.END)
    entry.focus_set()

    btn_f = ttk.Frame(f)
    btn_f.pack(fill=tk.X)
    ttk.Button(btn_f, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(8, 0))
    ttk.Button(btn_f, text="キャンセル", command=on_cancel).pack(side=tk.RIGHT)

    entry.bind("<Return>", lambda e: on_ok())
    entry.bind("<Escape>", lambda e: on_cancel())

    win.update_idletasks()
    win.geometry(f"+{win.winfo_screenwidth()//2 - 250}+{win.winfo_screenheight()//2 - 120}")
    if not parent:
        win.deiconify()
    win.wait_window()

    return result[0]
