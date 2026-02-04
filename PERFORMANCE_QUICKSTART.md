# Performance Optimization Quick Start

Fast-track guide to implementing Dharmic Agent performance optimizations.

---

## TL;DR

**Problem**: System will crash after 24 hours due to memory growth and slow vault searches.

**Solution**: 5 code patches that give 10-100x speedup.

**Time**: 2-4 hours to implement, 2 hours to test.

---

## Step 1: Baseline Measurement (5 minutes)

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW

# Run baseline benchmarks
python3 benchmark_performance.py --baseline

# Note the results - they'll be saved automatically
```

---

## Step 2: Backup Files (1 minute)

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/src/core

# Create backups
cp vault_bridge.py vault_bridge.py.backup
cp email_daemon.py email_daemon.py.backup
cp dharmic_agent.py dharmic_agent.py.backup
cp deep_memory.py deep_memory.py.backup
cp daemon.py daemon.py.backup

echo "Backups created"
```

---

## Step 3: Apply Critical Patches (1-2 hours)

### Patch 1: Vault Indexing (99% speedup)

**File**: `vault_bridge.py`

Open the file and apply these 3 changes:

1. **Line 31**: Change `def __init__(self, vault_path: str = None):` to:
   ```python
   def __init__(self, vault_path: str = None, lazy_init: bool = True):
   ```

2. **After line 48** (after `self.policy = PSMVPolicy()`), add:
   ```python
   # Search index for fast lookups
   self._index = None
   self._index_path = self.vault_path / ".vault_index.pkl"
   if not lazy_init:
       self._build_index()
   ```

3. **Before line 58** (before `get_vault_summary`), add the `_build_index()` method:
   Copy from `OPTIMIZATION_PATCHES.md` section 1.3 (about 60 lines)

4. **Replace `search_vault()` method** (line 228):
   Copy from `OPTIMIZATION_PATCHES.md` section 1.4 (about 80 lines)

**Test**:
```bash
python3 -c "
from src.core.vault_bridge import VaultBridge
import time
start = time.time()
vault = VaultBridge(lazy_init=False)
print(f'Index build: {time.time()-start:.2f}s')
start = time.time()
results = vault.search_vault('witness', 10)
print(f'Search: {time.time()-start:.3f}s, {len(results)} results')
"
```

Expected: Index build 2-3s, search <100ms

---

### Patch 2: IMAP Connection Pooling (75% speedup)

**File**: `email_daemon.py`

1. **After line 107**, add:
   ```python
   # IMAP connection pooling
   self._imap_connection = None
   self._imap_last_used = None
   self._imap_idle_timeout = 600
   ```

2. **After `connect_imap()` method**, add `_get_imap_connection()`:
   Copy from `OPTIMIZATION_PATCHES.md` section 2.2 (about 20 lines)

3. **Line 136** in `fetch_unread()`, change:
   ```python
   mail = self.connect_imap()  # OLD
   mail = self._get_imap_connection()  # NEW
   ```

4. **Line 185**, remove:
   ```python
   mail.logout()  # DELETE THIS LINE
   ```

5. **In `stop()` method**, add cleanup:
   ```python
   if self._imap_connection:
       try:
           self._imap_connection.logout()
       except:
           pass
   ```

**Test**:
```bash
python3 src/core/email_daemon.py --test
```

---

### Patch 3: Strange Memory Caching (95% speedup)

**File**: `dharmic_agent.py`

1. **After line 170** (in `StrangeLoopMemory.__init__`), add:
   ```python
   # Cache for recent entries
   self._cache = {}
   self._cache_mtime = {}
   ```

2. **Replace `_read_recent()` method** (line 182):
   Copy from `OPTIMIZATION_PATCHES.md` section 3.2 (about 40 lines)

3. **In `_append()` method**, add cache invalidation:
   Copy from `OPTIMIZATION_PATCHES.md` section 3.3 (about 8 lines)

**Test**:
```bash
python3 -c "
from src.core.dharmic_agent import DharmicAgent
import time
agent = DharmicAgent()

# First read (cold)
start = time.time()
obs1 = agent.strange_memory._read_recent('observations', 10)
t1 = time.time() - start

# Second read (cached)
start = time.time()
obs2 = agent.strange_memory._read_recent('observations', 10)
t2 = time.time() - start

print(f'Cold: {t1*1000:.2f}ms, Cached: {t2*1000:.2f}ms')
print(f'Speedup: {t1/t2:.1f}x')
"
```

Expected: 10-20x speedup on cached reads

---

## Step 4: High Priority Patches (1-2 hours)

### Patch 4: Deep Memory Caching

**File**: `deep_memory.py`

1. **After line 102**, add cache fields
2. **Replace `search_memories()` method** with cached version

Details in `OPTIMIZATION_PATCHES.md` section 4.

---

### Patch 5: Memory Maintenance

**File**: `daemon.py`

1. **After line 134**, add GC job to scheduler
2. **Add `_memory_maintenance()` method**

Details in `OPTIMIZATION_PATCHES.md` section 5.

---

## Step 5: Validate (30 minutes)

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW

# Run optimized benchmarks
python3 benchmark_performance.py --optimized

# Compare results
python3 benchmark_performance.py --compare
```

**Success Criteria**:
- Vault search: >90% improvement
- Email poll: >70% improvement
- Memory reads: >90% improvement
- No errors in tests

---

## Step 6: Integration Test (1 hour)

```bash
# Test daemon startup
cd /Users/dhyana/DHARMIC_GODEL_CLAW
python3 src/core/daemon.py --heartbeat 60 &
PID=$!

# Wait 5 minutes, check logs
sleep 300
tail logs/daemon_*.log

# Check memory usage
ps aux | grep $PID

# Graceful shutdown
kill $PID
```

**Success Criteria**:
- Daemon starts without errors
- Heartbeat completes in <100ms
- Memory stable at <200MB
- No crashes or exceptions

---

## Step 7: 24-Hour Stability Test (optional but recommended)

```bash
# Start daemon
cd /Users/dhyana/DHARMIC_GODEL_CLAW
nohup python3 src/core/daemon.py --heartbeat 3600 > logs/daemon_stability.log 2>&1 &
PID=$!
echo $PID > logs/daemon.pid

# Monitor for 24 hours
# Check memory every hour:
watch -n 3600 'ps aux | grep $PID'

# After 24 hours, check results
cat logs/daemon_stability.log
# Expected: No errors, memory <500MB, consistent heartbeat times
```

---

## Rollback (if needed)

```bash
cd /Users/dhyana/DHARMIC_GODEL_CLAW/src/core

# Restore backups
mv vault_bridge.py.backup vault_bridge.py
mv email_daemon.py.backup email_daemon.py
mv dharmic_agent.py.backup dharmic_agent.py
mv deep_memory.py.backup deep_memory.py
mv daemon.py.backup daemon.py

echo "Restored to pre-optimization state"
```

---

## Troubleshooting

### Issue: "Index build fails"

**Symptoms**: Error during vault index creation
**Solution**:
```bash
# Remove corrupted index
rm ~/Persistent-Semantic-Memory-Vault/.vault_index.pkl
# Try again - it will rebuild
```

### Issue: "IMAP connection timeout"

**Symptoms**: Email polling fails after period of inactivity
**Solution**: Already handled - connection will automatically reconnect on NOOP failure

### Issue: "Cache returns stale data"

**Symptoms**: Changes not reflected immediately
**Solution**: Caches check mtime - wait 1 second after write before reading

### Issue: "Memory still growing"

**Symptoms**: Memory >1GB after 24 hours
**Solution**:
```bash
# Force manual GC
python3 -c "
import gc
gc.collect(generation=2)
"
# Check if GC maintenance job is running
grep "Memory maintenance" logs/daemon_*.log
```

---

## Expected Results Summary

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Vault search | 2-5s | <100ms | ✓ 95%+ faster |
| Email poll | 500ms | <150ms | ✓ 70%+ faster |
| Memory reads | 20ms | <1ms | ✓ 95%+ faster |
| 24hr memory | 2-4GB | <500MB | ✓ 85% reduction |
| Startup | 483ms | <300ms | ✓ 38% faster |

---

## Common Questions

**Q: Can I apply patches incrementally?**
A: Yes! Each patch is independent. Apply and test one at a time.

**Q: Will this break existing functionality?**
A: No. All changes are backward-compatible optimizations.

**Q: How long until I see improvements?**
A: Immediately after applying patches. Run benchmarks to verify.

**Q: What if I only have time for one patch?**
A: Patch 1 (Vault Indexing) gives biggest win - 99% speedup on searches.

**Q: Do I need to restart the daemon?**
A: Yes, after applying patches, restart the daemon for changes to take effect.

---

## Next Steps After Optimization

1. **Set up monitoring** (see `PERFORMANCE_ANALYSIS.md` section on Monitoring)
2. **Configure alerts** for memory >1GB, heartbeat >500ms
3. **Document any custom adjustments** for your specific use case
4. **Share results** - update this doc with your actual before/after metrics

---

## Full Documentation

For deep technical details:
- **PERFORMANCE_ANALYSIS.md** - Complete analysis with theory
- **OPTIMIZATION_PATCHES.md** - Exact code for each patch
- **PERFORMANCE_SUMMARY.md** - Executive overview
- **benchmark_performance.py** - Automated testing tool

---

*Goal: 24/7 stable operation with <500MB memory and <1.5s email responses*
