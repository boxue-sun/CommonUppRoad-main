// ==========================================
// 必撞场景验证查询集 — Adversarial Verification Queries
// CommonUppRoad: 自动驾驶对抗性测试
// ==========================================

// Q1: 是否存在一条路径导致碰撞？
// TRUE = 存在碰撞可能（找到潜在必撞场景）
E<> cps_i_state.detection.collide

// Q2: 在所有可能的障碍物行为下，ego总是安全的吗？
// FALSE = 存在"必撞"场景（无论ego怎么做都会撞，或存在某个障碍物行为序列导致碰撞）
A[] !cps_i_state.detection.collide

// Q3: ego是否能安全到达目标？
// TRUE = 存在一条路径使ego安全到达
E<> cps_i_state.detection.reach && !cps_i_state.detection.collide

// Q4: 在所有障碍物行为下，ego总能到达目标且不碰撞？
// FALSE = 存在某个障碍物行为阻止ego安全到达
A[] (!cps_i_state.detection.collide || cps_i_state.detection.reach)

// Q5: 碰撞发生的概率上界（SMC: 统计模型检验）
// 需要 UPPAAL SMC 支持
Pr[<=MAXTIME](<> cps_i_state.detection.collide)

// Q6: 高相对速度碰撞的存在性
// TRUE = 存在高速碰撞场景（更危险）
E<> cps_i_state.detection.collide && cps_i_state.velocity >= d2i(10.0)

// Q7: 存在偏离道路的情况？（障碍物行为迫使ego离开道路）
E<> cps_i_state.detection.outside

// Q8: 碰撞前ego车速观察（用于分级碰撞严重性）
E<> cps_i_state.detection.collide && cps_i_state.velocity >= d2i(5.0)

// ==========================================
// 使用方法:
// 1. 在 UPPAAL GUI 中打开生成的 *_generated_lanelet.xml 模型
// 2. 在 Verifier 标签中粘贴以上查询
// 3. 重点观察 Q2 结果: A[] !collide = FALSE 表示发现必撞场景
// 4. 在 Simulator 中查看反例 Trace, 导出为 .txt 用于可视化
// ==========================================
