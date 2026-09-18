import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import FightEmpireApp


root = tk.Tk()
root.withdraw()
app = FightEmpireApp(root)
app.ensure_screen_built("sim_lab")
app.play_audit_years.set(2)
app.play_audit_seed.set(260720)
app.run_play_level_audit()
root.destroy()
