# UPPAAL 实操教程 — 从打开模型到查看碰撞轨迹

> 操作环境：Windows + UPPAAL 5.x GUI
> 推荐模型：`uppaal/models/ZAM_Tutorial-1_2_T-1_generated_lanelet.xml`（最简单，适合学习）

---

## 第一步：打开模型

1. 打开 UPPAAL GUI
2. 菜单栏 → **File** → **Open System...**
3. 找到项目目录下的文件：
   ```
   CommonUppRoad-main/uppaal/models/ZAM_Tutorial-1_2_T-1_generated_lanelet.xml
   ```
4. 打开后会看到多个标签页，这是正常的

---

## 第二步：认识模型结构（看什么）

打开后你会看到几个标签页，每个标签页对应一个**自动机模板（Template）**：

### 标签页一览

| 标签名 | 是什么 | 干什么的 |
|--------|--------|----------|
| **Controller** | Ego车的"大脑" | IDM决策：找前车→算加速度→下达指令 |
| **Act_Move** | 执行器-纵向 | 接收Controller的accRate，做限幅 |
| **Act_Turn** | 执行器-横向 | 车道保持，yawRate=0 |
| **Timer** | 时钟自动机 | 控制节奏：sense→decide→perform→end 循环 |
| **Dynamics** | 连续演化 | ODE积分：位置、速度的连续变化 |
| **Obstacle** | 障碍物自动机 | 行为自动机：每4步非确定性选行为 |
| **rewardMachine** | 奖励计算 | 记录安全、舒适、进度指标 |

### 重点看这三个

**① Controller（看IDM怎么决策）**
- 双击打开 Controller 标签
- 看 declaration 区域，找到 `computeIDM` 函数
- 这就是ego车的"大脑"：输入当前速度v、前车速度vLead、与前车距离gap → 输出加速度

**② Obstacle（看障碍物怎么选行为）**
- 双击打开 Obstacle 标签
- 看 declaration 区域，找到 `chooseLonAction` 和 `chooseLatAction`
- 注意：函数里 **没有给 action 赋值** → 这就是UPPAAL穷举的关键

**③ Dynamics（看连续演化）**
- 双击打开 Dynamics 标签
- 看 S0 状态的 invariant：
  ```
  cps_dynamic.x' == cos(cps_dynamic.orientation) * cps_dynamic.velocity
  cps_dynamic.y' == sin(cps_dynamic.orientation) * cps_dynamic.velocity
  cps_dynamic.velocity' == cps_dynamic.acceleration
  ```
- 这就是物理运动方程：x方向速度 = 总速度×cos(朝向)，y方向同理

---

## 第三步：查看系统组成（看 System 标签）

1. 点击最右边的 **system** 标签（或菜单 Edit → System Declaration）
2. 你会看到类似这样的声明：
   ```
   system timer, obs0, move, turn, controller, dynamics, rewardMachine;
   ```
3. 这行意思是：系统由这些自动机组成
   - `timer`：1个时钟
   - `obs0`：1个障碍物（如果场景有多个动态障碍物，会有 obs0, obs1, obs2...）
   - `controller`：1个ego控制器
   - `move, turn`：2个执行器
   - `dynamics`：1个连续演化
   - `rewardMachine`：1个奖励机

---

## 第四步：运行仿真（看ego车跑起来）

### 4.1 进入仿真模式

1. 菜单栏 → **Simulator** 标签（在窗口顶部）
2. 或者按快捷键 **Ctrl+T** 切换到 Simulator

### 4.2 设置仿真

1. 在 Simulator 中，点击上方的 **Options** 按钮
2. 设置仿真时间：`<= MAXTIME`（MAXTIME在模型中定义为10，即10秒）
3. 点击 **Run** 或按 **Ctrl+R** 开始仿真

### 4.3 观察仿真过程

仿真运行后，你会看到：
- 左侧显示**每个自动机的当前状态**（比如 Controller 在 Acting 状态，Obstacle 在 S0 状态）
- 中间显示**变量的当前值**，可以观察：
  - `cps_i_state.position.x` / `cps_i_state.position.y` → ego位置
  - `cps_i_state.velocity` → ego速度
  - `cps_i_state.detection.collide` → 是否碰撞（true/false）
  - `obs_i_state[0].position.x` → 障碍物位置

### 4.4 手动单步执行

- 点击 **Delay** 按钮可以让时间前进一小步
- 点击某个 transition 可以手动触发该转移
- 观察每一步变量的变化

---

## 第五步：运行验证（找碰撞/安全）

### 5.1 切换到验证器

1. 点击窗口顶部的 **Verifier** 标签
2. 这是验证查询的输入界面

### 5.2 输入查询并验证

在查询输入框中，**逐个输入**以下查询，每输入一个点 **Verify**（或按 Ctrl+E）：

**查询1：是否存在碰撞路径？**
```
E<> cps_i_state.detection.collide
```
- 结果 **TRUE** = 存在至少一条路径导致碰撞
- 结果 **FALSE** = 无论如何都不会碰撞（非常安全）

**查询2：所有路径都安全吗？（最关键！）**
```
A[] !cps_i_state.detection.collide
```
- 结果 **TRUE** = 所有可能的障碍物行为下，ego都不会撞
- 结果 **FALSE** = **发现必撞场景！** → 继续看第六步

**查询3：能安全到达目标吗？**
```
E<> cps_i_state.detection.reach && !cps_i_state.detection.collide
```
- 结果 **TRUE** = 存在一条安全到达目标的路径

**查询4：ego是否出界？**
```
E<> cps_i_state.detection.outside
```

### 5.3 理解验证结果

当你验证 `A[] !cps_i_state.detection.collide` 并得到 **FALSE** 时：

```
A[] !cps_i_state.detection.collide  →  结果: FALSE

含义：不是所有路径都安全 → 存在某些障碍物行为组合会导致碰撞
      → 这个参数组合是一个"必撞场景"
```

UPPAAL 会自动在 Simulator 中生成一条**反例轨迹（Counter-example）**。

---

## 第六步：查看反例轨迹（碰撞是怎么发生的）

### 6.1 自动跳转到反例

当验证 `A[] !collide` 得到 FALSE 时：
1. UPPAAL 会自动切换到 **Simulator** 标签
2. 加载一条导致碰撞的**具体轨迹**
3. 这条轨迹就是"反例"——展示碰撞是如何一步步发生的

### 6.2 逐步回放反例

在 Simulator 中：

1. 看到轨迹已经加载好了，变量值显示的是碰撞路径上的每一步
2. 点击 **Back** / **Forward** 按钮逐步查看：
   - `cps_i_state.position.x/y` → ego在哪
   - `obs_i_state[0].position.x/y` → 障碍物在哪
   - `cps_i_state.velocity` → ego速度多少
   - `cps_i_state.detection.collide` → 什么时候变成 true（碰撞发生）

3. **重点关注碰撞前几步**：
   - 障碍物选了什么行为？（加速？急刹？换道？）
   - ego的IDM为什么没能避免碰撞？

### 6.3 观察障碍物的非确定性选择

在反例轨迹中，看 Obstacle 自动机的状态：
- 每4步会进入 `decisionMaking()` 选择一次行为
- 观察 `obs_i_state[0].acceleration` 的变化：
  - 变成负值 = 障碍物急刹了
  - 保持0 = 匀速
  - 变成正值 = 加速
- 观察 `obs_i_state[0].yawRate` 的变化：
  - -0.3 = 左换道
  - 0 = 保持
  - 0.3 = 右换道

### 6.4 导出反例轨迹

1. 在 Simulator 中，菜单 **Trace** → **Save Trace...**
2. 保存为文本文件，比如 `counterexample.txt`
3. 这个文件包含每一步所有变量的值
4. 后续可以用 `generate_cr_scenarios.py` 转成 CommonRoad 可视化

---

## 第七步：用脚本可视化反例（可选，需要Python环境）

如果你想把UPPAAL的反例轨迹变成GIF动画：

### 7.1 导出采样日志

在 UPPAAL 中运行仿真查询：
```
simulate [<=MAXTIME;1] { cps_dynamic.x, cps_dynamic.y, cps_dynamic.orientation, cps_dynamic.velocity, cps_dynamic.acceleration }
```

仿真结束后，在 UPPAAL 的输出窗口复制采样数据，保存为 `uppaal/sampling.log`。

### 7.2 运行可视化脚本

```bash
cd CommonUppRoad-main
python generate_cr_scenarios.py
```

脚本会：
1. 读取 sampling.log
2. 把每步状态转成 CommonRoad 的 DynamicObstacle
3. 渲染成 GIF 动画，保存在 `experiments/animation/` 目录

---

## 附：推荐练习顺序

### 练习1：用简单模型跑仿真

1. 打开 `ZAM_Tutorial-1_2_T-1_generated_lanelet.xml`
2. 切到 Simulator → 运行仿真
3. 观察ego车位置变化、速度变化
4. 观察 `cps_i_state.detection.collide` 始终为 false → 这个场景是安全的

### 练习2：验证安全性

1. 切到 Verifier
2. 输入 `A[] !cps_i_state.detection.collide` → 验证
3. 如果 TRUE → 这个场景参数下没有碰撞
4. 如果 FALSE → 跳到练习3

### 练习3：查看反例

1. 验证 FALSE 后自动跳到 Simulator
2. 逐步回放，找到碰撞那一刻
3. 记录：碰撞时ego在哪、障碍物在哪、各自速度多少
4. 观察障碍物的行为选择（acceleration 和 yawRate 的变化）

### 练习4：换个场景试试

1. 打开 `DEU_Ffb-1_3_T-1_generated_lanelet.xml`（高速公路场景）
2. 重复练习2和练习3
3. 高速场景更容易出现碰撞

### 练习5：修改参数重新生成（进阶）

1. 修改 `generate_uppaal_models.py` 中的 `MAXT`（比如改成20）
2. 运行 `python generate_uppaal_models.py`
3. 重新打开生成的模型，验证结果可能不同（时间窗口更大，碰撞更容易被发现）

---

## 附：UPPAAL GUI 快捷键

| 操作 | 快捷键 |
|------|--------|
| 打开文件 | Ctrl+O |
| 保存 | Ctrl+S |
| 切换到 Simulator | Ctrl+T |
| 运行仿真 | Ctrl+R |
| 验证查询 | Ctrl+E |
| 单步前进 | 点击 Forward 或按 Enter |
| 单步后退 | 点击 Back |

---

## 附：常见问题

**Q: 打开模型后报错 "undeclared identifier" 怎么办？**
A: 说明模型生成不完整。重新运行 `python generate_uppaal_models.py` 生成模型。

**Q: 验证特别慢怎么办？**
A: 正常。UPPAAL在穷举所有行为组合，状态空间可能很大。可以先用小模型（ZAM_Tutorial）测试。如果超过5分钟没结果，可以点 Cancel 中止。

**Q: 怎么看障碍物具体选了什么行为？**
A: 在 Simulator 中观察 `obs_i_state[0].acceleration`（纵向：负=刹车，0=匀速，正=加速）和 `obs_i_state[0].yawRate`（横向：负=左转，0=保持，正=右转）。

**Q: 我想看多个障碍物的轨迹怎么办？**
A: 如果场景有多个动态障碍物，系统中会有 obs0, obs1, obs2... 分别观察 `obs_i_state[0]`, `obs_i_state[1]`, `obs_i_state[2]` 的位置和行为。
