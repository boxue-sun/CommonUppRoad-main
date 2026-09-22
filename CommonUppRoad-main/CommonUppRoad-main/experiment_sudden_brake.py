"""
experiment_sudden_brake.py
实验：前车突然紧急刹车，测试法规驾驶员模型能否避免碰撞
场景：两车同向同车道行驶，前车在某个时刻突然急刹到零
"""
import subprocess
import os
import sys
import io
import json
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_sudden_brake", "models")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_sudden_brake")
os.makedirs(MODELS_DIR, exist_ok=True)

QUERY_FILE = os.path.join(MODELS_DIR, "_query.q")


def generate_model(ego_speed, obs_speed, distance, brake_decel, brake_start_step, output_path):
    """
    生成 UPPAAL 模型：
    - ego 以 ego_speed 行驶，使用法规驾驶员模型
    - 障碍物以 obs_speed 行驶，从第一步开始持续以 brake_decel 减速
    - 初始距离为 distance 米

    关键：障碍物不做穷举，而是固定执行急刹动作
    """
    v_min = 0.0
    v_max = obs_speed * 1.2 + 5

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!DOCTYPE nta PUBLIC \'-//Uppaal Team//DTD Flat System 1.6//EN\' \'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd\'>',
        '<nta>',
        '	<declaration>// Generated scenario starts',
        'const int P = 1;',
        'const uint16_t MAXTIME = 50;',
        'const int MAXP = 2;',
        'const int NONE = -1;',
        'const int MAXL = 3;',
        'const int MAXSO = 1;',
        'const int MAXDO = 1;',
        'const int MAXTP = 1;',
        'const int MAXPRE = 1;',
        'const int MAXSUC = 1;',
        'const double THRESHOLD = 4.0;',
        'const double TIMESTEPSIZE = 0.1;',
        'const double RADAR = 100;',
        'const uint8_t N1 = 1;',
        'const uint8_t N2 = 4;',
        'const uint8_t MAXACT = 2;',
        'typedef int[0,MAXACT-1] act_id_t;',
        'const uint8_t BASE = 10;',
        'const uint8_t EXPONENT = 1;',
        'const uint8_t MAXOBS = 1;',
        'typedef int[0,MAXOBS-1] obs_id_t;',
        '',
        'typedef int[-1,65535] id_t;',
        'typedef struct { int32_t x; int32_t y; }ST_IPOINT;',
        'typedef struct { double x; double y; }ST_DPOINT;',
        'typedef struct { ST_IPOINT ends[2]; }ST_DLINE;',
        'typedef struct { ST_IPOINT points[MAXP]; bool dashLine; }ST_BOUND;',
        'typedef struct { id_t ID; ST_BOUND left; ST_BOUND right; id_t predecessor[MAXPRE]; id_t successor[MAXSUC]; id_t adjLeft; bool dirLeft; id_t adjRight; bool dirRight; }ST_LANE;',
        'typedef struct { bool collide; bool outside; bool reach; }ST_DETECTION;',
        'typedef struct { ST_DPOINT position; double velocity; double orientation; double acceleration; double accRate; double yawRate; }ST_DSTATE;',
        'typedef struct { ST_IPOINT position; int32_t velocity; int32_t orientation; int32_t acceleration; int32_t accRate; int32_t yawRate; ST_DETECTION detection; }ST_ISTATE;',
        'typedef struct { hybrid clock x; hybrid clock y; hybrid clock velocity; hybrid clock orientation; hybrid clock acceleration; }ST_DYNAMICS;',
        'typedef struct { ST_IPOINT center; int32_t width; int32_t length; int32_t orientation; }ST_RECTANGLE;',
        'typedef struct { int32_t maxVelocity; int32_t minVelocity; int32_t maxOrientation; int32_t minOrientation; }ST_RULES;',
        'typedef struct { ST_IPOINT goal; }ST_PLANNING;',
        'typedef struct { int32_t time; ST_DSTATE dState; }ST_PAIR;',
        'typedef struct { int32_t vMin; int32_t vMax; int32_t accMax; int32_t decMax; int32_t laneChangeProb; int32_t cutInRange; int32_t initialLane; }ST_OBEHAVIOR;',
        '',
        'const ST_BOUND leftLane1 = {{{0, 17}, {1990, 17}}, false};',
        'const ST_BOUND rightLane1 = {{{0, -17}, {1990, -17}}, false};',
        'const ST_LANE lane1 = {1, leftLane1, rightLane1, {NONE}, {NONE}, 2, false, NONE, false};',
        'const ST_BOUND leftLane2 = {{{0, 52}, {1990, 52}}, false};',
        'const ST_BOUND rightLane2 = {{{0, 17}, {1990, 17}}, false};',
        'const ST_LANE lane2 = {2, leftLane2, rightLane2, {NONE}, {NONE}, 3, true, 1, false};',
        'const ST_BOUND leftLane3 = {{{0, 87}, {1990, 87}}, false};',
        'const ST_BOUND rightLane3 = {{{0, 52}, {1990, 52}}, false};',
        'const ST_LANE lane3 = {3, leftLane3, rightLane3, {NONE}, {NONE}, NONE, false, 2, true};',
        'const ST_LANE laneNet[MAXL] = {lane1, lane2, lane3};',
        'const bool staticObsExists = false;',
        'const ST_RECTANGLE staticObs[MAXSO] = {{{NONE, NONE}, NONE, NONE, NONE}};',
        'const ST_PLANNING planning = {{995, 0}};',
        '// Generated scenario ends',
    ]

    # 读取模板的剩余部分（函数定义、模板等）
    template_path = os.path.join(os.path.dirname(__file__), "uppaal", "template.xml")
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # 从 "// Generated scenario ends" 之后开始提取模板内容
    marker = "// Generated scenario ends"
    idx = template_content.index(marker) + len(marker)
    template_rest = template_content[idx:]

    # 构建完整模型
    full_content = "\n".join(lines) + "\n" + template_rest

    # 修改障碍物的 chooseLonAction：总是返回 0（急刹），不穷举
    # 把 "int[0,2] chooseLonAction() { int[0,2] action; return action; }"
    # 改成 "int[0,2] chooseLonAction() { return 0; }"
    full_content = full_content.replace(
        'int[0,2] chooseLonAction() {\n    int[0,2] action;\n    // No init — UPPAAL exhausts all {0,1,2}\n    return action;\n}',
        'int[0,2] chooseLonAction() {\n    return 0;  // Always brake\n}'
    )
    # 横向也固定为保持
    full_content = full_content.replace(
        'int[-1,1] chooseLatAction() {\n    int[-1,1] action;\n    // No init — UPPAAL exhausts all {-1,0,1}\n    return action;\n}',
        'int[-1,1] chooseLatAction() {\n    return 0;  // Always stay\n}'
    )

    # 替换 moving obstacles 部分
    obs_start = "<system>// Generated moving obstacles starts"
    obs_end = "// Generated moving obstacles ends"
    obs_start_idx = full_content.index(obs_start)
    obs_end_idx = full_content.index(obs_end) + len(obs_end)

    obs_data = (
        "<system>// Generated moving obstacles starts\n"
        "const ST_DSTATE initCS0 = {{" + str(float(distance)) + ", 0.0}, " + str(float(obs_speed)) + ", 0.0, 0.0, 0.0, 0.0};\n"
        "const ST_RECTANGLE shapeObs0 = {{" + str(distance * 10) + ", 0}, 20, 45, 0};\n"
        "const ST_OBEHAVIOR obsBehavior0 = {d2i(" + str(v_min) + "), d2i(" + str(v_max) + "), d2i(3.0), d2i(" + str(abs(brake_decel)) + "), d2i(0.0), d2i(50.0), d2i(0.0)};\n"
        "obs0 = Obstacle(0, initCS0, shapeObs0, obsBehavior0);\n"
        "// Generated moving obstacles ends"
    )
    full_content = full_content[:obs_start_idx] + obs_data + full_content[obs_end_idx:]

    # 替换 ego 部分
    ego_start = "// Generated ego vehicle starts"
    ego_end = "// Generated ego vehicle ends"
    ego_start_idx = full_content.index(ego_start)
    ego_end_idx = full_content.index(ego_end) + len(ego_end)

    ego_data = (
        "// Generated ego vehicle starts\n"
        "const ST_DSTATE initEgo = {{0.0, 0.0}, " + str(float(ego_speed)) + ", 0.0, 0.0, 0.0, 0.0};\n"
        "const ST_RECTANGLE initShapeEgo = {{0, 0}, 10, 45, 0};\n"
        "const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};\n"
        "const int[0,MAXL] initLane = 0;\n"
        "move = Act_Move(0);\n"
        "turn = Act_Turn(1);\n"
        "controller = Controller(initLane,initEgo,initShapeEgo,rules);\n"
        "timer = Timer();\n"
        "dynamics = Dynamics();\n"
        "rewardMachine = Rewards();\n"
        "// Generated ego vehicle ends"
    )
    full_content = full_content[:ego_start_idx] + ego_data + full_content[ego_end_idx:]

    # 替换 system
    sys_start = "// Generated model instances starts"
    sys_end = "// Generated model instances ends"
    sys_start_idx = full_content.index(sys_start)
    sys_end_idx = full_content.index(sys_end) + len(sys_end)
    sys_data = "// Generated model instances starts\nsystem timer, obs0, move, turn, controller, dynamics, rewardMachine;\n// Generated model instances ends"
    full_content = full_content[:sys_start_idx] + sys_data + full_content[sys_end_idx:]

    # 替换 queries
    q_start = "<queries>"
    q_end = "</queries>"
    q_start_idx = full_content.index(q_start)
    q_end_idx = full_content.index(q_end) + len(q_end)
    full_content = full_content[:q_start_idx] + "<queries><query><formula>A[] !cps_i_state.detection.collide</formula><comment/></query></queries>" + full_content[q_end_idx:]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_content)


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
        return None
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    with open(QUERY_FILE, 'w') as f:
        f.write("A[] !cps_i_state.detection.collide\n")

    # 实验设计：
    # 场景：两车同向同车道，前车突然急刹
    # 变量：ego速度、初始距离、障碍物初速度、刹车减速度
    scenarios = [
        # (描述, ego速度, obs速度, 距离, 刹车减速度)
        # === 追尾场景：前车急刹到底 ===
        ("ego25_obs20_dist15_brake4",  25, 20, 15, -4.0),
        ("ego25_obs20_dist20_brake4",  25, 20, 20, -4.0),
        ("ego25_obs20_dist25_brake4",  25, 20, 25, -4.0),
        ("ego25_obs20_dist30_brake4",  25, 20, 30, -4.0),
        ("ego30_obs25_dist15_brake4",  30, 25, 15, -4.0),
        ("ego30_obs25_dist20_brake4",  30, 25, 20, -4.0),
        ("ego30_obs25_dist25_brake4",  30, 25, 25, -4.0),
        ("ego30_obs25_dist30_brake4",  30, 25, 30, -4.0),
        ("ego20_obs15_dist10_brake4",  20, 15, 10, -4.0),
        ("ego20_obs15_dist15_brake4",  20, 15, 15, -4.0),

        # === 法规模型优势：不是最大刹车也撞 ===
        ("ego25_obs20_dist15_brake3",  25, 20, 15, -3.0),
        ("ego25_obs20_dist20_brake3",  25, 20, 20, -3.0),
        ("ego25_obs20_dist25_brake3",  25, 20, 25, -3.0),
        ("ego30_obs25_dist20_brake3",  30, 25, 20, -3.0),
        ("ego30_obs25_dist25_brake3",  30, 25, 25, -3.0),

        # === 法规模型优势：更小减速度也撞 ===
        ("ego25_obs20_dist15_brake2",  25, 20, 15, -2.0),
        ("ego25_obs20_dist20_brake2",  25, 20, 20, -2.0),
        ("ego30_obs25_dist20_brake2",  30, 25, 20, -2.0),

        # === 安全场景：距离远或速度低 ===
        ("ego15_obs10_dist20_brake4",  15, 10, 20, -4.0),
        ("ego20_obs15_dist25_brake4",  20, 15, 25, -4.0),
        ("ego25_obs20_dist40_brake4",  25, 20, 40, -4.0),
        ("ego30_obs25_dist50_brake4",  30, 25, 50, -4.0),
    ]

    print(f"Sudden brake experiment: {len(scenarios)} scenarios")
    print(f"Ego uses regulatory driver model (reaction delay + gradual braking)")
    print(f"Obstacle suddenly brakes with given deceleration")
    print("=" * 70)

    results = []
    collision_count = 0
    safe_count = 0

    for i, (desc, ego_spd, obs_spd, dist, brake) in enumerate(scenarios):
        model_path = os.path.join(MODELS_DIR, f"variant_{i:04d}.xml")
        generate_model(ego_spd, obs_spd, dist, brake, 0, model_path)

        result = verify_model(model_path)
        if result == False:
            collision_count += 1
            tag = "COLLISION!"
        elif result == True:
            safe_count += 1
            tag = "safe"
        else:
            tag = str(result)

        print(f"[{i:2d}] {desc} -> {tag}")

        results.append({
            'id': i,
            'desc': desc,
            'ego_speed': ego_spd,
            'obs_speed': obs_spd,
            'distance': dist,
            'brake_decel': brake,
            'collision': 'TRUE' if result == False else 'FALSE' if result == True else str(result),
        })

    # 保存结果
    csv_path = os.path.join(OUTPUT_DIR, 'results.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'desc', 'ego_speed', 'obs_speed', 'distance', 'brake_decel', 'collision'])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 70)
    print(f"Results: {collision_count} COLLISION, {safe_count} SAFE")
    print(f"Collision rate: {collision_count}/{len(scenarios)} = {collision_count / len(scenarios) * 100:.1f}%")

    if collision_count > 0:
        print(f"\nCollision scenarios:")
        for r in results:
            if r['collision'] == 'TRUE':
                print(f"  ego={r['ego_speed']}m/s obs={r['obs_speed']}m/s dist={r['distance']}m brake={r['brake_decel']}m/s²")


if __name__ == '__main__':
    main()
