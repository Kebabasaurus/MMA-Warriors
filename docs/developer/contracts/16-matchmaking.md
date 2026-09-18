## 8. Matchmaking and Availability

Matchmaking is event-date aware. `fighter.status` describes the fighter's current condition; it is
not enough to decide whether the fighter can compete on a future date.

- Use `fighter_booking_status(fighter, month, week)` for the human-readable week-level state.
- Use `fighter_available_for_date(fighter, month, week, day)` for authoritative named-day
  eligibility.
- Refresh available fighters immediately when event year, month, or week changes.
- The default `Ready` filter means ready for the selected event date.
- The `All` filter may show unavailable fighters with a precise label such as
  `Available Mar W3 2026`.
- Routine conflicts belong in the inline matchmaking notice, not a native Windows message box.

Example:

```python
status = self.fighter_booking_status(fighter, selected_month, selected_week)
event_day = self.selected_booking_day()
if self.fighter_available_for_date(fighter, selected_month, selected_week, event_day):
    eligible.append(fighter)
else:
    display_unavailable(fighter, status)
```

