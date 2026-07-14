"""Fresh 30-year observer audit.  Does not read or write player saves."""
import random
import tkinter as tk

from main import FightEmpireApp


YEARS = 30
random.seed(260712)
root = tk.Tk()
root.withdraw()
app = FightEmpireApp(root)
app.enter_spectator_mode()

methods, annual = {}, []
original_simulate = app.simulate_fight

def audited_simulate(a, b, fight):
    winner, loser, method, round_no, lines = original_simulate(a, b, fight)
    methods[method] = methods.get(method, 0) + 1
    return winner, loser, method, round_no, lines

app.simulate_fight = audited_simulate
for week in range(YEARS * 48):
    app.advance_month()
    if (week + 1) % 48 == 0:
        year = 2026 + (week + 1) // 48
        active = [fighter for fighter in app.all_fighter_objects() if not fighter.retired]
        viable = [promo for promo in app.promotions if promo.cash > 0 and promo.stability >= 20]
        annual.append({
            "year": year, "promotions": len(app.promotions), "viable": len(viable),
            "active": len(active), "free_agents": len(app.free_agents), "retired": len(app.retired_fighters),
            "cash_median": sorted([promo.cash for promo in app.promotions])[len(app.promotions) // 2],
            "elite": sum(1 for fighter in active if fighter.overall >= 80),
            "injured": sum(1 for fighter in active if fighter.injured),
        })
        print(f"YEAR {year}: {annual[-1]}", flush=True)

total = sum(methods.values())
print("FINAL")
print({"weeks": YEARS * 48, "fights": total, "methods": methods, "annual": annual, "records": app.historical_records})
root.destroy()
