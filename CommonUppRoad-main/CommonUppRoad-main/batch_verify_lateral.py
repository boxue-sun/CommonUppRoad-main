"""
batch_verify_lateral.py
批量验证横向实验的 UPPAAL 模型
"""
import subprocess
import os
import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_lateral", "models")
PARAM_TABLE = os.path.join(os.path.dirname(__file__), "experiments", "exp_lateral", "param_table.json")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "experiments", "exp_lateral", "results.csv")

QUERY_FILE = os.path.join(MODELS_DIR, "_query.q")

def verify_model(model_path):
    try:
        result = subprocess.run(
            [VERIFYTA, "-s", model_path, QUERY_FILE],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout + result.stderr
        if "NOT satisfied" in output:
            return False  # Collision
        elif "satisfied" in output:
            return True   # Safe
        else:
            return None
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    with open(PARAM_TABLE, 'r', encoding='utf-8') as f:
        param_data = json.load(f)

    mutations = param_data['mutations']
    print(f"Total variants: {len(mutations)}")
    print("=" * 60)

    # Create query file
    with open(QUERY_FILE, 'w') as f:
        f.write("A[] !cps_i_state.detection.collide\n")

    results = []
    collision_count = 0
    safe_count = 0
    error_count = 0

    for i, mutation in enumerate(mutations):
        model_file = os.path.join(MODELS_DIR, f"variant_{i:04d}.xml")
        if not os.path.exists(model_file):
            results.append({'variant_id': i, 'params': json.dumps(mutation), 'collision_found': 'NOT_FOUND'})
            error_count += 1
            continue

        print(f"[{i:3d}/{len(mutations)}] lat={mutation['lateral_offset']:+4.0f}m "
              f"head={mutation['heading_offset']:+.1f}rad vel×{mutation['speed_factor']:.1f} -> ", end="", flush=True)
        result = verify_model(model_file)

        if result == False:
            print("COLLISION!")
            collision_count += 1
            results.append({'variant_id': i, 'params': json.dumps(mutation), 'collision_found': 'TRUE'})
        elif result == True:
            print("safe")
            safe_count += 1
            results.append({'variant_id': i, 'params': json.dumps(mutation), 'collision_found': 'FALSE'})
        else:
            print(f"{result}")
            error_count += 1
            results.append({'variant_id': i, 'params': json.dumps(mutation), 'collision_found': str(result)})

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['variant_id', 'params', 'collision_found'])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 60)
    print(f"Results: {collision_count} COLLISION, {safe_count} SAFE, {error_count} ERROR")
    print(f"Collision rate: {collision_count}/{collision_count + safe_count} = {collision_count / max(1, collision_count + safe_count) * 100:.1f}%")
    print(f"CSV saved to: {OUTPUT_CSV}")

    # Show collision details
    if collision_count > 0:
        print(f"\nCollision variants:")
        for r in results:
            if r['collision_found'] == 'TRUE':
                p = json.loads(r['params'])
                print(f"  id={r['variant_id']}: lat={p['lateral_offset']:+.0f}m head={p['heading_offset']:+.1f}rad vel×{p['speed_factor']:.1f}")

if __name__ == '__main__':
    main()
