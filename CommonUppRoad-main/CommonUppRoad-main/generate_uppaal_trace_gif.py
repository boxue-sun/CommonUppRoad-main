"""
generate_uppaal_trace_gif.py
从 UPPAAL 验证输出中提取碰撞轨迹，生成 CommonRoad GIF
流程：UPPAAL -t 1 → 解析轨迹 → sampling.log → CommonRoad 渲染
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import re
import subprocess
import numpy as np
import imageio

sys.path.insert(0, os.path.dirname(__file__))

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.state import CustomState, InitialState
from commonroad.scenario.trajectory import Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.geometry.obstacle_shapes.rect_obstacle_shape import RectObstacleShape

ROOT = os.path.dirname(__file__)
VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
ROAD_SCENARIO = os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml")


def run_uppaal_verification(model_path, query):
    """运行 UPPAAL 验证，返回完整输出"""
    # 写查询文件
    query_file = model_path.replace('.xml', '_query.q')
    with open(query_file, 'w') as f:
        f.write(query)

    result = subprocess.run(
        [VERIFYTA, "-t", "1", model_path, query_file],
        capture_output=True, text=True, timeout=300,
        encoding='utf-8', errors='replace'
    )
    return result.stdout + result.stderr


def parse_uppaal_trace(output):
    """从 UPPAAL 输出中提取轨迹状态"""
    states = []
    current_state = {}

    for line in output.split('\n'):
        line = line.strip()

        if line.startswith('State:'):
            if current_state:
                states.append(current_state)
            current_state = {}
            continue

        # 提取 key=value 对
        for match in re.finditer(r'(\w[\w.\[\]]*?)=([^ ]+)', line):
            key, value = match.group(1), match.group(2)
            current_state[key] = float(value)

    if current_state:
        states.append(current_state)

    return states


def states_to_sampling_log(states, output_path, interp_factor=10):
    """将状态列表转换为 sampling.log 格式，支持插值"""
    # sampling.log 格式: time obs_x obs_y obs_h obs_v obs_a ego_x ego_y ego_h ego_v ego_a
    lines = []

    # 提取有效状态（跳过初始全零）
    valid_states = []
    for i, state in enumerate(states):
        if state.get('cps_i_state.velocity', 0) == 0 and i < 2:
            continue
        valid_states.append(state)

    if len(valid_states) < 2:
        return []

    # 在每两个状态之间插值
    for i in range(len(valid_states) - 1):
        s1 = valid_states[i]
        s2 = valid_states[i + 1]

        for j in range(interp_factor):
            alpha = j / interp_factor

            # UPPAAL 整数编码 scale=10，需要除以 10 得到真实值
            SCALE = 10.0

            ego_x = (s1.get('cps_i_state.position.x', 0) + alpha * (s2.get('cps_i_state.position.x', 0) - s1.get('cps_i_state.position.x', 0))) / SCALE
            ego_v = (s1.get('cps_i_state.velocity', 0) + alpha * (s2.get('cps_i_state.velocity', 0) - s1.get('cps_i_state.velocity', 0))) / SCALE
            ego_a = (s1.get('cps_i_state.acceleration', 0) + alpha * (s2.get('cps_i_state.acceleration', 0) - s1.get('cps_i_state.acceleration', 0))) / SCALE
            ego_h = (s1.get('cps_i_state.orientation', 0) + alpha * (s2.get('cps_i_state.orientation', 0) - s1.get('cps_i_state.orientation', 0))) / SCALE

            obs_x = (s1.get('obs_i_state[0].position.x', 0) + alpha * (s2.get('obs_i_state[0].position.x', 0) - s1.get('obs_i_state[0].position.x', 0))) / SCALE
            obs_v = (s1.get('obs_i_state[0].velocity', 0) + alpha * (s2.get('obs_i_state[0].velocity', 0) - s1.get('obs_i_state[0].velocity', 0))) / SCALE
            obs_a = (s1.get('obs_i_state[0].acceleration', 0) + alpha * (s2.get('obs_i_state[0].acceleration', 0) - s1.get('obs_i_state[0].acceleration', 0))) / SCALE
            obs_h = (s1.get('obs_i_state[0].orientation', 0) + alpha * (s2.get('obs_i_state[0].orientation', 0) - s1.get('obs_i_state[0].orientation', 0))) / SCALE

            t = (i * interp_factor + j) * 0.01  # 每帧 0.01 秒
            line = f"{t:.2f} {obs_x:.2f} 0.0 {obs_h:.2f} {obs_v:.2f} {obs_a:.2f} {ego_x:.2f} 0.0 {ego_h:.2f} {ego_v:.2f} {ego_a:.2f}"
            lines.append(line)

    # 添加最后一个状态（除以 SCALE）
    SCALE = 10.0
    s = valid_states[-1]
    t = len(lines) * 0.01
    line = f"{t:.2f} {s.get('obs_i_state[0].position.x', 0)/SCALE:.2f} 0.0 {s.get('obs_i_state[0].orientation', 0)/SCALE:.2f} {s.get('obs_i_state[0].velocity', 0)/SCALE:.2f} {s.get('obs_i_state[0].acceleration', 0)/SCALE:.2f} {s.get('cps_i_state.position.x', 0)/SCALE:.2f} 0.0 {s.get('cps_i_state.orientation', 0)/SCALE:.2f} {s.get('cps_i_state.velocity', 0)/SCALE:.2f} {s.get('cps_i_state.acceleration', 0)/SCALE:.2f}"
    lines.append(line)

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    return lines


def make_dynamic_obstacle(obstacle_id, states, w=1.8, l=4.3):
    """从状态序列创建 CommonRoad DynamicObstacle"""
    t0, x0, y0, h0, v0, a0 = states[0]
    initial_state = CustomState(
        position=np.array([x0, y0]),
        velocity=v0,
        orientation=h0,
        time_step=0
    ).convert_state_to_state(InitialState())

    state_list = []
    for row in states[1:]:
        t, x, y, h, v, a = row
        state = CustomState(
            position=np.array([x, y]),
            velocity=v,
            orientation=h,
            acceleration=a,
            time_step=max(1, int(round(t / 0.01)))
        )
        state_list.append(state)

    if len(state_list) == 0:
        return None

    trajectory = Trajectory(1, state_list)
    shape = RectObstacleShape(width=w, length=l)
    prediction = TrajectoryPrediction(trajectory, shape)
    return DynamicObstacle(obstacle_id, ObstacleType.CAR, shape, initial_state, prediction)


def parse_log_lines(log_lines):
    """解析 log 行为 obs 和 ego 状态"""
    obs_states, ego_states = [], []
    for line in log_lines:
        parts = list(map(float, line.split()))
        t, ox, oy, oh, ov, oa, ex, ey, eh, ev, ea = parts
        obs_states.append((t, ox, oy, oh, ov, oa))
        ego_states.append((t, ex, ey, eh, ev, ea))
    return obs_states, ego_states


def render_commonroad_gif(scenario_path, obs_states, ego_states, collision_step, output_path):
    """用 CommonRoad 原生渲染器生成 GIF"""
    scenario, pps = CommonRoadFileReader(scenario_path).open()

    for orig_obs in list(scenario.dynamic_obstacles):
        scenario.remove_obstacle(orig_obs)

    obs = make_dynamic_obstacle(100, obs_states, w=1.8, l=4.3)
    ego = make_dynamic_obstacle(200, ego_states, w=1.0, l=4.5)

    if obs:
        scenario.add_objects(obs)
    if ego:
        scenario.add_objects(ego)

    figs_dir = os.path.join(os.path.dirname(output_path), "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    n_frames = min(len(ego_states), 200)
    if collision_step >= 0:
        n_frames = min(n_frames, collision_step * 10 + 15)

    for t in range(n_frames):
        fig = plt.figure(figsize=(20, 6))
        rnd = MPRenderer()
        rnd.draw_params.time_begin = t
        rnd.draw_params.time_end = t + 1
        rnd.draw_params.dynamic_obstacle.draw_icon = True
        rnd.draw_params.dynamic_obstacle.draw_shape = True

        scenario.draw(rnd)
        pps.draw(rnd)
        rnd.render()

        if collision_step >= 0 and t >= collision_step:
            ax = plt.gca()
            ex, ey = ego_states[t][1], ego_states[t][2]
            ax.annotate('COLLISION!', (ex, ey + 8), fontsize=20, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red'),
                        zorder=20)

        filepath = os.path.join(figs_dir, f"frame_{t:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    with imageio.get_writer(output_path, mode='I', duration=0.08) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))

    for fn in filenames:
        os.remove(fn)


def main():
    # 测试几个碰撞场景
    test_cases = [
        {"distance": 10, "obs_speed": 0, "ego_speed": 25},
        {"distance": 15, "obs_speed": 0, "ego_speed": 30},
        {"distance": 8, "obs_speed": 0, "ego_speed": 25},
    ]

    output_dir = os.path.join(ROOT, "experiments", "animation", "uppaal_trace")
    os.makedirs(output_dir, exist_ok=True)

    for case in test_cases:
        dist = case["distance"]
        obs_spd = case["obs_speed"]
        ego_spd = case["ego_speed"]

        print(f"\n{'='*60}")
        print(f"Scenario: dist={dist}m, obs={obs_spd}m/s, ego={ego_spd}m/s")

        # 1. 生成 UPPAAL 模型
        from experiment_close_range import generate_model
        model_path = os.path.join(output_dir, f"model_dist{dist}_obs{obs_spd}_ego{ego_spd}.xml")
        generate_model(dist, obs_spd, ego_spd, model_path)

        # 2. 运行 UPPAAL 验证（带轨迹输出）
        print("  Running UPPAAL verification...")
        output = run_uppaal_verification(model_path, "E<> cps_i_state.detection.collide")

        if "Formula is satisfied" in output:
            print("  Collision FOUND!")
        else:
            print("  No collision found, skipping...")
            continue

        # 3. 解析轨迹
        print("  Parsing trace...")
        states = parse_uppaal_trace(output)
        print(f"  Found {len(states)} states in trace")

        # 4. 转换为 sampling.log 格式
        log_path = os.path.join(output_dir, f"trace_dist{dist}_obs{obs_spd}_ego{ego_spd}.log")
        log_lines = states_to_sampling_log(states, log_path)

        # 5. 生成 GIF
        print("  Rendering GIF...")
        obs_states, ego_states = parse_log_lines(log_lines)

        # 找碰撞步
        collision_step = -1
        for i, state in enumerate(states):
            if state.get('cps_i_state.detection.collide', 0) == 1:
                collision_step = i
                break

        gif_path = os.path.join(output_dir, f"uppaal_collision_dist{dist}_obs{obs_spd}_ego{ego_spd}.gif")
        render_commonroad_gif(ROAD_SCENARIO, obs_states, ego_states, collision_step, gif_path)
        print(f"  GIF saved: {os.path.basename(gif_path)}")

    print(f"\n{'='*60}")
    print(f"Done! GIFs saved to: {output_dir}")


if __name__ == '__main__':
    main()
