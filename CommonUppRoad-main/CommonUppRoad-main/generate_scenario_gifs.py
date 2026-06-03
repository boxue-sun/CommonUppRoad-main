"""
generate_scenario_gifs.py
生成 CommonRoad 原生风格的场景 GIF 动画
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import imageio

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer

ROOT = os.path.dirname(__file__)
ANIM_DIR = os.path.join(ROOT, "experiments", "animation")
os.makedirs(ANIM_DIR, exist_ok=True)


def render_scenario_gif(scenario_path, output_path, time_steps=30):
    """渲染原始 CommonRoad 场景为 GIF（不修改）"""
    scenario, pps = CommonRoadFileReader(scenario_path).open()

    figs_dir = os.path.join(ANIM_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    for t in range(time_steps):
        plt.figure(figsize=(20, 6))
        rnd = MPRenderer()
        rnd.draw_params.time_begin = t
        rnd.draw_params.time_end = t + 1
        rnd.draw_params.dynamic_obstacle.draw_icon = True
        rnd.draw_params.dynamic_obstacle.draw_shape = True

        scenario.draw(rnd)
        pps.draw(rnd)
        rnd.render()

        filepath = os.path.join(figs_dir, f"frame_{t:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    with imageio.get_writer(output_path, mode='I', duration=0.15) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))

    for fn in filenames:
        os.remove(fn)
    print(f"GIF saved: {output_path}")


def idm_acceleration(v_ego, v_lead, gap, v0=30.0, T=1.5, s0=2.0, a_max=2.0, b_comf=1.5, delta=4.0):
    """IDM 加速度计算"""
    s_star = s0 + v_ego * T + v_ego * (v_ego - v_lead) / (2.0 * np.sqrt(a_max * b_comf))
    if gap < 0.001:
        gap = 0.001
    acc = a_max * (1.0 - (v_ego / v0) ** delta - (s_star / gap) ** 2)
    return acc


def simulate_collision_scenario():
    """
    模拟 test_adversarial 碰撞场景：
    - Ego: pos=(15,0), vel=22 m/s, IDM 控制
    - Obs0: pos=(18,0), vel=1 m/s, 匀速直行
    """
    dt = 0.1
    n_steps = 40  # 4秒

    ego_x, ego_y, ego_v, ego_h = 0.0, 0.0, 22.0, 0.0
    obs_x, obs_y, obs_v, obs_h = 10.0, 0.0, 1.0, 0.0

    ego_states = []
    obs_states = []
    collision_step = -1

    for t in range(n_steps):
        ego_states.append((t * dt, ego_x, ego_y, ego_h, ego_v))
        obs_states.append((t * dt, obs_x, obs_y, obs_h, obs_v))

        dist = np.sqrt((ego_x - obs_x) ** 2 + (ego_y - obs_y) ** 2)
        if dist < 4.0 and collision_step < 0:
            collision_step = t

        if collision_step >= 0:
            continue  # 碰撞后继续记录几帧

        gap = max(0.1, dist)
        ego_acc = idm_acceleration(ego_v, obs_v, gap)
        ego_acc = max(-5.0, min(2.0, ego_acc))

        ego_v = max(0.0, ego_v + ego_acc * dt)
        ego_x += ego_v * dt
        obs_x += obs_v * dt

    print(f"Collision at step {collision_step}, time = {collision_step * dt:.1f}s")
    return ego_states, obs_states, collision_step


def render_collision_gif(scenario_path, ego_states, obs_states, collision_step, output_path):
    """渲染碰撞场景：用 CommonRoad 画道路，用 matplotlib 画车辆"""
    scenario, pps = CommonRoadFileReader(scenario_path).open()

    figs_dir = os.path.join(ANIM_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []
    # 只渲染到碰撞后5帧
    n_frames = min(len(ego_states), collision_step + 6)

    for i in range(n_frames):
        t, ex, ey, eh, ev = ego_states[i]
        _, ox, oy, oh, ov = obs_states[i]

        plt.figure(figsize=(20, 6))
        rnd = MPRenderer()
        rnd.draw_params.time_begin = 0
        rnd.draw_params.time_end = 1
        scenario.draw(rnd)
        pps.draw(rnd)
        rnd.render()

        # 用 matplotlib 叠加画车辆
        ax = plt.gca()
        # Ego (blue)
        ego_rect = patches.FancyBboxPatch((ex - 2.25, ey - 0.5), 4.5, 1.0,
                                           boxstyle="round,pad=0.05",
                                           facecolor='#2196F3', edgecolor='white', linewidth=2, zorder=10)
        ax.add_patch(ego_rect)
        ax.annotate(f'Ego {ev:.0f}m/s', (ex, ey + 2), fontsize=10, ha='center',
                    color='#2196F3', fontweight='bold', zorder=11)

        # Obs0 (red)
        obs_rect = patches.FancyBboxPatch((ox - 2.25, oy - 0.5), 4.5, 1.0,
                                           boxstyle="round,pad=0.05",
                                           facecolor='#F44336', edgecolor='white', linewidth=2, zorder=10)
        ax.add_patch(obs_rect)
        ax.annotate(f'Obs0 {ov:.0f}m/s', (ox, oy + 2), fontsize=10, ha='center',
                    color='#F44336', fontweight='bold', zorder=11)

        # 碰撞标注
        if i >= collision_step:
            mid_x = (ex + ox) / 2
            mid_y = (ey + oy) / 2
            ax.annotate('COLLISION!', (mid_x, mid_y + 4), fontsize=18, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red'),
                        zorder=12)

        # 缩放到碰撞区域附近
        ax.set_xlim(-20, 50)
        ax.set_ylim(-15, 15)

        filepath = os.path.join(figs_dir, f"collision_{i:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    with imageio.get_writer(output_path, mode='I', duration=0.2) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))

    for fn in filenames:
        os.remove(fn)
    print(f"GIF saved: {output_path}")


# ============================================================
# 1. 渲染原始 ZAM_Tutorial 场景
# ============================================================
print("=" * 50)
print("1. Rendering ZAM_Tutorial original scenario...")
render_scenario_gif(
    os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml"),
    os.path.join(ANIM_DIR, "ZAM_Tutorial_original.gif"),
    time_steps=30
)

# ============================================================
# 2. 渲染原始 DEU_Ffb 场景
# ============================================================
print("=" * 50)
print("2. Rendering DEU_Ffb original scenario...")
render_scenario_gif(
    os.path.join(ROOT, "scenarios", "DEU_Ffb-1_3_T-1.xml"),
    os.path.join(ANIM_DIR, "DEU_Ffb_original.gif"),
    time_steps=30
)

# ============================================================
# 3. 渲染 test_adversarial 碰撞场景
# ============================================================
print("=" * 50)
print("3. Simulating test_adversarial collision...")
ego_states, obs_states, collision_step = simulate_collision_scenario()

print("   Rendering GIF...")
render_collision_gif(
    os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml"),
    ego_states, obs_states, collision_step,
    os.path.join(ANIM_DIR, "test_adversarial_collision.gif")
)

print("=" * 50)
print("Done! All GIFs saved to:", ANIM_DIR)
