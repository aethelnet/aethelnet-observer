Files requested for further edits (please add these to the chat so I can propose precise SEARCH/REPLACE edits):

1. .env (project root)
   - Why: I will simplify the .env to a minimal template with only secret keys and comments that defaults come from settings.py.
   - Action: Please add the current .env file contents so I can comment-out non-essential entries and produce a minimal template.

2. backend/config/SETTINGS_GUIDE.md
   - Why: Update documentation to reflect safer defaults (EXECUTION_ENABLED=False), STOP_LOSS settings, and the minimal .env approach.
   - Action: Add this file so I can update sections and examples.

3. backend/GOING_LIVE.md
   - Why: Update the "going live" checklist with the new settings and safety checks (per-trade stop loss, citadel limits, lockfile process checks).
   - Action: Add this file so I can ensure docs match code and provide final steps.

Optional but recommended:
- tests/test_risk_controls.py
  - Why: Add unit tests that validate STOP_LOSS enforcement behavior and settings validation.
  - Action: If you want tests added now, include the current tests folder or allow me to create a new test file.

Short plan after you add the files:
- Update .env to a minimal template and comment guidance.
- Update docs to reflect new safer defaults and STOP_LOSS_ENABLED.
- If desired, add a small unit test verifying the settings validator rejects invalid STOP_LOSS values.

Once you add the requested files, I will produce exact SEARCH/REPLACE edits for them.
