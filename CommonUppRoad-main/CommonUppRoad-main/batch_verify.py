"""
batch_verify.py
批量验证 UPPAAL 模型，输出碰撞结果到 CSV
"""
import subprocess
import os
import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp1", "models")
PARAM_TABLE = os.path.join(os.path.dirname(__file__), "experiments", "exp1", "param_table.json")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "experiments", "exp1", "results.csv")

QUERY = "A[] !cps_i_state.detection.collide"

QUERY_FILE = os.path.join(MODELS_DIR, "_query.q")

def verify_model(model_path):
    """用 verifyta 验证单个模型，返回 True(安全) 或 False(碰撞)"""
    try:
        result = subprocess.run(
            [VERIFYTA, "-s", model_path, QUERY_FILE],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout + result.stderr
        # verifyta 输出中找结果
        # "Formula is satisfied" = TRUE (安全)
        # "Formula is NOT satisfied" = FALSE (碰撞)
        if "NOT satisfied" in output:
            return False  # 碰撞
        elif "satisfied" in output:
            return True   # 安全
        else:
            return None   # 无法判断
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    # 加载参数表
    with open(PARAM_TABLE, 'r', encoding='utf-8') as f:
        param_data = json.load(f)

    mutations = param_data['mutations']
    print(f"Total variants: {len(mutations)}")
    print(f"Verifyta: {VERIFYTA}")
    print(f"Query: {QUERY}")
    print("=" * 60)

    # 先把查询写入临时文件
    query_file = os.path.join(MODELS_DIR, "_query.q")
    with open(query_file, 'w') as f:
        f.write(QUERY)

    results = []
    collision_count = 0
    safe_count = 0
    error_count = 0

    for i, mutation in enumerate(mutations):
        model_file = os.path.join(MODELS_DIR, f"variant_{i:04d}.xml")
        if not os.path.exists(model_file):
            print(f"[{i:3d}/80] Model not found: {model_file}")
            results.append({
                'variant_id': i,
                'params': json.dumps(mutation['params']),
                'collision_found': 'NOT_FOUND',
                'result_raw': ''
            })
            error_count += 1
            continue

        # 运行验证
        print(f"[{i:3d}/80] Verifying variant_{i:04d}...", end=" ", flush=True)
        result = verify_model(model_file)

        if result == False:
            print("COLLISION!")
            collision_count += 1
            results.append({
                'variant_id': i,
                'params': json.dumps(mutation['params']),
                'collision_found': 'TRUE',
                'result_raw': 'NOT_satisfied'
            })
        elif result == True:
            print("safe")
            safe_count += 1
            results.append({
                'variant_id': i,
                'params': json.dumps(mutation['params']),
                'collision_found': 'FALSE',
                'result_raw': 'satisfied'
            })
        elif result == "TIMEOUT":
            print("TIMEOUT")
            error_count += 1
            results.append({
                'variant_id': i,
                'params': json.dumps(mutation['params']),
                'collision_found': 'TIMEOUT',
                'result_raw': 'timeout'
            })
        else:
            print(f"ERROR: {result}")
            error_count += 1
            results.append({
                'variant_id': i,
                'params': json.dumps(mutation['params']),
                'collision_found': 'ERROR',
                'result_raw': str(result)
            })

    # 写入 CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['variant_id', 'params', 'collision_found', 'result_raw'])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 60)
    print(f"Results: {collision_count} COLLISION, {safe_count} SAFE, {error_count} ERROR")
    print(f"Collision rate: {collision_count}/{collision_count + safe_count} = {collision_count / max(1, collision_count + safe_count) * 100:.1f}%")
    print(f"CSV saved to: {OUTPUT_CSV}")


if __name__ == '__main__':
    main()
