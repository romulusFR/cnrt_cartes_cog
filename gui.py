# pylint: disable = logging-fstring-interpolation
# type: ignore
"""Interface graphique"""

__author__ = "Romuald Thion"

import logging
import tkinter as tk
from io import StringIO
from tkinter import filedialog, ttk
from cartes_cog import generate_results

log_stream = StringIO()
logging.basicConfig(stream=log_stream)
# logging.basicConfig()
logger = logging.getLogger("COGNITIVE_MAP")
logger.setLevel(logging.INFO)


root = tk.Tk()
root.title("Calculateur de cartes cognitives")
s = ttk.Style()
s.theme_use("alt")
window = ttk.Frame(root)
window.pack(fill="both", expand=True)


# variables globales
cartes_cog_la_mine = tk.StringVar(window, "input/cartes_cog_la_mine.csv")
thesaurus_la_mine = tk.StringVar(window, "input/thesaurus_la_mine.csv")
cartes_cog_mine_futur = tk.StringVar(window, "input/cartes_cog_mine_futur.csv")
thesaurus_mine_futur = tk.StringVar(window, "input/thesaurus_mine_futur.csv")

output = tk.StringVar(window, "output")
with_unknown = tk.BooleanVar(window, False)
report_unknown = tk.BooleanVar(window, False)


def uploader(variable, *, directory=False):
    """Générateur de handler"""

    def upload(_event=None):
        filename = ""
        if directory:
            filename = filedialog.askdirectory(initialdir=variable.get())
        else:
            filename = filedialog.askopenfilename(
                title="Choisir un fichier de cartes",
                filetypes=(("csv files", "*.csv"), ("all files", "*.*")),
                initialfile=variable.get(),
            )
        logger.info(f"Selected: {filename}")
        variable.set(filename)

    return upload


def compute(_event=None):
    """Lance le calcul"""
    generate_results(output.get(), cartes_cog_la_mine.get(), thesaurus_la_mine.get(), with_unknown.get())
    generate_results(output.get(), cartes_cog_mine_futur.get(), thesaurus_mine_futur.get(), with_unknown.get())

    text_log.insert("1.0", log_stream.getvalue())
    log_stream.truncate(0)
    log_stream.seek(0)


pack_params = {"fill": tk.X, "padx": 10}

top_frame = ttk.Frame(window)
top_frame.pack(side=tk.TOP)
left_frame = ttk.Frame(top_frame)
left_frame.pack(side=tk.LEFT)
right_frame = ttk.Frame(top_frame)
right_frame.pack(side=tk.RIGHT)
cartes_btn = ttk.Button(left_frame, text="Cartes cognitives la mine")
cartes_btn.configure(command=uploader(cartes_cog_la_mine))
cartes_btn.pack(**pack_params, side=tk.TOP)
ontologie_btn = ttk.Button(left_frame, text="Thesaurus la mine")
ontologie_btn.configure(command=uploader(thesaurus_la_mine))
ontologie_btn.pack(**pack_params, side=tk.BOTTOM)
cartes_btn = ttk.Button(right_frame, text="Cartes cognitives la mine dans le futur")
cartes_btn.configure(command=uploader(cartes_cog_mine_futur))
cartes_btn.pack(**pack_params, side=tk.TOP)
ontologie_btn = ttk.Button(right_frame, text="Thesaurus la mine dans  futur")
ontologie_btn.configure(command=uploader(thesaurus_mine_futur))
ontologie_btn.pack(**pack_params, side=tk.BOTTOM)


text_log = tk.Text(window, background="lightgrey", relief="sunken", width=120, height=12)
text_log.pack(expand=True, fill=tk.BOTH)


mid_frame = ttk.Frame(window)
mid_frame.pack()  # side=tk.BOTTOM
generate_btn = ttk.Button(mid_frame, text="Calculer les cartes", command=compute)
generate_btn.pack(**pack_params, side=tk.LEFT)
clear_btn = ttk.Button(mid_frame, text="Vider la console", command=lambda: text_log.delete("1.0", tk.END))
clear_btn.pack(**pack_params, side=tk.LEFT)

sep_mid_bot = ttk.Separator(window, orient="horizontal")
sep_mid_bot.pack(fill="x", pady=5)

bot_frame = ttk.Frame(window)
bot_frame.pack()  # side=tk.BOTTOM
output_btn = ttk.Button(bot_frame, text="Choisir le dossier de sortie")
output_btn.configure(command=uploader(output, directory=True))
output_btn.pack(**pack_params, side=tk.LEFT)
with_unknown_chk = ttk.Checkbutton(
    bot_frame, text="Générer les cartes mères avec concept inconnu", variable=with_unknown, onvalue=True, offvalue=False
)
with_unknown_chk.pack(**pack_params, side=tk.LEFT)
report_unknown_chk = ttk.Checkbutton(
    bot_frame, text="Générer un rapport des concepts inconnus", variable=report_unknown, onvalue=True, offvalue=False
)
report_unknown_chk.pack(**pack_params, side=tk.LEFT)


window.mainloop()
