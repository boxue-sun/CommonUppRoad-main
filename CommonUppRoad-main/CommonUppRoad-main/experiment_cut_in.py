"""
experiment_cut_in.py
实验：障碍物从相邻车道切入(cut-in)，UPPAAL穷举所有行为组合找碰撞

场景布局：
  Lane 3 (左)   |  obs在此时从左侧切入 ego
  Lane 2 (中)   |  ego 在中间车道
  Lane 1 (右)   |  obs在此时从右侧切入 ego

UPPAAL obstacle automaton 会穷举所有 {刹车/匀速/加速} × {左转/直行/右转} = 9种行为组合
"""
import subprocess
import os
import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_cut_in", "models")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_cut_in")
os.makedirs(MODELS_DIR, exist_ok=True)

TEMPLATE = os.path.join(os.path.dirname(__file__), "uppaal", "template.xml")
QUERY_FILE = os.path.join(MODELS_DIR, "_query.q")

# ====== 车道几何 ======
# Lane 1 (右): y=[-17, 17] iP, center=0.0m
# Lane 2 (中): y=[17, 52] iP, center=3.45m  ← ego 在这里
# Lane 3 (左): y=[52, 87] iP, center=6.95m
LANE2_Y = 3.45       # ego Y (m)
LANE1_Y = 0.0        # right cut-in (m)
LANE3_Y = 6.95       # left cut-in (m)
EGO_LANE_INDEX = 1   # initLane = 1 (0-based → lane 2)

# ====== 参数空间 ======
CUT_IN_DISTANCES = [2, 3, 5, 8, 10, 15, 20, 30]   # 纵向距离 (m)
EGO_SPEEDS = [15, 20, 25, 30]                       # ego 速度 (m/s)
OBS_SPEEDS = [10, 15, 20, 25]                       # 障碍物速度 (m/s)
CUT_IN_SIDES = ['left', 'right']                    # 切入方向

# ====== 增强切入参数 ======
OBS_INIT_HEADING = 0.08     # 障碍物初始朝向(rad)，偏向ego车道，加速切入
YAW_RATE_VALUE = 1.0        # 替换模板中的 0.3 → 1.0，3倍切入速度


def generate_model(distance, obs_speed, ego_speed, side, output_path):
    """生成 UPPAAL 模型：障碍物在相邻车道，ego 在中间车道"""
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()

    # 障碍物 Y 位置和初始朝向
    if side == 'left':
        obs_y = LANE3_Y      # 左车道
        obs_heading = -OBS_INIT_HEADING  # 向右偏（偏向ego）
    else:
        obs_y = LANE1_Y      # 右车道
        obs_heading = OBS_INIT_HEADING   # 向左偏（偏向ego）

    obs_y_ip = int(round(obs_y * 10))   # iP 坐标
    ego_y_ip = int(round(LANE2_Y * 10))

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

    # 替换 scenario data
    start_marker = "<declaration>// Generated scenario starts"
    end_marker = "// Generated scenario ends"
    start_idx = template.index(start_marker)
    end_idx = template.index(end_marker) + len(end_marker)
    new_template = template[:start_idx] + start_marker + "\n" + scenario_data + "\n" + template[end_idx:]

    # 替换 moving obstacle
    obs_start = "<system>// Generated moving obstacles starts"
    obs_end = "// Generated moving obstacles ends"
    obs_start_idx = new_template.index(obs_start)
    obs_end_idx = new_template.index(obs_end) + len(obs_end)

    obs_pos_x_ip = int(distance * 10)
    v_min = max(0.5, obs_speed * 0.5)
    v_max = obs_speed * 1.5 + 5
    obs_lines = [
        "<system>// Generated moving obstacles starts",
        f"const ST_DSTATE initCS0 = {{{{{distance}.0, {obs_y}}}, {float(obs_speed)}, {obs_heading}, 0.0, 0.0, 0.0}};",
        f"const ST_RECTANGLE shapeObs0 = {{{{{obs_pos_x_ip}, {obs_y_ip}}}, 20, 45, {int(obs_heading * 10)}}};",
        f"const ST_OBEHAVIOR obsBehavior0 = {{d2i({v_min}), d2i({v_max}), d2i(3.0), d2i(6.0), d2i(0.3), d2i(50.0), d2i(0.0)}};",
        "obs0 = Obstacle(0, initCS0, shapeObs0, obsBehavior0);",
        "// Generated moving obstacles ends",
    ]
    obs_data = "\n".join(obs_lines)
    new_template = new_template[:obs_start_idx] + obs_data + new_template[obs_end_idx:]

    # === 增强横向切入速度：替换 yawRate ±0.3 → ±YAW_RATE_VALUE ===
    new_template = new_template.replace(
        'obs_i_state[id].yawRate = d2i(-0.3);',
        f'obs_i_state[id].yawRate = d2i(-{YAW_RATE_VALUE});'
    )
    new_template = new_template.replace(
        'obs_i_state[id].yawRate = d2i(0.3);',
        f'obs_i_state[id].yawRate = d2i({YAW_RATE_VALUE});'
    )

    # 替换 ego（在 Lane 2 中间）
    ego_start = "// Generated ego vehicle starts"
    ego_end = "// Generated ego vehicle ends"
    ego_start_idx = new_template.index(ego_start)
    ego_end_idx = new_template.index(ego_end) + len(ego_end)

    ego_lines = [
        "// Generated ego vehicle starts",
        f"const ST_DSTATE initEgo = {{{{{0.0}, {LANE2_Y}}}, {float(ego_speed)}, 0.0, 0.0, 0.0, 0.0}};",
        f"const ST_RECTANGLE initShapeEgo = {{{{{0}, {ego_y_ip}}}, 10, 45, 0}};",
        "const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};",
        f"const int[0,MAXL] initLane = {EGO_LANE_INDEX};",
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

    # 替换 queries
    q_start = "<queries>"
    q_end = "</queries>"
    q_start_idx = new_template.index(q_start)
    q_end_idx = new_template.index(q_end) + len(q_end)
    new_template = new_template[:q_start_idx] + "<queries><query><formula>A[] !cps_i_state.detection.collide</formula><comment/></query></queries>" + new_template[q_end_idx:]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_template)


def verify_model(model_path):
    """UPPAAL 验证模型，返回 True=safe, False=collision, None=error"""
    try:
        result = subprocess.run(
            [VERIFYTA, "-s", model_path, QUERY_FILE],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace'
        )
        output = result.stdout + result.stderr
        if "NOT satisfied" in output:
            return False   # 碰撞找到
        elif "satisfied" in output:
            return True    # 安全
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
    error_count = 0
    vid = 0

    total = len(CUT_IN_DISTANCES) * len(EGO_SPEEDS) * len(OBS_SPEEDS) * len(CUT_IN_SIDES)
    print(f"Cut-in Experiment: Distance × EgoSpeed × ObsSpeed × Side")
    print(f"  = {len(CUT_IN_DISTANCES)} × {len(EGO_SPEEDS)} × {len(OBS_SPEEDS)} × {len(CUT_IN_SIDES)}")
    print(f"  = {total} variants")
    print(f"Lane config: Ego in Lane2 (Y={LANE2_Y}m), Obs in Lane1 (Y={LANE1_Y}m) or Lane3 (Y={LANE3_Y}m)")
    print(f"Cut-in boost: initHeading={OBS_INIT_HEADING}rad, yawRate=±{YAW_RATE_VALUE}")
    print("=" * 80)

    for dist in CUT_IN_DISTANCES:
        for ego_spd in EGO_SPEEDS:
            for obs_spd in OBS_SPEEDS:
                for side in CUT_IN_SIDES:
                    model_path = os.path.join(MODELS_DIR, f"variant_{vid:04d}.xml")
                    generate_model(dist, obs_spd, ego_spd, side, model_path)

                    result = verify_model(model_path)

                    side_label = "L" if side == 'left' else "R"
                    if result == False:
                        collision_count += 1
                        tag = f"COLLISION! ({side_label})"
                    elif result == True:
                        safe_count += 1
                        tag = f"safe ({side_label})"
                    else:
                        error_count += 1
                        tag = str(result)

                    print(f"[{vid:3d}/{total}] dist={dist:2d}m ego={ego_spd:2d}m/s "
                          f"obs={obs_spd:2d}m/s side={side:5s} -> {tag}")

                    results.append({
                        'variant_id': vid,
                        'distance': dist,
                        'ego_speed': ego_spd,
                        'obs_speed': obs_spd,
                        'cut_in_side': side,
                        'collision_found': 'TRUE' if result == False else 'FALSE' if result == True else str(result),
                    })
                    vid += 1

    # 保存结果
    csv_path = os.path.join(OUTPUT_DIR, 'results.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['variant_id', 'distance', 'ego_speed', 'obs_speed', 'cut_in_side', 'collision_found'])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 80)
    print(f"Results: {collision_count} COLLISION, {safe_count} SAFE", end='')
    if error_count > 0:
        print(f", {error_count} ERROR/TIMEOUT", end='')
    verified = collision_count + safe_count
    rate = collision_count / max(1, verified) * 100
    print(f" | Collision rate: {rate:.1f}%")
    print(f"Output: {csv_path}")

    # 按侧分组统计
    left_collisions = sum(1 for r in results if r['cut_in_side'] == 'left' and r['collision_found'] == 'TRUE')
    right_collisions = sum(1 for r in results if r['cut_in_side'] == 'right' and r['collision_found'] == 'TRUE')
    left_total = len([r for r in results if r['cut_in_side'] == 'left' and r['collision_found'] in ('TRUE', 'FALSE')])
    right_total = len([r for r in results if r['cut_in_side'] == 'right' and r['collision_found'] in ('TRUE', 'FALSE')])
    print(f"  Left cut-in:  {left_collisions}/{left_total} = {left_collisions/max(1,left_total)*100:.1f}%")
    print(f"  Right cut-in: {right_collisions}/{right_total} = {right_collisions/max(1,right_total)*100:.1f}%")

    if collision_count > 0:
        print(f"\nCollision scenarios (first 20):")
        collision_scenarios = [r for r in results if r['collision_found'] == 'TRUE']
        for r in collision_scenarios[:20]:
            side_short = "L" if r['cut_in_side'] == 'left' else "R"
            print(f"  dist={r['distance']:2d}m ego={r['ego_speed']:2d}m/s "
                  f"obs={r['obs_speed']:2d}m/s side={side_short}")


if __name__ == '__main__':
    main()
