from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pje_automation.domain.execution import ExecutionMode, MODE_LABELS
from pje_automation.domain.models import WorkbookPreview
from pje_automation.gui.progress_view import ProgressView


DEFAULT_FIXED_PROCESS = "0010953-19.2017.5.03.0034"


class MainWindow(tk.Tk):
    def __init__(self, app_controller) -> None:
        super().__init__()
        self.app_controller = app_controller
        self.title("Automacao PJe-Calc")
        self.geometry("860x560")
        self.resizable(False, False)

        self.model_var = tk.StringVar()
        self.excel_var = tk.StringVar()
        self.history_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.fixed_process_var = tk.StringVar(value=DEFAULT_FIXED_PROCESS)
        self.preview_var = tk.StringVar(value="Nenhuma validacao executada.")
        self._mvp_thread: threading.Thread | None = None

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Modo de execucao").grid(row=0, column=0, sticky="w", pady=4)
        self.mode_combo = ttk.Combobox(
            frame,
            state="readonly",
            values=[MODE_LABELS[mode] for mode in ExecutionMode],
            width=52,
        )
        self.mode_combo.grid(row=0, column=1, sticky="w", padx=8)
        self.mode_combo.current(0)
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_changed)

        self.model_label = ttk.Label(frame, text="Modelo do PJe-Calc")
        self.model_label.grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.model_var, state="readonly", width=72).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(frame, text="Selecionar", command=self._pick_model).grid(row=1, column=2, sticky="e")

        self._path_row(frame, 2, "Excel de cadastro", self.excel_var, self._pick_excel)
        self._path_row(frame, 3, "Excel de historico (opcional)", self.history_var, self._pick_history)
        ttk.Label(frame, text="Processo fixo (opcional)").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.fixed_process_var, width=72).grid(row=4, column=1, sticky="ew", padx=8)
        self._path_row(frame, 5, "Pasta de saida", self.output_var, self._pick_output)

        actions = ttk.Frame(frame)
        actions.grid(row=6, column=0, columnspan=3, sticky="w", pady=(12, 12))
        self.validate_button = ttk.Button(actions, text="Validar", command=self._validate)
        self.validate_button.pack(side="left")
        self.probe_button = ttk.Button(actions, text="Mapear PJe", command=self._probe)
        self.probe_button.pack(side="left", padx=(8, 0))
        self.run_button = ttk.Button(actions, text="Executar", command=self._run_mvp)
        self.run_button.pack(side="left", padx=(8, 0))
        self.stop_button = ttk.Button(actions, text="Parar", command=self._stop_mvp, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))

        self.progress = ProgressView(frame)
        self.progress.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        ttk.Label(frame, text="Preview").grid(row=8, column=0, sticky="w")
        self.preview_box = tk.Text(frame, height=18, width=96)
        self.preview_box.grid(row=9, column=0, columnspan=3, sticky="nsew")

        for column in range(3):
            frame.columnconfigure(column, weight=1)
        self._on_mode_changed()

    def _path_row(self, master: ttk.Frame, row: int, label: str, variable: tk.StringVar, command) -> None:
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(master, textvariable=variable, state="readonly", width=72).grid(row=row, column=1, sticky="ew", padx=8)
        ttk.Button(master, text="Selecionar", command=command).grid(row=row, column=2, sticky="e")

    def _execution_mode(self) -> ExecutionMode:
        return tuple(ExecutionMode)[self.mode_combo.current()]

    def _optional_model_path(self) -> Path | None:
        raw_path = self.model_var.get().strip()
        return Path(raw_path) if raw_path else None

    def _on_mode_changed(self, _event=None) -> None:
        if self._execution_mode() == ExecutionMode.NOVO_CALCULO:
            self.model_label.configure(text="Modelo do PJe-Calc")
        else:
            self.model_label.configure(text="Modelo do PJe-Calc (nao usado neste modo)")

    def _pick_model(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Modelo PJe", "*.pjc *.zip")])
        if path:
            self.model_var.set(path)

    def _pick_excel(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xlsm")])
        if path:
            self.excel_var.set(path)

    def _pick_history(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xlsm")])
        if path:
            self.history_var.set(path)

    def _pick_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def _validate(self) -> None:
        try:
            preview = self.app_controller.validate_inputs(
                self._optional_model_path(),
                Path(self.excel_var.get()),
                Path(self.output_var.get()),
                Path(self.history_var.get()) if self.history_var.get() else None,
                execution_mode=self._execution_mode(),
                fixed_process=self.fixed_process_var.get().strip() or None,
            )
        except Exception as exc:
            self.progress.set_status("Falha na validacao.", str(exc))
            messagebox.showerror("Validacao", str(exc))
            return

        self.progress.set_status("Validacao concluida.", f"{len(preview.valid_records)} registros validos encontrados.")
        self._show_preview(preview)

    def _probe(self) -> None:
        try:
            result = self.app_controller.run_probe()
        except Exception as exc:
            self.progress.set_status("Falha no probe.", str(exc))
            messagebox.showerror("Probe", str(exc))
            return

        self.progress.set_status("Probe concluido.", str(result.output_dir))
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.insert(tk.END, f"URL: {result.url}\n")
        self.preview_box.insert(tk.END, f"HTML: {result.html_file}\n")
        self.preview_box.insert(tk.END, f"Elementos: {result.elements_file}\n")
        self.preview_box.insert(tk.END, f"Selectors: {result.selectors_file}\n")

    def _run_mvp(self) -> None:
        if self._mvp_thread and self._mvp_thread.is_alive():
            return
        self._set_running_state(True)
        self.progress.set_status("Executando...", "Automacao em andamento.")
        self._mvp_thread = threading.Thread(target=self._run_mvp_worker, daemon=True)
        self._mvp_thread.start()

    def _run_mvp_worker(self) -> None:
        try:
            message = self.app_controller.run_mvp(
                self._optional_model_path(),
                Path(self.excel_var.get()),
                Path(self.output_var.get()),
                Path(self.history_var.get()) if self.history_var.get() else None,
                execution_mode=self._execution_mode(),
                fixed_process=self.fixed_process_var.get().strip() or None,
            )
        except Exception as exc:
            self.after(0, lambda exc=exc: self._finish_mvp_error(exc))
            return
        self.after(0, lambda message=message: self._finish_mvp_success(message))

    def _stop_mvp(self) -> None:
        self.app_controller.request_stop()
        self.progress.set_status("Parando execucao...", "Aguardando encerramento da automacao.")

    def _finish_mvp_success(self, message: str) -> None:
        self._set_running_state(False)
        self.progress.set_status("Execucao concluida.", message)
        messagebox.showinfo("Automacao", message)

    def _finish_mvp_error(self, exc: Exception) -> None:
        self._set_running_state(False)
        if "cancelada pelo usuario" in str(exc).lower():
            self.progress.set_status("Execucao cancelada.", str(exc))
            return
        self.progress.set_status("Falha na execucao.", str(exc))
        messagebox.showerror("Automacao", str(exc))

    def _set_running_state(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.validate_button.configure(state=state)
        self.probe_button.configure(state=state)
        self.run_button.configure(state=state)
        self.stop_button.configure(state="normal" if running else "disabled")

    def _on_close(self) -> None:
        self.app_controller.request_stop()
        self.destroy()

    def _show_preview(self, preview: WorkbookPreview) -> None:
        self.preview_box.delete("1.0", tk.END)
        self.preview_box.insert(tk.END, f"Registros validos: {len(preview.valid_records)}\n")
        self.preview_box.insert(tk.END, "\nNomes validados para automacao:\n")
        for record in preview.valid_records:
            self.preview_box.insert(tk.END, f"{record.nome}\n")
