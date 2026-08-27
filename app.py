"""Tkinter desktop interface for non-technical users."""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config.categories import CATEGORIES
from src import convert_wawi_to_shopify

ROOT = Path(__file__).resolve().parent


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WAMI to Shopify Converter")
        self.geometry("680x430")
        self.resizable(True, True)
        self.group = tk.StringVar(value="Tafeln")
        self.category = tk.StringVar()
        self.file = tk.StringVar()
        self._build()
        self._group_changed()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="WAMI → Shopify / Matrixify", font=("TkDefaultFont", 16, "bold")).pack(anchor="w", pady=(0, 18))
        ttk.Label(frame, text="Main category").pack(anchor="w")
        group = ttk.Combobox(frame, textvariable=self.group, values=list(CATEGORIES), state="readonly")
        group.pack(fill="x", pady=(4, 12)); group.bind("<<ComboboxSelected>>", lambda _e: self._group_changed())
        ttk.Label(frame, text="Subcategory").pack(anchor="w")
        self.category_box = ttk.Combobox(frame, textvariable=self.category, state="readonly")
        self.category_box.pack(fill="x", pady=(4, 12))
        ttk.Button(frame, text="Choose Excel File…", command=self._choose).pack(anchor="w")
        ttk.Label(frame, textvariable=self.file, wraplength=630).pack(anchor="w", pady=(8, 16))
        self.convert_button = ttk.Button(frame, text="Validate and Convert", command=self._convert)
        self.convert_button.pack(anchor="w")
        self.status = tk.Text(frame, height=9, state="disabled", wrap="word")
        self.status.pack(fill="both", expand=True, pady=(16, 0))

    def _group_changed(self) -> None:
        values = list(CATEGORIES[self.group.get()])
        self.category_box["values"] = values
        self.category.set(values[0])
        self.file.set("")

    def _choose(self) -> None:
        folder = ROOT / "input" / f"WAMI_{self.group.get()}"
        selected = filedialog.askopenfilename(initialdir=folder, filetypes=[("Excel workbooks", "*.xlsx")])
        if selected: self.file.set(selected)

    def _show(self, value: str) -> None:
        self.status.configure(state="normal"); self.status.delete("1.0", "end"); self.status.insert("end", value); self.status.configure(state="disabled")

    def _convert(self) -> None:
        if not self.file.get():
            messagebox.showwarning("File required", "Please choose an Excel workbook."); return
        self.convert_button.configure(state="disabled"); self.update_idletasks()
        try:
            result = convert_wawi_to_shopify(group=self.group.get(), category=self.category.get(), input_file=Path(self.file.get()), templates_dir=ROOT / "input" / "Templates", output_dir=ROOT / "output", logs_dir=ROOT / "logs")
            self._show(f"Processing complete.\n\nProducts: {result.products}\nVariants: {result.variants}\nWarnings: {len(result.warnings)}\n\nOutput:\n{result.output_file}")
            if messagebox.askyesno("Complete", "Conversion completed. Open the output folder?"):
                self._open_folder(ROOT / "output")
        except Exception as exc:
            self._show(f"Conversion failed:\n\n{exc}"); messagebox.showerror("Conversion failed", str(exc))
        finally:
            self.convert_button.configure(state="normal")

    @staticmethod
    def _open_folder(folder: Path) -> None:
        if sys.platform == "darwin": subprocess.run(["open", folder], check=False)
        elif sys.platform == "win32": subprocess.run(["explorer", folder], check=False)
        else: subprocess.run(["xdg-open", folder], check=False)


if __name__ == "__main__":
    ConverterApp().mainloop()
