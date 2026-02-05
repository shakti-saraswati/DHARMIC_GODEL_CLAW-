import os
import sys
from pathlib import Path

# Add the project root to sys.path so we can import swarm
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from swarm.run_gates import GateRunner

def test_ckc_trigger():
    print("Setting DGC_YOLO_MODE=1...")
    os.environ["DGC_YOLO_MODE"] = "1"
    
    print("Instantiating GateRunner...")
    runner = GateRunner(config_path=project_root / "swarm" / "gates.yaml")
    
    print("Running gates (dry-run mode)...")
    
    result = runner.run_all_gates(proposal_id="TEST-CKC-001", dry_run=True)
    
    # Check if CKC gates are present in the results
    gate_ids = [res['gate_id'] for res in result.gate_results]
    
    print("Executed Gate IDs:", gate_ids)
    
    if "CKC_META_CHECK" in gate_ids:
        print("SUCCESS: CKC_META_CHECK was triggered!")
    else:
        print("FAILURE: CKC_META_CHECK was NOT triggered.")
        sys.exit(1)

    if "CKC_SPEED_LIMIT" in gate_ids:
        print("SUCCESS: CKC_SPEED_LIMIT was triggered!")
    else:
        print("FAILURE: CKC_SPEED_LIMIT was NOT triggered.")
        sys.exit(1)

if __name__ == "__main__":
    test_ckc_trigger()