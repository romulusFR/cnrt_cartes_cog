# pylint: disable = logging-fstring-interpolation
# type: ignore
"""Interface graphique"""

__author__ = "Romuald Thion"

import logging
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from cog_maps import (
    generate_results,
    INPUT_DIR,
    CM_LA_MINE_FILENAME,
    CM_FUTUR_FILENAME,
    THESAURUS_FILENAME,
    WEIGHTS_MAP_FILENAME,
    OUTPUT_DIR,
)

# violemment repris de
# https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget"""

    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.text = widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state="normal")
            self.text.insert(tk.END, msg + "\n")
            self.text.configure(state="disabled")
            # Autoscroll to the bottom
            self.text.yview(tk.END)

        # mystère
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


# fenetre générale
root = tk.Tk()
root.title("Calculateur de cartes cognitives")
s = ttk.Style()
s.theme_use("alt")
window = ttk.Frame(root)
window.pack(fill="both", expand=True)

# variables globales
cm_la_mine = tk.StringVar(window, CM_LA_MINE_FILENAME, "cm_la_mine")
cm_mine_futur = tk.StringVar(window, CM_FUTUR_FILENAME, "cm_mine_futur")
thesaurus = tk.StringVar(window, THESAURUS_FILENAME, "thesaurus")
weights = tk.StringVar(window, WEIGHTS_MAP_FILENAME, "weights")

output_dir = tk.StringVar(window, OUTPUT_DIR, "output_dir")
with_unknown = tk.BooleanVar(window, False)
report_unknown = tk.BooleanVar(window, True)


def uploader(variable, *, directory=False):
    """Générateur de handler"""

    def upload(_event=None):
        filename = ""
        if directory:
            filename = filedialog.askdirectory(initialdir=variable.get())
        else:
            filename = filedialog.askopenfilename(
                initialdir=INPUT_DIR,  # Path.cwd(),
                title="Choisir un fichier",
                filetypes=(("csv files", "*.csv"), ("all files", "*.*")),
                # initialfile=variable.get(),
            )
        if filename:
            logger.info(f"{__name__}.upload({variable}): selected {filename}")
            variable.set(filename)
        else:
            logger.info(f"{__name__}.upload({variable}): no file selected, keeping {variable.get()}")

    return upload


def compute(_event=None):
    """Lance le calcul"""
    generate_results(output_dir.get(), cm_la_mine.get(), thesaurus.get(), weights.get(), with_unknown.get())
    generate_results(output_dir.get(), cm_mine_futur.get(), thesaurus.get(), weights.get(), with_unknown.get())


# découpage en 3 panneaux
pack_params = {"fill": tk.X, "padx": 10}
top_frame = ttk.Frame(window)
top_frame.pack(side=tk.TOP)


cm_la_mine_btn = ttk.Button(top_frame, text="Cartes cog. 'la mine'")
cm_la_mine_btn.configure(command=uploader(cm_la_mine))
cm_la_mine_btn.pack(**pack_params, side=tk.LEFT)

cm_mine_futur_btn = ttk.Button(top_frame, text="Cartes cog. 'la mine futur'")
cm_mine_futur_btn.configure(command=uploader(cm_mine_futur))
cm_mine_futur_btn.pack(**pack_params, side=tk.LEFT)

thesaurus_btn = ttk.Button(top_frame, text="Thesaurus")
thesaurus_btn.configure(command=uploader(thesaurus))
thesaurus_btn.pack(**pack_params, side=tk.LEFT)

thesaurus_btn = ttk.Button(top_frame, text="Coefficients")
thesaurus_btn.configure(command=uploader(thesaurus))
thesaurus_btn.pack(**pack_params, side=tk.LEFT)


text_log = scrolledtext.ScrolledText(
    window, background="lightgrey", relief="sunken", width=120, height=12, state="disabled"
)
text_log.pack(expand=True, fill=tk.BOTH)
# Create textLogger
text_handler = TextHandler(text_log)


logger = logging.getLogger("COGNITIVE_MAP")
logger.addHandler(text_handler)
logger.setLevel(logging.INFO)


def clear_log():
    """mepty the log"""
    text_log.configure(state="normal")
    text_log.delete("1.0", tk.END)
    text_log.configure(state="disabled")


mid_frame = ttk.Frame(window)
mid_frame.pack()  # side=tk.BOTTOM
generate_btn = ttk.Button(mid_frame, text="Calculer les cartes", command=compute)
generate_btn.pack(**pack_params, side=tk.LEFT)
clear_btn = ttk.Button(mid_frame, text="Vider la console", command=clear_log)
clear_btn.pack(**pack_params, side=tk.LEFT)

sep_mid_bot = ttk.Separator(window, orient="horizontal")
sep_mid_bot.pack(fill="x", pady=5)

bot_frame = ttk.Frame(window)
bot_frame.pack()  # side=tk.BOTTOM
output_btn = ttk.Button(bot_frame, text="Choisir le dossier de sortie")
output_btn.configure(command=uploader(output_dir, directory=True))
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
