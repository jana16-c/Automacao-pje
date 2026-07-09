from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ProgressView(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.status_var = tk.StringVar(value="Aguardando validacao.")
        self.detail_var = tk.StringVar(value="")

        ttk.Label(self, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(self, textvariable=self.detail_var, foreground="#555").grid(row=1, column=0, sticky="w", pady=(4, 0))

    def set_status(self, status: str, detail: str = "") -> None:
        self.status_var.set(status)
        self.detail_var.set(detail)
