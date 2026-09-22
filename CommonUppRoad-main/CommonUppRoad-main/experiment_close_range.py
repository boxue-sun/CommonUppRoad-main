"""
experiment_close_range.py
实验：障碍物在 ego 正前方近距离，变化距离和速度
"""
import subprocess
import os
import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_close_range", "models")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_close_range")
os.makedirs(MODELS_DIR, exist_ok=True)

TEMPLATE = os.path.join(os.path.dirname(__file__), "uppaal", "template.xml")
QUERY_FILE = os.path.join(MODELS_DIR, "_query.q")

# 参数空间
DISTANCES = [3, 5, 8, 10, 15, 20, 30, 50]       # 障碍物在 ego 前方的距离（米）
OBS_SPEEDS = [0, 1, 3, 5, 10]                     # 障碍物速度（m/s）
EGO_SPEEDS = [10, 15, 20, 25, 30]                 # Ego 初始速度（m/s）

def generate_model(distance, obs_speed, ego_speed, output_path):
    """生成一个 UPPAAL 模型，障碍物在 ego 正前方 distance 米"""
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()

    # 场景数据：3条直道，ego 在原点，障碍物在正前方
    scenario_lines = [
        "const int P = 1;",
        "const uint16_t MAXTIME = 50;",
        "const int MAXP = 2;",
        "const int NONE = -1;",
        "const int MAXL = 3;",
        "const int MAXSO = 1;",
        "const int MAXDO = 1;",
        "const int MAXTP = 1;",
        "const int MAXPRE = 1;",
        "const int MAXSUC = 1;",
        "const double THRESHOLD = 4.0;",
        "const double TIMESTEPSIZE = 0.1;",
        "const double RADAR = 100;",
        "const uint8_t N1 = 1;",
        "const uint8_t N2 = 4;",
        "const uint8_t MAXACT = 2;",
        "typedef int[0,MAXACT-1] act_id_t;",
        "const uint8_t BASE = 10;",
        "const uint8_t EXPONENT = 1;",
        "const uint8_t MAXOBS = 1;",
        "typedef int[0,MAXOBS-1] obs_id_t;",
        "",
        "typedef int[-1,65535] id_t;",
        "typedef struct { int32_t x; int32_t y; }ST_IPOINT;",
        "typedef struct { double x; double y; }ST_DPOINT;",
        "typedef struct { ST_IPOINT ends[2]; }ST_DLINE;",
        "typedef struct { ST_IPOINT points[MAXP]; bool dashLine; }ST_BOUND;",
        "typedef struct { id_t ID; ST_BOUND left; ST_BOUND right; id_t predecessor[MAXPRE]; id_t successor[MAXSUC]; id_t adjLeft; bool dirLeft; id_t adjRight; bool dirRight; }ST_LANE;",
        "typedef struct { bool collide; bool outside; bool reach; }ST_DETECTION;",
        "typedef struct { ST_DPOINT position; double velocity; double orientation; double acceleration; double accRate; double yawRate; }ST_DSTATE;",
        "typedef struct { ST_IPOINT position; int32_t velocity; int32_t orientation; int32_t acceleration; int32_t accRate; int32_t yawRate; ST_DETECTION detection; }ST_ISTATE;",
        "typedef struct { hybrid clock x; hybrid clock y; hybrid clock velocity; hybrid clock orientation; hybrid clock acceleration; }ST_DYNAMICS;",
        "typedef struct { ST_IPOINT center; int32_t width; int32_t length; int32_t orientation; }ST_RECTANGLE;",
        "typedef struct { int32_t maxVelocity; int32_t minVelocity; int32_t maxOrientation; int32_t minOrientation; }ST_RULES;",
        "typedef struct { ST_IPOINT goal; }ST_PLANNING;",
        "typedef struct { int32_t time; ST_DSTATE dState; }ST_PAIR;",
        "typedef struct { int32_t vMin; int32_t vMax; int32_t accMax; int32_t decMax; int32_t laneChangeProb; int32_t cutInRange; int32_t initialLane; }ST_OBEHAVIOR;",
        "",
        "const ST_BOUND leftLane1 = {{{0, 17}, {1990, 17}}, false};",
        "const ST_BOUND rightLane1 = {{{0, -17}, {1990, -17}}, false};",
        "const ST_LANE lane1 = {1, leftLane1, rightLane1, {NONE}, {NONE}, 2, false, NONE, false};",
        "const ST_BOUND leftLane2 = {{{0, 52}, {1990, 52}}, false};",
        "const ST_BOUND rightLane2 = {{{0, 17}, {1990, 17}}, false};",
        "const ST_LANE lane2 = {2, leftLane2, rightLane2, {NONE}, {NONE}, 3, true, 1, false};",
        "const ST_BOUND leftLane3 = {{{0, 87}, {1990, 87}}, false};",
        "const ST_BOUND rightLane3 = {{{0, 52}, {1990, 52}}, false};",
        "const ST_LANE lane3 = {3, leftLane3, rightLane3, {NONE}, {NONE}, NONE, false, 2, true};",
        "const ST_LANE laneNet[MAXL] = {lane1, lane2, lane3};",
        "const bool staticObsExists = false;",
        "const ST_RECTANGLE staticObs[MAXSO] = {{{NONE, NONE}, NONE, NONE, NONE}};",
        "const ST_PLANNING planning = {{995, 0}};",
    ]
    scenario_data = "\n".join(scenario_lines)

    # 找到标记位置并替换
    start_marker = "<declaration>// Generated scenario starts"
    end_marker = "// Generated scenario ends"
    start_idx = template.index(start_marker)
    end_idx = template.index(end_marker) + len(end_marker)
    new_template = template[:start_idx] + start_marker + "\n" + scenario_data + "\n" + template[end_idx:]

    # 替换 moving obstacles
    obs_start = "<system>// Generated moving obstacles starts"
    obs_end = "// Generated moving obstacles ends"
    obs_start_idx = new_template.index(obs_start)
    obs_end_idx = new_template.index(obs_end) + len(obs_end)

    obs_pos_x = distance
    obs_pos_x_int = distance * 10
    v_min = max(0.5, obs_speed * 0.5)
    v_max = obs_speed * 1.5 + 5
    obs_lines = [
        "<system>// Generated moving obstacles starts",
        "const ST_DSTATE initCS0 = {{" + str(obs_pos_x) + ".0, 0.0}, " + str(float(obs_speed)) + ", 0.0, 0.0, 0.0, 0.0};",
        "const ST_RECTANGLE shapeObs0 = {{" + str(obs_pos_x_int) + ", 0}, 20, 45, 0};",
        "const ST_OBEHAVIOR obsBehavior0 = {d2i(" + str(v_min) + "), d2i(" + str(v_max) + "), d2i(3.0), d2i(6.0), d2i(0.3), d2i(50.0), d2i(0.0)};",
        "obs0 = Obstacle(0, initCS0, shapeObs0, obsBehavior0);",
        "// Generated moving obstacles ends",
    ]
    obs_data = "\n".join(obs_lines)

    new_template = new_template[:obs_start_idx] + obs_data + new_template[obs_end_idx:]

    # 替换 ego
    ego_start = "// Generated ego vehicle starts"
    ego_end = "// Generated ego vehicle ends"
    ego_start_idx = new_template.index(ego_start)
    ego_end_idx = new_template.index(ego_end) + len(ego_end)

    ego_lines = [
        "// Generated ego vehicle starts",
        "const ST_DSTATE initEgo = {{0.0, 0.0}, " + str(float(ego_speed)) + ", 0.0, 0.0, 0.0, 0.0};",
        "const ST_RECTANGLE initShapeEgo = {{0, 0}, 10, 45, 0};",
        "const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};",
        "const int[0,MAXL] initLane = 0;",
        "move = Act_Move(0);",
        "turn = Act_Turn(1);",
        "controller = Controller(initLane,initEgo,initShapeEgo,rules);",
        "timer = Timer();",
        "dynamics = Dynamics();",
        "rewardMachine = Rewards();",
        "// Generated ego vehicle ends",
    ]
    ego_data = "\n".join(ego_lines)

    new_template = new_template[:ego_start_idx] + ego_data + new_template[ego_end_idx:]

    # 替换 system
    sys_start = "// Generated model instances starts"
    sys_end = "// Generated model instances ends"
    sys_start_idx = new_template.index(sys_start)
    sys_end_idx = new_template.index(sys_end) + len(sys_end)
    new_template = new_template[:sys_start_idx] + "// Generated model instances starts\nsystem timer, obs0, move, turn, controller, dynamics, rewardMachine;\n// Generated model instances ends" + new_template[sys_end_idx:]

    # 清理 queries
    q_start = "<queries>"
    q_end = "</queries>"
    q_start_idx = new_template.index(q_start)
    q_end_idx = new_template.index(q_end) + len(q_end)
    new_template = new_template[:q_start_idx] + "<queries><query><formula>A[] !cps_i_state.detection.collide</formula><comment/></query></queries>" + new_template[q_end_idx:]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_template)


def verify_model(model_path):
    try:
        result = subprocess.run(
            [VERIFYTA, "-s", model_path, QUERY_FILE],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout + result.stderr
        if "NOT satisfied" in output:
            return False
        elif "satisfied" in output:
            return True
        return None
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    with open(QUERY_FILE, 'w') as f:
        f.write("A[] !cps_i_state.detection.collide\n")

    results = []
    collision_count = 0
    safe_count = 0
    vid = 0

    print(f"Distance × ObsSpeed × EgoSpeed = {len(DISTANCES)} × {len(OBS_SPEEDS)} × {len(EGO_SPEEDS)} = {len(DISTANCES) * len(OBS_SPEEDS) * len(EGO_SPEEDS)} variants")
    print("=" * 70)

    for dist in DISTANCES:
        for obs_spd in OBS_SPEEDS:
            for ego_spd in EGO_SPEEDS:
                model_path = os.path.join(MODELS_DIR, f"variant_{vid:04d}.xml")
                generate_model(dist, obs_spd, ego_spd, model_path)

                result = verify_model(model_path)

                if result == False:
                    collision_count += 1
                    tag = "COLLISION!"
                elif result == True:
                    safe_count += 1
                    tag = "safe"
                else:
                    tag = str(result)

                print(f"[{vid:3d}] dist={dist:2d}m obs={obs_spd:2d}m/s ego={ego_spd:2d}m/s -> {tag}")

                results.append({
                    'variant_id': vid,
                    'distance': dist,
                    'obs_speed': obs_spd,
                    'ego_speed': ego_spd,
                    'collision_found': 'TRUE' if result == False else 'FALSE' if result == True else str(result),
                })
                vid += 1

    # Save results
    csv_path = os.path.join(OUTPUT_DIR, 'results.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['variant_id', 'distance', 'obs_speed', 'ego_speed', 'collision_found'])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 70)
    print(f"Results: {collision_count} COLLISION, {safe_count} SAFE")
    print(f"Collision rate: {collision_count}/{collision_count + safe_count} = {collision_count / max(1, collision_count + safe_count) * 100:.1f}%")

    if collision_count > 0:
        print(f"\nCollision scenarios:")
        for r in results:
            if r['collision_found'] == 'TRUE':
                print(f"  dist={r['distance']}m obs={r['obs_speed']}m/s ego={r['ego_speed']}m/s")

if __name__ == '__main__':
    main()
