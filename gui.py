# pylint: disable = logging-fstring-interpolation
# type: ignore
"""Interface graphique"""

__author__ = "Romuald Thion"

import logging
from io import StringIO
import tkinter as tk
from tkinter import filedialog, ttk
from cartes_cog import (
    CARTES_COG_FILE_DEFAULT,
    ONTOLOGIE_FILE_DEFAULT,
    OUTPUT_DIR,
    generate_results,
)

log_stream = StringIO()
logging.basicConfig(stream=log_stream)
# logging.basicConfig()
logger = logging.getLogger("COGNITIVE_MAP")
logger.setLevel(logging.INFO)

window = tk.Tk()
window.title("Calculateur de cartes cognitives")


# variables globales
cartes_cognitives = tk.StringVar(window, CARTES_COG_FILE_DEFAULT)
ontologie = tk.StringVar(window, ONTOLOGIE_FILE_DEFAULT)
output = tk.StringVar(window, OUTPUT_DIR)
with_unknown = tk.BooleanVar(window, False)


def uploader(variable, *, directory=False):
    """Générateur de handler"""

    def upload(_event=None):
        filename = ""
        if directory:
            filename = filedialog.askdirectory()
        else:
            filename = filedialog.askopenfilename(
                title="Choisir un fichier de cartes", filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
            )
        logger.info(f"Selected: {filename}")
        variable.set(filename)

    return upload


def compute(_event=None):
    """Lance le calcul"""
    generate_results(output.get(), cartes_cognitives.get(), ontologie.get(), with_unknown.get())

    text_log.insert("1.0", log_stream.getvalue())
    log_stream.truncate(0)
    log_stream.seek(0)


pack_params = {"fill": tk.X, "padx": 10}

top_frame = tk.Frame(window)
top_frame.pack(side=tk.TOP)


cartes_btn = tk.Button(top_frame, text="Choisir les cartes cognitives")
cartes_btn.configure(command=uploader(cartes_cognitives))
cartes_btn.pack(**pack_params, side=tk.LEFT)

ontologie_btn = tk.Button(top_frame, text="Choisir l'ontologie")
ontologie_btn.configure(command=uploader(ontologie))
ontologie_btn.pack(**pack_params, side=tk.RIGHT)

sep_top_mid = ttk.Separator(window, orient="horizontal")
sep_top_mid.pack(fill="x", pady=5)

mid_frame = tk.Frame(window)
mid_frame.pack(side=tk.TOP)


output_btn = tk.Button(mid_frame, text="Choisir le dossier de sortie")
output_btn.configure(command=uploader(output, directory=True))
output_btn.pack(**pack_params, side=tk.LEFT)

with_unknown_chk = tk.Checkbutton(
    mid_frame, text="Générer les cartes mères avec concept inconnu", variable=with_unknown, onvalue=True, offvalue=False
)
with_unknown_chk.pack(**pack_params, side=tk.LEFT)


text_log = tk.Text(window, background="lightgrey", relief="sunken", width=120, height=12)
text_log.pack(expand=True, fill=tk.BOTH)


bot_frame = tk.Frame(window)
bot_frame.pack(side=tk.BOTTOM)


generate_btn = tk.Button(bot_frame, text="Calculer", bg="blue", fg="white", command=compute)
generate_btn.pack(**pack_params, side=tk.LEFT)

clear_btn = tk.Button(bot_frame, text="Clear", command=lambda: text_log.delete("1.0", tk.END))
clear_btn.pack(**pack_params, side=tk.LEFT)


window.mainloop()
