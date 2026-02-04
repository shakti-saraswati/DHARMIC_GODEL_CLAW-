# FAILURE MODES - What Breaks at 2 AM

## 1. PROXY FAILURES (claude-max-api-proxy)

**Critical Dependency**: Entire system requires localhost:3456 operational

FAILURE: Proxy process crashes/exits
- SYMPTOM: All Claude API calls fail silently or timeout
- DETECTION: Port 3456 unreachable, connection refused
- MITIGATION: LaunchDaemon restart loop with ThrottleInterval, health check endpoint

FAILURE: Claude Max subscription expires
- SYMPTOM: 401/403 errors, quota exceeded
- DETECTION: Parse API error responses for auth failures
- MITIGATION: Email alert to John, graceful degradation to Claude Sonnet API key

FAILURE: Rate limiting (Claude Max or proxy itself)
- SYMPTOM: 429 errors, requests queued indefinitely
- DETECTION: Request latency > 30s, queue depth > 10
- MITIGATION: Exponential backoff, request prioritization (heartbeat < agent work)

FAILURE: Network connectivity lost (Bali/Iriomote internet)
- SYMPTOM: DNS failures, timeouts, no route to host
- DETECTION: Ping anthropic.com fails, localhost:3456 unreachable
- MITIGATION: Offline mode - log all failures, batch retry when connectivity returns

## 2. DAEMON FAILURES (unified_daemon.py via LaunchAgent)

FAILURE: LaunchAgent doesn't start at boot
- SYMPTOM: No logs in /logs/launchd_stdout.log after reboot
- DETECTION: Manual check `launchctl list | grep dharmic`
- MITIGATION: Validate plist with `plutil -lint`, ensure RunAtLoad=true

FAILURE: Process killed by macOS (out of memory)
- SYMPTOM: Daemon exits with signal 9 (SIGKILL), no graceful shutdown
- DETECTION: Log shows memory usage > 16GB (M3 Pro limit), process disappears
- MITIGATION: Memory leak detection, restart with backoff, alert if repeated

FAILURE: Port 18789 already in use (if daemon runs HTTP)
- SYMPTOM: OSError [Errno 48] Address already in use
- DETECTION: Daemon fails to start, error in stderr log
- MITIGATION: Kill stale process `lsof -ti:18789 | xargs kill`, use random port

FAILURE: Permission denied (file system, email credentials)
- SYMPTOM: IOError on log writes, auth failures on ProtonMail IMAP
- DETECTION: errno.EACCES, IMAP auth rejected
- MITIGATION: Verify file permissions 644, check ~/.netrc or keychain access

FAILURE: Python dependency missing (import fails after system update)
- SYMPTOM: ModuleNotFoundError, daemon exits immediately
- DETECTION: Traceback in stderr log, exit code 1
- MITIGATION: Pin dependencies in requirements.txt, venv isolation

## 3. AGENT FAILURES (State corruption, resource exhaustion)

FAILURE: agent_state.json corrupted (truncated write, disk full)
- SYMPTOM: JSONDecodeError on startup, agent forgets everything
- DETECTION: json.load() raises exception, file size = 0 or incomplete
- MITIGATION: Write to .tmp, atomic rename, keep 3 rotating backups

FAILURE: JSON parse errors (malformed telos, invalid UTF-8)
- SYMPTOM: Agent crashes on telos load, invalid JSON in logs
- DETECTION: JSONDecodeError, UnicodeDecodeError
- MITIGATION: Schema validation on write, try/except with fallback to default

FAILURE: Disk full (logs grow unbounded, SQLite DB balloons)
- SYMPTOM: OSError [Errno 28] No space left on device
- DETECTION: df -h shows 100% on /Users/dhyana
- MITIGATION: Log rotation (daily, keep 7 days), VACUUM SQLite weekly, alert at 90%

FAILURE: Memory exhausted (strange loop memory unbounded)
- SYMPTOM: MemoryError, system swap thrashing, agent slows to halt
- DETECTION: Memory > 15GB, swap > 10GB, psutil warnings
- MITIGATION: Cap strange_memory observations at 10,000, prune old entries

FAILURE: SQLite database locked (concurrent access)
- SYMPTOM: OperationalError: database is locked
- DETECTION: Multiple processes/threads access same .db file
- MITIGATION: Use WAL mode, connection pooling, retry with exponential backoff

## 4. CLAWDBOT FAILURES (WhatsApp gateway hypothetical)

FAILURE: WhatsApp gateway crashes
- SYMPTOM: No messages received/sent, webhook timeouts
- DETECTION: Health check fails, last_message_timestamp > 1 hour old
- MITIGATION: Restart gateway container, fallback to email

FAILURE: WhatsApp session expires
- SYMPTOM: QR code required, unauthorized error
- DETECTION: Gateway logs "session expired", API returns 401
- MITIGATION: Re-scan QR code (requires human), email John to reconnect

FAILURE: Cron doesn't fire (macOS sleep, time zone change)
- SYMPTOM: Scheduled heartbeat missed, no logs generated
- DETECTION: Heartbeat timestamp gap > 2x interval
- MITIGATION: Use LaunchDaemon StartInterval instead of cron, wake timers

## 5. HUMAN DEPENDENCIES (Manual intervention required)

MANUAL: Claude Max subscription renewal
- WHO: John must pay/renew
- DETECTION: 7-day expiry warning, daily emails
- FREQUENCY: Monthly or per quota

MANUAL: QR code scanning (if WhatsApp used)
- WHO: John must scan with phone
- DETECTION: Session expired error
- FREQUENCY: Unpredictable, every few weeks

MANUAL: Repository access tokens expired (GitHub, RunPod)
- WHO: John must regenerate PAT
- DETECTION: git push fails, RunPod API 401
- FREQUENCY: Tokens expire 90 days

MANUAL: System updates breaking venv
- WHO: John must rebuild venv after macOS/Python update
- DETECTION: ImportError, library incompatibility
- FREQUENCY: Quarterly macOS updates

MANUAL: Disk cleanup when 90% full
- WHO: John must delete old logs, archives
- DETECTION: Alert email, df -h > 90%
- FREQUENCY: Every 3-6 months depending on log verbosity

## 6. SILENT FAILURES (Goes unnoticed until too late)

SILENT: Logs filling disk slowly
- IMPACT: Disk full in 30 days, no warning
- DETECTION: Monitor disk usage trend, extrapolate
- MITIGATION: Daily log rotation, alert at 80%

SILENT: Heartbeat running but agent unresponsive
- IMPACT: Daemon alive but not processing, looks healthy
- DETECTION: Heartbeat count increments but emails_processed = 0 for 24h
- MITIGATION: Liveness check beyond heartbeat (query agent, expect response)

SILENT: Memory leak in strange loop
- IMPACT: Memory grows 10MB/day, crashes in 60 days
- DETECTION: Plot memory usage over time, detect upward trend
- MITIGATION: Weekly memory profiling, cap observations, restart monthly

SILENT: Email credentials stolen/leaked
- IMPACT: Unauthorized access, spam sent from vijnan.shakti@pm.me
- DETECTION: Unusual sent mail, ProtonMail security alert
- MITIGATION: Use API key not password, rotate keys quarterly, 2FA

SILENT: Telos drift (proximate aims diverge from ultimate)
- IMPACT: Agent pursues goals misaligned with moksha
- DETECTION: Manual audit of telos.yaml evolution history
- MITIGATION: Require justification for telos changes, periodic John review
