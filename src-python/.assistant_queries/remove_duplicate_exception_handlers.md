Clarification needed: which duplicate exception handlers should I remove?

I can make the change, but I need a quick confirmation about scope and intent.

Observed possibilities (from the files you added):
- backend/services/trading_service.py:
  - Several adjacent/duplicated exception handlers after order placement and simulation blocks.
  - Duplicate 'else' / nested control-flow fixes were already addressed earlier, but there may still be repeated
    `except Exception:` blocks that were copied twice or multiple identical handlers around the same try.
- backend/services/citadel.py:
  - Broad except: pass blocks in load_state/save_state and others — do you want these left as-is (best-effort silent failure)
    or converted to logged warnings/errors?
- Other files (settings.py etc.) appear fine.

Please answer these (pick options or provide instructions):
1) Target files: I should edit (select one or more)
   - trading_service.py
   - citadel.py
   - both
   - other: (list paths)

2) Strategy (choose one):
   A) Conservative — remove only exact duplicated except/handler blocks that appear back-to-back (minimal risk).
   B) Sanitize — consolidate multiple adjacent generic handlers into a single handler that logs the exception once.
   C) Aggressive — replace broad `except:`/`except Exception:` patterns with specific exception classes and add logging (may require adding imports or deeper logic).

3) Logging policy for replaced handlers:
   - Keep silent (use `pass`) — low noise (not recommended).
   - Log at DEBUG level — record but low noise.
   - Log at ERROR/CRITICAL — always visible.

Recommended default (safe):
- Files: trading_service.py
- Strategy: A) Conservative — remove exact duplicate adjacent except blocks and ensure only one handler remains per try.
- Logging: DEBUG (avoid spam in prod logs).

If you confirm (e.g., reply "OK: trading_service.py, Conservative, DEBUG"), I'll:
1) Produce exact SEARCH/REPLACE edits for each file selected (only the files you added).
2) Keep edits minimal and create unit-friendly changes.
3) Suggest a shell command to run tests / start the service.

Suggested quick commands you can run after I provide edits (I will include one when ready):
- python backend/main.py

Reply with your choice.
