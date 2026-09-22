#!/usr/bin/env python3
"""
create_adversarial_scenario.py
手动创建一个"必撞"测试场景：障碍物直接挡在ego正前方很近处
"""
import os
import shutil

TEMPLATE = os.path.join(os.path.dirname(__file__), "uppaal", "template.xml")
OUTPUT = os.path.join(os.path.dirname(__file__), "uppaal", "models", "test_adversarial_generated_lanelet.xml")

with open(TEMPLATE, 'r', encoding='utf-8') as f:
    template = f.read()

# 场景参数：
# 3条车道，直路
# Ego: pos=(15, 0), vel=22 m/s (80 km/h), heading=0
# Obs0: pos=(18, 0), vel=1 m/s, heading=0  → 在ego正前方3米，几乎静止！
# Obs1: pos=(100, 0), vel=22 m/s, heading=0 → 远处同速，无影响

scenario_data = '''
const int P = 1;
const uint16_t MAXTIME = 50;
const int MAXP = 2;
const int NONE = -1;
const int MAXL = 3;
const int MAXSO = 1;
const int MAXDO = 2;
const int MAXTP = 1;
const int MAXPRE = 1;
const int MAXSUC = 1;
const double THRESHOLD = 4.0;
const double TIMESTEPSIZE = 0.1;
const double RADAR = 100;
const uint8_t N1 = 1;
const uint8_t N2 = 4;
const uint8_t MAXACT = 2;
typedef int[0,MAXACT-1] act_id_t;
const uint8_t BASE = 10;
const uint8_t EXPONENT = 1;
const uint8_t MAXOBS = 2;
typedef int[0,MAXOBS-1] obs_id_t;

typedef int[-1,65535] id_t;

typedef struct {
    int32_t x;
    int32_t y;
}ST_IPOINT;

typedef struct {
    double x;
    double y;
}ST_DPOINT;

typedef struct {
    ST_IPOINT ends[2];
}ST_DLINE;

typedef struct {
    ST_IPOINT points[MAXP];
    bool dashLine;
}ST_BOUND;

typedef struct {
    id_t ID;
    ST_BOUND left;
    ST_BOUND right;
    id_t predecessor[MAXPRE];
    id_t successor[MAXSUC];
    id_t adjLeft;
    bool dirLeft;
    id_t adjRight;
    bool dirRight;
}ST_LANE;

typedef struct {
    bool collide;
    bool outside;
    bool reach;
}ST_DETECTION;

typedef struct {
    ST_DPOINT position;
    double velocity;
    double orientation;
    double acceleration;
    double accRate;
    double yawRate;
}ST_DSTATE;

typedef struct {
    ST_IPOINT position;
    int32_t velocity;
    int32_t orientation;
    int32_t acceleration;
    int32_t accRate;
    int32_t yawRate;
    ST_DETECTION detection;
}ST_ISTATE;

typedef struct {
    hybrid clock x;
    hybrid clock y;
    hybrid clock velocity;
    hybrid clock orientation;
    hybrid clock acceleration;
}ST_DYNAMICS;

typedef struct {
    ST_IPOINT center;
    int32_t width;
    int32_t length;
    int32_t orientation;
}ST_RECTANGLE;

typedef struct {
    int32_t maxVelocity;
    int32_t minVelocity;
    int32_t maxOrientation;
    int32_t minOrientation;
}ST_RULES;

typedef struct {
    ST_IPOINT goal;
}ST_PLANNING;

typedef struct {
    int32_t time;
    ST_DSTATE dState;
}ST_PAIR;

typedef struct {
    int32_t vMin;
    int32_t vMax;
    int32_t accMax;
    int32_t decMax;
    int32_t laneChangeProb;
    int32_t cutInRange;
    int32_t initialLane;
}ST_OBEHAVIOR;

// === 3条车道 ===
const ST_BOUND leftLane1 = {{{0, 17}, {1990, 17}}, false};
const ST_BOUND rightLane1 = {{{0, -17}, {1990, -17}}, false};
const ST_LANE lane1 = {1, leftLane1, rightLane1, {NONE}, {NONE}, 2, false, NONE, false};

const ST_BOUND leftLane2 = {{{0, 52}, {1990, 52}}, false};
const ST_BOUND rightLane2 = {{{0, 17}, {1990, 17}}, false};
const ST_LANE lane2 = {2, leftLane2, rightLane2, {NONE}, {NONE}, 3, true, 1, false};

const ST_BOUND leftLane3 = {{{0, 87}, {1990, 87}}, false};
const ST_BOUND rightLane3 = {{{0, 52}, {1990, 52}}, false};
const ST_LANE lane3 = {3, leftLane3, rightLane3, {NONE}, {NONE}, NONE, false, 2, true};

const ST_LANE laneNet[MAXL] = {lane1, lane2, lane3};

const bool staticObsExists = true;
const ST_RECTANGLE staticObs[MAXSO] = {{{300, 35}, 20, 45, 0}};

const ST_PLANNING planning = {{995, 0}};

// Generated scenario ends

'''

# 找到模板中的标记位置，替换内容
start_marker = "<declaration>// Generated scenario starts"
end_marker = "// Generated scenario ends"

start_idx = template.index(start_marker)
end_idx = template.index(end_marker) + len(end_marker)

# 替换场景声明部分
new_template = template[:start_idx] + start_marker + "\n" + scenario_data + "\n" + template[end_idx:]

# 替换 moving obstacles 部分
obs_start = "<system>// Generated moving obstacles starts"
obs_end = "// Generated moving obstacles ends"
obs_start_idx = new_template.index(obs_start)
obs_end_idx = new_template.index(obs_end) + len(obs_end)

# 关键：Obs0 在 ego 正前方3米，几乎静止
obs_data = """<system>// Generated moving obstacles starts
const ST_DSTATE initCS0 = {{18.0, 0.0}, 1.0, 0.0, 0.0, 0.0, 0.0};
const ST_RECTANGLE shapeObs0 = {{180, 0}, 20, 45, 0};
const ST_OBEHAVIOR obsBehavior0 = {d2i(0.5), d2i(3.0), d2i(3.0), d2i(4.0), d2i(0.3), d2i(50.0), d2i(0.0)};
obs0 = Obstacle(0, initCS0, shapeObs0, obsBehavior0);
const ST_DSTATE initCS1 = {{100.0, 0.0}, 22.0, 0.0, 0.0, 0.0, 0.0};
const ST_RECTANGLE shapeObs1 = {{1000, 0}, 18, 43, 0};
const ST_OBEHAVIOR obsBehavior1 = {d2i(11.0), d2i(33.0), d2i(3.0), d2i(4.0), d2i(0.3), d2i(50.0), d2i(0.0)};
obs1 = Obstacle(1, initCS1, shapeObs1, obsBehavior1);
// Generated moving obstacles ends"""

new_template = new_template[:obs_start_idx] + obs_data + new_template[obs_end_idx:]

# 替换 ego vehicle 部分
ego_start = "// Generated ego vehicle starts"
ego_end = "// Generated ego vehicle ends"
ego_start_idx = new_template.index(ego_start)
ego_end_idx = new_template.index(ego_end) + len(ego_end)

ego_data = """// Generated ego vehicle starts
const ST_DSTATE initEgo = {{15.0, 0.0}, 22.0, 0.0, 0.0, 0.0, 0.0};
const ST_RECTANGLE initShapeEgo = {{150, 0}, 10, 45, 0};
const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};
const int[0,MAXL] initLane = 0;
move = Act_Move(0);
turn = Act_Turn(1);
controller = Controller(initLane,initEgo,initShapeEgo,rules);
timer = Timer();
dynamics = Dynamics();
rewardMachine = Rewards();
// Generated ego vehicle ends"""

new_template = new_template[:ego_start_idx] + ego_data + new_template[ego_end_idx:]

# 替换 system 声明
sys_start = "// Generated model instances starts"
sys_end = "// Generated model instances ends"
sys_start_idx = new_template.index(sys_start)
sys_end_idx = new_template.index(sys_end) + len(sys_end)

sys_data = """// Generated model instances starts
system timer, obs0, obs1, move, turn, controller, dynamics, rewardMachine;
// Generated model instances ends"""

new_template = new_template[:sys_start_idx] + sys_data + new_template[sys_end_idx:]

# 清除旧的 queries，只留关键的
queries_start = "<queries>"
queries_end = "</queries>"
queries_start_idx = new_template.index(queries_start)
queries_end_idx = new_template.index(queries_end) + len(queries_end)

new_queries = """<queries>
    <query>
        <formula>E&lt;&gt; cps_i_state.detection.collide</formula>
        <comment>存在碰撞路径？</comment>
    </query>
    <query>
        <formula>A[] !cps_i_state.detection.collide</formula>
        <comment>所有路径都不碰撞？FALSE=必撞</comment>
    </query>
    <query>
        <formula>E&lt;&gt; cps_i_state.detection.reach &amp;&amp; !cps_i_state.detection.collide</formula>
        <comment>能安全到达目标？</comment>
    </query>
</queries>"""

new_template = new_template[:queries_start_idx] + new_queries + new_template[queries_end_idx:]

# 写入文件
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(new_template)

print(f"Generated: {OUTPUT}")
print()
print("场景设置：")
print("  Ego:  pos=(15, 0), vel=22 m/s (80 km/h)")
print("  Obs0: pos=(18, 0), vel=1 m/s  → 正前方3米，几乎静止！")
print("  Obs1: pos=(100,0), vel=22 m/s → 远处无影响")
print()
print("预期结果：A[] !collide = FALSE（必撞）")
print("原因：ego速度22m/s，前方3米有慢车，IDM最大刹车-4m/s²，需要110米才能停下，必然追尾")
