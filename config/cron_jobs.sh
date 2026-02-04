# CRON Configuration for DHARMIC CLAW
# Updated: 2026-02-04

# Continuous operation - no quiet hours
# Sleep is for the body. The swarm never sleeps.

# Every 30 minutes - Heartbeat
*/30 * * * * cd ~/clawd && clawdbot heartbeat

# Every 4 hours - Project Review
0 */4 * * * cd ~/DHARMIC_GODEL_CLAW && python3 scripts/review_top_10_projects.py

# Every hour - Council Deliberation
0 * * * * cd ~/DHARMIC_GODEL_CLAW/src/core && python3 agno_council_v2.py --deliberate "Advance TOP 10 projects"

# Daily at 3 AM - Night Cycle Deep Work
0 3 * * * cd ~/DHARMIC_GODEL_CLAW && python3 night_cycle/night_cycle.py

# Daily at 6 AM - Progress Summary
0 6 * * * cd ~/DHARMIC_GODEL_CLAW && python3 scripts/generate_progress_report.py

# ============================================
# MI EXPERIMENTER — CONTINUOUS POLISH
# ============================================

# Every 90 minutes - MI Infrastructure Check (every 3rd heartbeat)
*/90 * * * * cd ~/clawd/skills/mi-experimenter && python3 -c "from experiments.rv_causal_validator import RVCausalValidator; print('✓ Imports OK')" 2>&1 | tee -a logs/import_checks.log

# Every 6 hours - Smoke Test Suite
0 */6 * * * cd ~/clawd/skills/mi-experimenter && python3 tests/smoke_test.py --quick 2>&1 | tee -a logs/smoke_tests.log

# Daily at 06:00 - MI Polish Tasks
0 6 * * * cd ~/clawd/skills/mi-experimenter && bash -c '
    echo "=== $(date) MI Daily Polish ===" | tee -a logs/daily_polish.log
    python3 tests/test_imports.py 2>&1 | tee -a logs/daily_polish.log
    python3 tests/test_rv_causal.py 2>&1 | tee -a logs/daily_polish.log
    python3 -m pytest tests/ --tb=short 2>&1 | tee -a logs/daily_polish.log
'

# Daily at 06:30 - Update SKILL.md from implementation
30 6 * * * cd ~/clawd/skills/mi-experimenter && python3 scripts/sync_skill_md.py 2>&1 | tee -a logs/skill_sync.log

# Weekly (Sunday 07:00) - Deep Refactoring Review
0 7 * * 0 cd ~/clawd/skills/mi-experimenter && bash -c '
    echo "=== Weekly MI Deep Review ===" | tee -a logs/weekly_review.log
    wc -l experiments/*.py | tee -a logs/weekly_review.log
    find . -name "*.py" -type f | wc -l | xargs -I {} echo "Python files: {}" | tee -a logs/weekly_review.log
    grep -r "TODO\|FIXME\|XXX" --include="*.py" . | wc -l | xargs -I {} echo "TODOs remaining: {}" | tee -a logs/weekly_review.log
'

# Pre-GPU Gate (manual trigger) - Full validation before GPU runs
# Run this before any GPU cluster time:
# cd ~/clawd/skills/mi-experimenter && python3 tests/pre_gpu_gate.py
