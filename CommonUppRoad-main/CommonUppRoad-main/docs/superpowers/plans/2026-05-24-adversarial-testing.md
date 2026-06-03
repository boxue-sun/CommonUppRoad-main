# 自动驾驶对抗性测试 UPPAAL 改造 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 改造 CommonUppRoad 项目，实现：智能IDM ego车 + 行为参数化障碍物 + 自动化必撞场景挖掘

**Architecture:** 修改 UPPAAL template.xml（Controller加IDM、Obstacle改行为自动机），改造 generate_uppaal_models.py（生成行为参数而非固定轨迹），新建 adversarial_search.py（场景变异 + 模型批量生成），用户用 Windows UPPAAL GUI 验证，结果收集后可视化分析。

**Tech Stack:** Python 3.10+, commonroad-io, numpy, matplotlib, UPPAAL 5.x (Windows GUI)

---

## 里程碑总览（组会汇报节奏）

| 时间 | 汇报内容 | 核心交付 |
|------|----------|----------|
| 第2周 | IDM ego车UPPAAL建模 | ego能沿车道行驶到目标，演示一个场景 |
| 第4周 | 障碍物行为参数化 + 必撞验证 | 展示第一个"必撞场景"反例 |
| 第6周 | 自动化挖掘框架 + 初步实验 | 5+个必撞场景，对比实验表格 |
| 第8周 | 完整实验 + 论文大纲 | 全部实验图表，论文Ch3-5初稿 |

---

## Sprint 1: IDM智能Ego车（第1-2周）

### Task 1.1: 分析现有UPPAAL控制流程

**Files:**
- Read: `uppaal/template.xml:376-468` (Act_Move模板)
- Read: `uppaal/template.xml:469-554` (Controller模板)
- Read: `uppaal/template.xml:1-375` (全局声明)

梳理清楚当前ego车决策-执行-动力学的完整数据流。

- [ ] **Step 1: 画出控制流图**

```
当前控制流:
Timer(sense!) → Controller.sensor() → 更新cps_i_state
Timer(decide!) → Controller → Act_Move(perform[0]!) 非确定性选gear
                            → Act_Turn(perform[1]!) 非确定性选gear
Dynamics(ODE) → cps_dynamic 连续演化
Timer(end!) → 结束检测
```

- [ ] **Step 2: 记录关键数据结构位置**

```
cps_i_state.position  - 当前位置 (ST_DPOINT)
cps_i_state.velocity  - 当前速度 (double)
cps_i_state.orientation - 当前朝向 (double)
cps_i_state.acceleration - 当前加速度 (double)
cps_i_state.accRate   - 加速度变化率 (double)
cps_i_state.yawRate   - 横摆角速度 (double)
cps_dynamic.x/y/velocity/acceleration/orientation - 连续动态变量
```

- [ ] **Commit:** `docs: 控制流分析笔记`

---

### Task 1.2: 在Controller模板中添加IDM函数

**Files:**
- Modify: `uppaal/template.xml:431-468` (Controller declaration部分)

在Controller模板的declaration中新增IDM纵向控制函数。

- [ ] **Step 1: 写IDM加速度计算函数**

在 Controller 模板的 `<declaration>` 标签内，现有函数之后添加：

```c
// === IDM 参数 (可配置) ===
const double IDM_V0 = 30.0;       // 期望速度 m/s
const double IDM_T = 1.5;         // 安全时距 s
const double IDM_S0 = 2.0;        // 最小间距 m
const double IDM_A_MAX = 2.0;     // 最大加速度 m/s²
const double IDM_B_COMF = 1.5;    // 舒适减速度 m/s²
const double IDM_DELTA = 4.0;     // 加速度指数

// 找前方最近车辆，返回距离和速度
// targetLane: 要检查的车道ID，NONE表示检查所有车道
void findVehicleAhead(const ST_ISTATE &egoState, const int targetLane, 
                       double &gap, double &vLead) {
    int i = 0;
    double minDist = FLT_MAX;
    double egoVx = 0.0, egoVy = 0.0;
    double obsVx = 0.0, obsVy = 0.0;
    double relDist = 0.0;
    double egoDirX = 0.0, egoDirY = 0.0;
    double projDist = 0.0;
    
    gap = FLT_MAX;
    vLead = 0.0;
    
    egoDirX = cos(egoState.orientation);
    egoDirY = sin(egoState.orientation);
    
    for (i = 0; i < MAXOBS; i++) {
        // 计算前方距离（纵向投影）
        relDist = (obs_i_state[i].position.x - egoState.position.x) * egoDirX +
                  (obs_i_state[i].position.y - egoState.position.y) * egoDirY;
        
        if (relDist > 0 && relDist < minDist) {
            minDist = relDist;
            gap = sqrt(pow(obs_i_state[i].position.x - egoState.position.x, 2) +
                       pow(obs_i_state[i].position.y - egoState.position.y, 2));
            vLead = i2d(obs_i_state[i].velocity);
        }
    }
}

// IDM 纵向加速度计算
double computeIDM(double v, double vLead, double gap) {
    double s_star = 0.0;
    double acc = 0.0;
    double vRatio = 0.0;
    double gapRatio = 0.0;
    
    vRatio = v / IDM_V0;
    s_star = IDM_S0 + v * IDM_T + 
             v * (v - vLead) / (2.0 * sqrt(IDM_A_MAX * IDM_B_COMF));
    
    if (gap < 0.001) {
        gap = 0.001;
    }
    gapRatio = s_star / gap;
    
    acc = IDM_A_MAX * (1.0 - pow(vRatio, IDM_DELTA) - pow(gapRatio, 2.0));
    
    return acc;
}
```

- [ ] **Step 2: 修改Controller::reload()函数，加入IDM控制逻辑**

将原来的 `reload()` 改为：

```c
void reload(){
    actID = 0;
}

// 新增：IDM决策函数（替代非确定性选择）
void makeDecision(){
    double gap = FLT_MAX;
    double vLead = 0.0;
    double vEgo = 0.0;
    double idmAcc = 0.0;
    
    vEgo = i2d(cps_i_state.velocity);
    findVehicleAhead(cps_i_state, NONE, gap, vLead);
    idmAcc = computeIDM(vEgo, vLead, gap);
    
    // 将IDM结果写入控制量
    cps_i_state.accRate = d2i(idmAcc);
}
```

- [ ] **Commit:** `feat: add IDM longitudinal control functions to Controller template`

---

### Task 1.3: 修改Act_Move模板使其使用IDM输出

**Files:**
- Modify: `uppaal/template.xml:376-427` (Act_Move模板)

- [ ] **Step 1: 简化Act_Move模板**

Act_Move不再做非确定性选择，改为读取Controller已计算好的accRate：

```xml
<template>
    <name x="5" y="5">Act_Move</name>
    <parameter>const act_id_t id</parameter>
    <declaration>
void act(){
    // IDM加速度已在 reload/makeDecision 中写入 cps_i_state.accRate
    // 此处仅做限幅
    if(cps_i_state.accRate &gt; MAX_ACC){
        cps_i_state.accRate = MAX_ACC;
    }
    if(cps_i_state.accRate &lt; MIN_ACC){
        cps_i_state.accRate = MIN_ACC;
    }
}
    </declaration>
    <location id="id0" x="-204" y="0">
        <name x="-221" y="17">Wait</name>
    </location>
    <location id="id1" x="-68" y="0">
        <name x="-102" y="17">Execute</name>
        <committed/>
    </location>
    <init ref="id0"/>
    <transition>
        <source ref="id1"/>
        <target ref="id0"/>
        <label kind="assignment" x="-161" y="-51">act()</label>
        <nail x="-68" y="-68"/>
        <nail x="-204" y="-68"/>
    </transition>
    <transition>
        <source ref="id0"/>
        <target ref="id1"/>
        <label kind="synchronisation" x="-178" y="-25">perform[id]?</label>
    </transition>
</template>
```

- [ ] **Commit:** `refactor: simplify Act_Move to use deterministic IDM output`

---

### Task 1.4: 简化Act_Turn模板

**Files:**
- Modify: `uppaal/template.xml:428-468` (Act_Turn模板)

当前Act_Turn做了三个选择(左转/直行/右转)，改造后ego车由MOBIL规则或简单地跟随车道中线行驶。

- [ ] **Step 1: 简化为车道保持**

```xml
<template>
    <name>Act_Turn</name>
    <parameter>const act_id_t id</parameter>
    <declaration>
void laneKeeping(){
    // 简单车道保持：不转向
    cps_i_state.yawRate = d2i(0.0);
}
    </declaration>
    <location id="id4" x="170" y="102">
        <name x="136" y="119">Execute</name>
        <committed/>
    </location>
    <location id="id5" x="34" y="102">
        <name x="17" y="119">Wait</name>
    </location>
    <init ref="id5"/>
    <transition>
        <source ref="id4"/>
        <target ref="id5"/>
        <label kind="assignment" x="76" y="51">laneKeeping()</label>
        <nail x="170" y="34"/>
        <nail x="34" y="34"/>
    </transition>
    <transition>
        <source ref="id5"/>
        <target ref="id4"/>
        <label kind="synchronisation" x="59" y="76">perform[id]?</label>
    </transition>
</template>
```

- [ ] **Commit:** `refactor: simplify Act_Turn to lane-keeping behavior`

---

### Task 1.5: 更新Controller模板的决策调用

**Files:**
- Modify: `uppaal/template.xml:552-557` (Controller::reload)

- [ ] **Step 1: 在Controller中接入makeDecision**

找到Controller的transition中调用 `reload()` 的地方，改为或增加 `makeDecision()` 调用。找到transition `id14` (发送perform前)：

```xml
<transition id="id14">
    <source ref="id10"/>
    <target ref="id9"/>
    <label kind="guard" x="-170" y="-102">actID==MAXACT-1</label>
    <label kind="synchronisation" x="-170" y="-119">perform[actID]!</label>
    <label kind="assignment" x="-170" y="-85">reload()</label>
    <nail x="-136" y="-85"/>
</transition>
```

在reload()中或perform触发前加入makeDecision:

```c
void reload(){
    makeDecision();  // 调用IDM做好决策
    actID = 0;
}
```

- [ ] **Commit:** `feat: wire IDM decision into Controller reload cycle`

---

### Task 1.6: 生成一个测试模型并验证

**Files:**
- Modify: `generate_uppaal_models.py:269-270` (IDM参数声明)

- [ ] **Step 1: 在generate_uppaal_models.py中加入IDM参数声明**

在场景参数输出部分加入：

```python
# 在第269行附近加入
IDM_PARAMS_str = (
    f"const double IDM_V0 = 30.0;\n"
    f"const double IDM_T = 1.5;\n"
    f"const double IDM_S0 = 2.0;\n"
    f"const double IDM_A_MAX = 2.0;\n"
    f"const double IDM_B_COMF = 1.5;\n"
    f"const double IDM_DELTA = 4.0;\n"
)
```

然后在 scenario_prompt 之后、write_large_block 之前的位置，把IDM参数写入。实际上这些参数已经在template.xml的Controller中声明了，所以只需要确认generate脚本不覆盖它们即可。

- [ ] **Step 2: 生成测试模型**

在Linux上运行：
```bash
python generate_uppaal_models.py
```

- [ ] **Step 3: 在Windows UPPAAL GUI中测试**

打开 `uppaal/models/ZAM_Tutorial-1_2_T-1_generated_lanelet.xml`，运行：
```
simulate[<=MAXTIME;1]{cps_dynamic.x, cps_dynamic.y, cps_dynamic.velocity}
```

验证：
- Ego车从初始位置出发
- 沿车道行驶，速度受IDM控制
- 到达目标区域后停止
- 不与静态障碍物碰撞

- [ ] **Commit:** `test: verify IDM ego vehicle in ZAM_Tutorial scenario`

---

### Sprint 1 组会汇报材料

- 1张架构图：改造前后的控制流对比
- 1个GIF：ego车在场景中沿车道行驶
- 1页PPT：IDM公式 + UPPAAL实现要点

---

## Sprint 2: 行为参数化障碍物 + 必撞验证（第3-4周）

### Task 2.1: 设计新的Obstacle行为自动机

**Files:**
- Create: `docs/obstacle_automaton_design.md` (设计文档，非论文)

- [ ] **Step 1: 画出障碍物行为自动机状态图**

```
                  ┌─────────────┐
     initialize──→│   巡航跟随    │←──────────┐
                  │ CruiseFollow │           │
                  └──────┬──────┘           │
                         │                   │
                   每N步决策一次              │
                         │                   │
              ┌──────────┼──────────┐        │
              ▼          ▼          ▼        │
         ┌────────┐ ┌────────┐ ┌────────┐   │
         │ 急加速  │ │ 匀速   │ │ 急减速  │   │
         │ Accel  │ │ Cruise │ │ Brake  │   │
         └───┬────┘ └───┬────┘ └───┬────┘   │
             │           │          │        │
             └───────────┼──────────┘        │
                         │                   │
              ┌──────────┼──────────┐        │
              ▼          ▼          ▼        │
         ┌────────┐ ┌────────┐ ┌────────┐   │
         │ 左换道  │ │ 保持   │ │ 右换道  │   │
         │ LaneL  │ │ Stay   │ │ LaneR  │   │
         └───┬────┘ └───┬────┘ └───┬────┘   │
             │           │          │        │
             └───────────┼──────────┘        │
                         ▼                   │
                  ┌─────────────┐            │
                  │   执行动作    │────────────┘
                  │  Execute    │
                  └─────────────┘
```

- [ ] **Step 2: 定义行为参数数据结构**

```c
// 新增到 parseCR/utils.py 的 write_large_block 中
typedef struct {
    double vMin;          // 最小速度
    double vMax;          // 最大速度  
    double accMax;        // 最大加速度
    double decMax;        // 最大减速度
    double laneChangeProb;// 换道概率
    double cutInRange;    // 切入感知范围
    int initialLane;      // 初始车道
}ST_OBEHAVIOR;
```

- [ ] **Commit:** `docs: obstacle behavior automaton design`

---

### Task 2.2: 修改parseCR/utils.py添加行为参数结构

**Files:**
- Modify: `parseCR/utils.py`

- [ ] **Step 1: 在write_large_block中添加ST_OBEHAVIOR类型定义**

在 `write_large_block()` 函数的 `large_block` 字符串中，ST_PAIR定义之后添加：

```c
typedef struct {
    int32_t vMin;
    int32_t vMax;
    int32_t accMax;
    int32_t decMax;
    int32_t laneChangeProb;
    int32_t cutInRange;
    int32_t initialLane;
}ST_OBEHAVIOR;
```

- [ ] **Commit:** `feat: add ST_OBEHAVIOR type for parameterized obstacle behavior`

---

### Task 2.3: 改造Obstacle UPPAAL模板为行为自动机

**Files:**
- Modify: `uppaal/template.xml:701-847` (Obstacle模板)

这是最关键的任务。需要把整个Obstacle模板从"轨迹回放"改为"行为自动机"。

- [ ] **Step 1: 重写Obstacle模板的declaration**

```c
// === Obstacle模板新声明 ===
const int32_t OBS_DECISION_PERIOD = 4;  // 每4步做一次决策

uint8_t pc = 0;     // 决策计数器
uint8_t tc = 0;     // 时间计数器

int32_t obs_vMin = 0;     // 最小速度(m/s) → d2i换算
int32_t obs_vMax = 0;     // 最大速度(m/s)
int32_t obs_accMax = 0;   // 最大加速度
int32_t obs_decMax = 0;   // 最大减速度
int32_t obs_curLane = 0;  // 当前车道
int32_t obs_targetLane = 0; // 目标车道

void followShape(){
    obs_shape[id].center = obs_i_state[id].position;
    obs_shape[id].orientation = obs_i_state[id].orientation;
}

// 纵向行为选择: 0=减速, 1=匀速, 2=加速
int[0,2] chooseLonAction(double egoDist, double egoSpeed, double mySpeed) {
    int[0,2] action = 1;
    
    // 如果ego在后面很近且我速度低于ego→加速(防止被追尾，制造危险)
    if (egoDist < i2d(d2i(30.0)) && egoDist > 0 && mySpeed < egoSpeed) {
        action = 2;  // 加速
    }
    // 非确定性: 在ego前方时可能急刹
    if (egoDist < i2d(d2i(50.0)) && egoDist > 0) {
        // 非确定性选择是否急刹 (由UPPAAL穷举)
    }
    
    return action;
}

// 横向行为选择: -1=左换道, 0=保持, 1=右换道
int[-1,1] chooseLatAction(double egoDist) {
    int[-1,1] action = 0;
    
    // 如果ego在可切入范围内，非确定性选换道方向
    // (此处UPPAAL会穷举所有可能)
    
    return action;
}

// 执行选择的行为
void applyAction(int[0,2] lon, int[-1,1] lat) {
    int32_t targetAcc = 0;
    int32_t targetYaw = 0;
    
    // 纵向执行
    if (lon == 0) {
        targetAcc = d2i(-3.0);  // 急刹
    } else if (lon == 1) {
        targetAcc = d2i(0.0);   // 匀速
    } else {
        targetAcc = d2i(2.0);   // 加速
    }
    
    // 横向执行
    if (lat == -1) {
        targetYaw = d2i(-0.3);  // 左转
    } else if (lat == 1) {
        targetYaw = d2i(0.3);   // 右转
    }
    
    obs_i_state[id].acceleration = targetAcc;
    obs_i_state[id].yawRate = targetYaw;
}

void decisionMaking() {
    int[0,2] lon;
    int[-1,1] lat;
    double egoDist = 0.0;
    double egoSpeed = 0.0;
    double mySpeed = 0.0;
    
    // 计算与ego的距离
    egoDist = sqrt(pow(obs_i_state[id].position.x - cps_i_state.position.x, 2.0) +
                   pow(obs_i_state[id].position.y - cps_i_state.position.y, 2.0));
    egoSpeed = i2d(cps_i_state.velocity);
    mySpeed = i2d(obs_i_state[id].velocity);
    
    // 非确定性选择动作 (UPPAAL穷举所有组合)
    lon = chooseLonAction(egoDist, egoSpeed, mySpeed);
    lat = chooseLatAction(egoDist);
    applyAction(lon, lat);
}

void initCon() {
    obs_dynamic[id].x = obs_i_state[id].position.x;
    obs_dynamic[id].y = obs_i_state[id].position.y;
    obs_dynamic[id].velocity = mTimeStep(obs_i_state[id].velocity);
    obs_dynamic[id].orientation = obs_i_state[id].orientation;
}

void initDis() {
    // 初始状态由场景参数提供
    obs_i_state[id].position.x = d2i(initCS.position.x);
    obs_i_state[id].position.y = d2i(initCS.position.y);
    obs_i_state[id].velocity = d2i(mTimeStep(initCS.velocity));
    obs_i_state[id].orientation = d2i(initCS.orientation);
}

void updateDis() {
    double vx = 0.0, vy = 0.0;
    double rVelocity = 0.0;
    double rOrientation = 0.0;
    int32_t dVx = 0, dVy = 0;
    double step = mTimeStep(1.0);
    
    // 用加速度更新速度
    obs_i_state[id].velocity = obs_i_state[id].velocity + 
        d2i(i2d(obs_i_state[id].acceleration) * step);
    
    // 速度限幅
    if (obs_i_state[id].velocity > d2i(35.0)) {
        obs_i_state[id].velocity = d2i(35.0);
    }
    if (obs_i_state[id].velocity < d2i(0.0)) {
        obs_i_state[id].velocity = d2i(0.0);
    }
    
    rVelocity = i2d(obs_i_state[id].velocity);
    rOrientation = i2d(obs_i_state[id].orientation);
    
    vx = rVelocity * cos(rOrientation);
    vy = rVelocity * sin(rOrientation);
    
    obs_i_state[id].position.x = obs_i_state[id].position.x + d2i(vx * step);
    obs_i_state[id].position.y = obs_i_state[id].position.y + d2i(vy * step);
    followShape();
}

void initialize() {
    pc = 0;
    tc = 0;
    initDis();
    initCon();
    obs_shape[id] = shape;
    followShape();
}

void change(){
    updateDis();
    if (tc % OBS_DECISION_PERIOD == 0 || tc == 0) {
        decisionMaking();  // 行为决策
    }
    tc++;
}
```

- [ ] **Step 2: 更新Obstacle模板的transition**

保持transition结构不变（start/end/sense），但change()函数的行为已改为行为自动机。

- [ ] **Commit:** `feat: rewrite Obstacle template as behavior automaton`

---

### Task 2.4: 修改generate_uppaal_models.py生成行为参数

**Files:**
- Modify: `generate_uppaal_models.py:146-210` (动态障碍物声明部分)

- [ ] **Step 1: 将轨迹声明改为行为参数声明**

```python
# 替换原来的 trajectory_str 生成逻辑
# 每个动态障碍物生成行为参数而不是固定轨迹

# 新逻辑：从场景中提取障碍物初始状态，生成行为参数
for dyn_obs in scenario.dynamic_obstacles:
    obs_width = int(dyn_obs._obstacle_shape._width * pow(BASE, EXPONENT))
    obs_length = int(dyn_obs._obstacle_shape._length * pow(BASE, EXPONENT))
    obs_id = obs_count
    obs_count += 1
    
    # 提取初始状态（用于initDis）
    obs_ini_pos = dyn_obs._initial_state.position
    obs_ini_vel = dyn_obs._initial_state.velocity
    obs_ini_ori = dyn_obs._initial_state.orientation
    obs_ini_acc = DEFAULT_VAL
    obs_ini_jerk = DEFAULT_VAL
    obs_ini_yaw = DEFAULT_VAL
    
    # === 根据场景自动推断行为参数范围 ===
    # 有轨迹的场景：用轨迹速度范围作为参数
    if hasattr(dyn_obs, 'prediction') and dyn_obs.prediction is not None:
        traj = dyn_obs.prediction.trajectory.state_list
        if len(traj) > 0:
            speeds = [s.velocity for s in traj if hasattr(s, 'velocity')]
            if speeds:
                v_min_val = max(0, min(speeds) * 0.5)
                v_max_val = max(speeds) * 1.5
            else:
                v_min_val = 5.0
                v_max_val = 20.0
        else:
            v_min_val = 5.0
            v_max_val = 20.0
    else:
        v_min_val = 5.0
        v_max_val = 20.0
    
    # 生成行为参数声明
    behavior_str = (
        f"const ST_OBEHAVIOR obsBehavior{obs_id} = {{"
        f"d2i({v_min_val}), d2i({v_max_val}), "
        f"d2i(3.0), d2i(4.0), "  # accMax, decMax
        f"d2i(0.3), d2i(50.0), "  # laneChangeProb, cutInRange
        f"d2i(0.0)"               # initialLane (暂用0)
        f"}};"
    )
    
    # 初始状态声明（保持原有格式）
    initCS_str = f"const ST_DSTATE initCS{obs_id} = {{...}};"  # 同上逻辑
    shapeObs_str = f"const ST_RECTANGLE shapeObs{obs_id} = {{...}};"
    Obstacle_str = f"obs{obs_id} = Obstacle({obs_id}, initCS{obs_id}, shapeObs{obs_id}, obsBehavior{obs_id});"
```

- [ ] **Step 2: 回退MAXTP相关声明**

不再需要 `MAXTP`、`ST_PAIR`、`trajectory`、`PHOLDER` 等常量。在生成代码中移除或设为最小值。

- [ ] **Commit:** `feat: generate behavior parameters instead of fixed trajectories`

---

### Task 2.5: 编写必撞性验证查询

**Files:**
- Create: `uppaal/query_adversarial.q`

- [ ] **Step 1: 写查询文件**

```c
// ==========================================
// 必撞场景验证查询集
// ==========================================

// Q1: 是否存在一条路径导致碰撞？
// 如果为TRUE，存在碰撞可能
E<> cps_i_state.detection.collide

// Q2: 在所有可能的障碍物行为下，ego总是安全的吗？
// 如果为FALSE，存在"必撞"场景（无论ego怎么做都会撞）
A[] !cps_i_state.detection.collide

// Q3: ego是否能安全到达目标？
// 如果为FALSE，考虑所有障碍物行为，ego无法到达
E<> cps_i_state.detection.reach && !cps_i_state.detection.collide

// Q4: 碰撞发生的概率上界？
// SMC: 统计模型检验
Pr[<=MAXTIME](<> cps_i_state.detection.collide)

// Q5: 获取反例轨迹（在UPPAAL GUI的诊断模式中查看）
// A[] !cps_i_state.detection.collide的反例 = 必撞场景

// Q6: 碰撞严重程度
// 观察碰撞时的速度、相对角度
E<> cps_i_state.detection.collide && cps_i_state.velocity >= d2i(10.0)
```

- [ ] **Commit:** `feat: add adversarial verification queries`

---

### Task 2.6: 端到端测试第一个必撞场景

**Files:**
- Read+Modify: `generate_uppaal_models.py`
- Read: `uppaal/template.xml`

- [ ] **Step 1: 生成新的UPPAAL模型**

```bash
python generate_uppaal_models.py
```

- [ ] **Step 2: 在Windows UPPAAL GUI中打开模型**

打开 `uppaal/models/DEU_Ffb-1_3_T-1_generated_lanelet.xml`

- [ ] **Step 3: 运行验证查询**

在UPPAAL的Verifier标签中加载 `query_adversarial.q`，运行：
- `E<> cps_i_state.detection.collide` → 检查是否有碰撞路径
- `A[] !cps_i_state.detection.collide` → 检查是否总能安全

- [ ] **Step 4: 如果找到反例，截图/导出trace**

记录反例中每一步的：ego位置、obs位置、速度、碰撞时刻

- [ ] **Commit:** `test: end-to-end verification of first adversarial scenario`

---

### Sprint 2 组会汇报材料

- 1张图：Obstacle行为自动机状态图
- 1张截图：UPPAAL GUI验证结果（A[] !collision = FALSE + 反例trace）
- 1张GIF：反例的可视化（碰撞场景）
- 1页PPT：行为参数化 vs 固定轨迹的对比

---

## Sprint 3: 自动化挖掘框架 + 初步实验（第5-6周）

### Task 3.1: 创建场景变异脚本

**Files:**
- Create: `adversarial_search.py`

- [ ] **Step 1: 写入场景参数变异器**

```python
#!/usr/bin/env python3
"""
adversarial_search.py — 自动化必撞场景挖掘框架
用于硕士论文：基于形式化验证(UPPAAL)的自动驾驶对抗性测试方法研究

工作流程:
  1. 读取基础CommonRoad场景
  2. 在参数空间内产生变异
  3. 为每个变异生成UPPAAL模型
  4. 用户可在UPPAAL GUI中批量验证
  5. 收集结果，统计必撞场景
"""

import os
import sys
import copy
import itertools
import json
import numpy as np
from datetime import datetime
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.state import CustomState, InitialState
from commonroad.geometry.shape import Rectangle
from commonroad.scenario.trajectory import Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction

# === 参数空间定义 ===
# 对标师兄论文的实验参数表
PARAM_SPACE = {
    # 障碍物初始条件
    'obs_initial_speed': {
        'type': 'continuous',
        'range': [5.0, 30.0],
        'step': 5.0,
        'description': '障碍物初始速度 (m/s)',
    },
    'obs_longitudinal_offset': {
        'type': 'continuous', 
        'range': [-50.0, 50.0],
        'step': 10.0,
        'description': '障碍物纵向偏移 (m)',
    },
    'obs_lateral_offset': {
        'type': 'discrete',
        'values': [-1, 0, 1],
        'description': '障碍物相对于ego的车道偏移 (-1=左, 0=同, 1=右)',
    },
    'obs_count': {
        'type': 'discrete',
        'values': [1, 2, 3],
        'description': '障碍车数量',
    },
    
    # 障碍物行为参数
    'obs_max_speed_factor': {
        'type': 'continuous',
        'range': [0.8, 2.0],
        'step': 0.2,
        'description': '障碍物最大速度系数',
    },
    'obs_brake_aggressiveness': {
        'type': 'continuous',
        'range': [2.0, 8.0],
        'step': 2.0,
        'description': '急刹车减速度 (m/s²)',
    },
    
    # Ego初始条件
    'ego_initial_speed': {
        'type': 'continuous',
        'range': [10.0, 30.0],
        'step': 5.0,
        'description': 'Ego车初始速度 (m/s)',
    },
    'ego_target_speed': {
        'type': 'continuous',
        'range': [15.0, 35.0],
        'step': 5.0,
        'description': 'IDM期望速度 (m/s)',
    },
}


class ScenarioMutator:
    """场景变异器 — 在参数空间内采样生成场景变体"""
    
    def __init__(self, base_scenario_path):
        self.base_path = base_scenario_path
        self.scenario, self.planning_problem_set = \
            CommonRoadFileReader(base_scenario_path).open()
        self.mutations = []
    
    def grid_search(self, param_keys=None):
        """网格搜索：穷举所有参数组合（小参数空间用）"""
        if param_keys is None:
            param_keys = ['obs_initial_speed', 'ego_initial_speed', 
                         'obs_longitudinal_offset']
        
        param_specs = {k: PARAM_SPACE[k] for k in param_keys}
        values_list = []
        
        for key, spec in param_specs.items():
            if spec['type'] == 'continuous':
                r = spec['range']
                values = np.arange(r[0], r[1] + spec['step']/2, spec['step'])
                values_list.append(list(values))
            elif spec['type'] == 'discrete':
                values_list.append(spec['values'])
        
        for combo in itertools.product(*values_list):
            params = dict(zip(param_keys, combo))
            self.mutations.append(params)
        
        print(f"[GridSearch] {len(self.mutations)} combinations generated")
        return self.mutations
    
    def latin_hypercube(self, n_samples=200, param_keys=None):
        """拉丁超立方采样：均匀覆盖大参数空间"""
        if param_keys is None:
            param_keys = list(PARAM_SPACE.keys())
        
        n_dims = len(param_keys)
        # LHS: 每个维度分成n_samples个区间，各取一点
        segments = np.linspace(0, 1, n_samples + 1)
        samples = np.zeros((n_samples, n_dims))
        
        for i in range(n_dims):
            # 随机排列区间
            perm = np.random.permutation(n_samples)
            for j in range(n_samples):
                lo = segments[perm[j]]
                hi = segments[perm[j] + 1]
                samples[j, i] = lo + np.random.random() * (hi - lo)
        
        for j in range(n_samples):
            params = {}
            for i, key in enumerate(param_keys):
                spec = PARAM_SPACE[key]
                if spec['type'] == 'continuous':
                    r = spec['range']
                    params[key] = r[0] + samples[j, i] * (r[1] - r[0])
                elif spec['type'] == 'discrete':
                    idx = int(samples[j, i] * len(spec['values']))
                    params[key] = spec['values'][min(idx, len(spec['values'])-1)]
            self.mutations.append(params)
        
        print(f"[LHS] {n_samples} samples generated")
        return self.mutations
    
    def apply_mutation(self, params):
        """将参数应用到场景，返回修改后的场景"""
        mutated_scenario = copy.deepcopy(self.scenario)
        
        # TODO: 根据params修改障碍物的初始状态
        # 修改初始速度、位置偏移、数量等
        # 修改ego初始状态
        
        return mutated_scenario
    
    def export_param_table(self, output_path='experiments/param_table.json'):
        """导出参数表（对标师兄论文的表5.1）"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                'param_space': {k: v for k, v in PARAM_SPACE.items()},
                'mutations': [
                    {'id': i, 'params': p} 
                    for i, p in enumerate(self.mutations)
                ],
                'total_count': len(self.mutations),
            }, f, indent=2, default=str)
        print(f"[Export] Parameter table saved to {output_path}")


class UppaalModelBatchGenerator:
    """UPPAAL模型批量生成器"""
    
    def __init__(self, template_path, output_dir):
        self.template_path = template_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_all(self, mutations, base_scenario):
        """为每个变异生成UPPAAL模型"""
        models = []
        for i, params in enumerate(mutations):
            model_name = f"variant_{i:04d}"
            model_path = os.path.join(self.output_dir, f"{model_name}.xml")
            
            # 生成UPPAAL XML（复用generate_uppaal_models.py的逻辑）
            self._generate_single(params, base_scenario, model_path)
            models.append({
                'id': i,
                'params': params,
                'model_path': model_path,
            })
        
        print(f"[Generate] {len(models)} UPPAAL models generated")
        return models
    
    def _generate_single(self, params, scenario, output_path):
        """生成单个UPPAAL模型"""
        # 调用现有的生成逻辑，但使用修改后的场景参数
        # （该函数将在Task 3.3中完成）
        pass


def main():
    """主入口"""
    import argparse
    parser = argparse.ArgumentParser(description='必撞场景挖掘框架')
    parser.add_argument('--scenario', type=str, 
                       default='scenarios/DEU_Ffb-1_3_T-1.xml',
                       help='基础CommonRoad场景路径')
    parser.add_argument('--method', type=str, default='grid',
                       choices=['grid', 'lhs'],
                       help='参数搜索方法')
    parser.add_argument('--n-samples', type=int, default=100,
                       help='LHS采样数量')
    parser.add_argument('--output', type=str, default='experiments/exp1',
                       help='输出目录')
    parser.add_argument('--export-table', action='store_true',
                       help='导出参数表JSON')
    
    args = parser.parse_args()
    
    # 1. 场景变异
    mutator = ScenarioMutator(args.scenario)
    if args.method == 'grid':
        mutator.grid_search()
    else:
        mutator.latin_hypercube(n_samples=args.n_samples)
    
    if args.export_table:
        mutator.export_param_table()
    
    # 2. 生成UPPAAL模型批次
    # generator = UppaalModelBatchGenerator(
    #     'uppaal/template.xml', 
    #     os.path.join(args.output, 'models')
    # )
    # models = generator.generate_all(mutator.mutations, mutator.scenario)
    
    print(f"\n[Done] Generated {len(mutator.mutations)} scenario variants")
    print(f"[Next] Copy models to Windows, open in UPPAAL GUI to verify")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 测试参数生成**

```bash
python adversarial_search.py --scenario scenarios/ZAM_Tutorial-1_2_T-1.xml \
    --method grid --export-table
```

验证：`experiments/param_table.json` 已生成，包含所有参数组合。

- [ ] **Commit:** `feat: scenario mutator with grid search and LHS`

---

### Task 3.2: 对接generate_uppaal_models.py的批量生成

**Files:**
- Modify: `generate_uppaal_models.py`

- [ ] **Step 1: 将generate_uppaal_models.py重构为可import的模块**

在文件末尾添加：

```python
def generate_model_for_scenario(scenario, planning_problem_set, output_path):
    """
    为单个场景生成UPPAAL模型
    参数:
        scenario: CommonRoad scenario对象
        planning_problem_set: 规划问题集
        output_path: 输出XML路径
    """
    template_file = os.path.dirname(__file__) + "/uppaal/template.xml"
    with open(template_file, 'r') as f:
        lines = f.readlines()
    
    # ... (复用现有的生成逻辑，但接受外部scenario参数)
    
    with open(output_path, 'w') as file:
        for line in lines:
            file.write(line)
            # ... (注入生成的声明)
    
    return output_path


def generate_batch(scenario_path, mutations, output_dir):
    """
    批量生成UPPAAL模型
    参数:
        scenario_path: 基础场景文件
        mutations: 参数变异列表
        output_dir: 输出目录
    """
    scenario, planning_problem_set = CommonRoadFileReader(scenario_path).open()
    
    models = []
    for i, params in enumerate(mutations):
        mutated = apply_params_to_scenario(scenario, params)
        output_path = f"{output_dir}/variant_{i:04d}.xml"
        generate_model_for_scenario(mutated, planning_problem_set, output_path)
        models.append(output_path)
    
    return models
```

- [ ] **Commit:** `refactor: make generate_uppaal_models importable for batch use`

---

### Task 3.3: 创建结果收集与分析脚本

**Files:**
- Create: `experiments/collect_results.py`

- [ ] **Step 1: 写结果收集脚本**

```python
#!/usr/bin/env python3
"""
collect_results.py — 收集UPPAAL GUI验证结果，生成分析报告

用户手动在UPPAAL GUI中运行每个模型的验证查询，
将结果填入results.csv，本脚本做汇总分析。
"""

import os
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter


class ResultCollector:
    """UPPAAL验证结果收集器"""
    
    def __init__(self, results_csv):
        self.results = []
        self._load(results_csv)
    
    def _load(self, csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['collision_found'] = row['collision_found'] == 'TRUE'
                row['params'] = json.loads(row['params'])
                self.results.append(row)
    
    def summary(self):
        """生成汇总统计"""
        total = len(self.results)
        collisions = sum(1 for r in self.results if r['collision_found'])
        
        return {
            'total_scenarios': total,
            'collision_scenarios': collisions,
            'safe_scenarios': total - collisions,
            'collision_rate': collisions / total if total > 0 else 0,
        }
    
    def by_param(self, param_name):
        """按参数分组统计碰撞率"""
        groups = {}
        for r in self.results:
            val = r['params'].get(param_name, 'unknown')
            if val not in groups:
                groups[val] = {'total': 0, 'collisions': 0}
            groups[val]['total'] += 1
            if r['collision_found']:
                groups[val]['collisions'] += 1
        
        return {
            val: g['collisions'] / g['total'] 
            for val, g in groups.items()
        }
    
    def plot_param_sensitivity(self, output_path='experiments/param_sensitivity.png'):
        """参数敏感性分析图（对标图5.3）"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        key_params = ['obs_initial_speed', 'ego_initial_speed',
                     'obs_longitudinal_offset', 'obs_max_speed_factor',
                     'obs_brake_aggressiveness', 'ego_target_speed']
        
        for ax, param in zip(axes, key_params):
            groups = self.by_param(param)
            if groups:
                keys = sorted(groups.keys(), key=lambda x: float(x) if isinstance(x, (int, float)) else 0)
                vals = [groups[k] for k in keys]
                ax.bar(range(len(keys)), vals)
                ax.set_xticks(range(len(keys)))
                ax.set_xticklabels([f'{k:.1f}' if isinstance(k, float) else str(k) for k in keys], 
                                   rotation=45, ha='right')
                ax.set_title(f'{param}')
                ax.set_ylabel('Collision Rate')
        
        fig.suptitle('Parameter Sensitivity Analysis', fontsize=14)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"[Plot] Saved to {output_path}")
    
    def export_latex_table(self, output_path='experiments/results_table.tex'):
        """生成LaTeX表格（对标表5.4）"""
        summary = self.summary()
        
        latex = r"""
\begin{table}[htbp]
\centering
\caption{必撞场景挖掘实验结果}
\label{tab:results}
\begin{tabular}{lcccc}
\hline
\textbf{场景类型} & \textbf{总数} & \textbf{必撞数} & \textbf{安全数} & \textbf{必撞率(\%)} \\
\hline
"""
        latex += f"高速公路 & {summary['total_scenarios']} & {summary['collision_scenarios']} & " \
                f"{summary['safe_scenarios']} & {summary['collision_rate']*100:.1f} \\\\\n"
        latex += r"""
\hline
\end{tabular}
\end{table}
"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(latex)
        print(f"[LaTeX] Table saved to {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='结果收集与分析')
    parser.add_argument('--results', type=str, required=True,
                       help='results.csv文件路径')
    parser.add_argument('--output', type=str, default='experiments',
                       help='输出目录')
    args = parser.parse_args()
    
    collector = ResultCollector(args.results)
    summary = collector.summary()
    
    print("=" * 50)
    print("必撞场景挖掘结果汇总")
    print("=" * 50)
    print(f"总场景数: {summary['total_scenarios']}")
    print(f"必撞场景: {summary['collision_scenarios']}")
    print(f"安全场景: {summary['safe_scenarios']}")
    print(f"必撞率:   {summary['collision_rate']*100:.1f}%")
    print("=" * 50)
    
    collector.plot_param_sensitivity(
        os.path.join(args.output, 'param_sensitivity.png')
    )
    collector.export_latex_table(
        os.path.join(args.output, 'results_table.tex')
    )


if __name__ == '__main__':
    main()
```

- [ ] **Commit:** `feat: result collection and analysis scripts`

---

### Task 3.4: 运行初步实验

**Files:**
- Create: `run_experiment1.py`

- [ ] **Step 1: 实验1 — 参数敏感性分析**

```python
#!/usr/bin/env python3
"""实验1: 参数对必撞概率的影响分析"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from adversarial_search import ScenarioMutator
# from generate_uppaal_models import generate_batch

def run_experiment_1():
    """参数敏感性实验"""
    print("[Exp1] 参数敏感性分析")
    print("=" * 50)
    
    # 1. 生成场景变体（小规模：便于手工验证）
    mutator = ScenarioMutator('scenarios/DEU_Ffb-1_3_T-1.xml')
    mutator.grid_search(param_keys=[
        'obs_initial_speed',    # 5个值
        'ego_initial_speed',    # 5个值
        'obs_longitudinal_offset', # 11个值
    ])  # 总共 5*5*11 = 275个变体
    
    mutator.export_param_table('experiments/exp1/param_table.json')
    
    # 2. 生成UPPAAL模型（到Linux目录）
    # generate_batch('scenarios/DEU_Ffb-1_3_T-1.xml', 
    #                mutator.mutations,
    #                'experiments/exp1/models')
    
    print(f"\n生成了 {len(mutator.mutations)} 个场景变体")
    print("下一步：在Windows UPPAAL GUI中打开模型，运行验证查询")
    print("将结果填入 experiments/exp1/results.csv")
    
    # 3. 采样缩减（如果不能全部手工验证）
    print(f"\n建议：先用LHS采样20个变体做预实验")
    return mutator

if __name__ == '__main__':
    run_experiment_1()
```

- [ ] **Step 2: 在Windows UPPAAL GUI中验证**

选20个变体，每个运行 `A[] !cps_i_state.detection.collide`，记录结果到 `experiments/exp1/results.csv`。

- [ ] **Step 3: 分析结果**

```bash
python experiments/collect_results.py \
    --results experiments/exp1/results.csv \
    --output experiments/exp1
```

- [ ] **Commit:** `exp: parameter sensitivity analysis results`

---

### Sprint 3 组会汇报材料

- 1张表：参数敏感性分析（哪个参数对碰撞率影响最大）
- 3-5张GIF：挖掘出的典型必撞场景
- 1张图：必撞场景参数空间分布图
- 1页PPT：自动化挖掘框架流程

---

## Sprint 4: 完整实验 + 可视化（第7-8周）

### Task 4.1: 多场景类型对比实验

**Files:**
- Create: `run_experiment2.py`

- [ ] **Step 1: 在3种场景类型上运行挖掘**

```python
# 实验2: 场景类型对比
scenarios = [
    ('highway', 'scenarios/DEU_Ffb-1_3_T-1.xml'),
    ('merging', 'scenarios/ZAM_Ramp-1_1-T-1.xml'),
    ('t_junction', 'scenarios/ZAM_Tjunction-1_216_T-1.xml'),
]

for scene_type, path in scenarios:
    # 每种场景生成50个LHS变体
    mutator = ScenarioMutator(path)
    mutator.latin_hypercube(n_samples=50)
    # 生成模型、验证（手工）、收集结果
```

- [ ] **Commit:** `exp: multi-scenario type comparison`

---

### Task 4.2: 必撞场景可视化

**Files:**
- Modify: `generate_cr_scenarios.py`

- [ ] **Step 1: 将UPPAAL反例轨迹可视化**

```python
def visualize_counterexample(trace_data, output_gif):
    """
    将UPPAAL反例trace转换为CommonRoad动画
    trace_data: 从UPPAAL诊断输出解析的状态序列
    """
    # 为trace中每步创建DynamicObstacle
    # 创建动画GIF
    pass
```

- [ ] **Step 2: 生成5个典型必撞场景的GIF**

每种类型至少1个：
- 追尾必撞（rear-end）
- 切入必撞（cut-in）
- 急刹必撞（emergency brake）
- 多车包夹（encirclement）
- 路口交叉碰撞（intersection）

- [ ] **Commit:** `feat: visualize counterexample traces as GIFs`

---

### Task 4.3: 生成所有实验图表

**Files:**
- Create: `experiments/generate_all_figures.py`

生成论文需要的全部图表：
1. 参数敏感性柱状图
2. 场景类型对比柱状图
3. 搜索方法收敛曲线
4. 碰撞类型分布饼图
5. 必撞场景示例GIF × 5

- [ ] **Commit:** `feat: generate all experiment figures for thesis`

---

### Task 4.4: 论文大纲 + Ch3-5初稿

**Files:**
- Create: `thesis_outline.md`

对标师兄论文结构，写出你的论文大纲：
- Ch1: 绪论（自动驾驶安全、形式化验证、对抗性测试）
- Ch2: 背景知识（CommonRoad、UPPAAL、时间自动机、IDM模型）
- Ch3: 自动驾驶场景的UPPAAL建模（IDM ego + 行为化obstacle）
- Ch4: 基于模型检验的必撞性验证方法
- Ch5: 实验与分析
- Ch6: 总结与展望

- [ ] **Commit:** `docs: thesis outline and Ch3-5 draft`

---

### Sprint 4 组会汇报材料

- 完整实验结果汇总表（对标表5.8）
- 5个典型必撞场景GIF
- 参数敏感性完整分析
- 论文大纲 + Ch3-5初稿
- 下一步：填论文、答辩准备

---

## 附录A: 文件变更总览

| 操作 | 文件 | Sprint |
|------|------|--------|
| 修改 | `uppaal/template.xml` (Controller + IDM) | S1 |
| 修改 | `uppaal/template.xml` (Act_Move简化) | S1 |
| 修改 | `uppaal/template.xml` (Act_Turn简化) | S1 |
| 修改 | `uppaal/template.xml` (Obstacle重写) | S2 |
| 修改 | `parseCR/utils.py` (ST_OBEHAVIOR) | S2 |
| 修改 | `generate_uppaal_models.py` (行为参数) | S2 |
| 新增 | `uppaal/query_adversarial.q` | S2 |
| 新增 | `adversarial_search.py` | S3 |
| 新增 | `experiments/collect_results.py` | S3 |
| 新增 | `run_experiment1.py`, `run_experiment2.py` | S3-S4 |
| 修改 | `generate_cr_scenarios.py` (反例可视化) | S4 |
| 新增 | `experiments/generate_all_figures.py` | S4 |
| 新增 | `thesis_outline.md` | S4 |

## 附录B: UPPAAL GUI操作速查

```
1. 打开模型: File → Open System → 选择生成的.xml文件
2. 加载查询: Verifier → 粘贴 query_adversarial.q 内容
3. 运行验证: 选中查询 → 按 Ctrl+E 或点击 Verify
4. 查看反例: 如果验证失败 → Simulator → 查看Trace中的每步状态
5. 导出反例: Trace → Save Trace → 保存为文本文件
```
