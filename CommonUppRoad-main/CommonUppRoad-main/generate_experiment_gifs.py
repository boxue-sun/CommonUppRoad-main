"""
generate_experiment_gifs.py
生成碰撞/不碰撞轨迹的可视化 GIF
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import imageio

ANIM_DIR = os.path.join(os.path.dirname(__file__), "experiments", "animation")
os.makedirs(ANIM_DIR, exist_ok=True)


def idm_acceleration(v_ego, v_lead, gap):
    """IDM 加速度计算，限幅 [-10, 2]"""
    v0 = 30.0
    T = 1.5
    s0 = 2.0
    a_max = 2.0
    b_comf = 1.5
    delta = 4

    s_star = s0 + v_ego * T + v_ego * (v_ego - v_lead) / (2.0 * np.sqrt(a_max * b_comf))
    if gap < 0.001:
        gap = 0.001
    acc = a_max * (1.0 - (v_ego / v0) ** delta - (s_star / gap) ** 2)
    if acc > 2.0:
        acc = 2.0
    if acc < -10.0:
        acc = -10.0
    return acc


def simulate(ego_x0, ego_v0, obs_x0, obs_v0, dt=0.1, max_steps=80):
    """模拟 ego（IDM 控制）和障碍物（匀速）的运动"""
    ego_x, ego_v = ego_x0, ego_v0
    obs_x, obs_v = obs_x0, obs_v0

    ego轨迹 = [(ego_x, ego_v)]
    obs轨迹 = [(obs_x, obs_v)]
    collision_step = -1

    for t in range(max_steps):
        gap = max(0.01, obs_x - ego_x)
        acc = idm_acceleration(ego_v, obs_v, gap)

        ego_v = max(0.0, ego_v + acc * dt)
        ego_x = ego_x + ego_v * dt
        obs_x = obs_x + obs_v * dt

        ego轨迹.append((ego_x, ego_v))
        obs轨迹.append((obs_x, obs_v))

        # 碰撞检测：两车中心距离 < 4 米
        if abs(ego_x - obs_x) < 4.0 and collision_step < 0:
            collision_step = t + 1

    return ego轨迹, obs轨迹, collision_step


def render_gif(ego轨迹, obs轨迹, collision_step, title, output_path, dt=0.1):
    """渲染 GIF 动画"""
    figs_dir = os.path.join(ANIM_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    n_frames = len(ego轨迹)
    if collision_step >= 0:
        n_frames = min(n_frames, collision_step + 8)  # 碰撞后多画几帧

    for i in range(n_frames):
        ex, ev = ego轨迹[i]
        ox, ov = obs轨迹[i]

        fig, ax = plt.subplots(1, 1, figsize=(16, 4))

        # 画道路
        road_left = min(ex, ox) - 15
        road_right = max(ex, ox) + 25
        ax.fill_between([road_left, road_right], -3.5, 3.5, color='#e8e8e8', alpha=0.5)
        ax.fill_between([road_left, road_right], -0.1, 0.1, color='white', alpha=0.8)
        ax.plot([road_left, road_right], [1.75, 1.75], '--', color='gray', linewidth=0.5, alpha=0.5)
        ax.plot([road_left, road_right], [-1.75, -1.75], '--', color='gray', linewidth=0.5, alpha=0.5)

        # 画 ego（蓝色）
        ego_rect = patches.FancyBboxPatch((ex - 2.25, -0.5), 4.5, 1.0,
                                           boxstyle="round,pad=0.05",
                                           facecolor='#2196F3', edgecolor='white', linewidth=2, zorder=10)
        ax.add_patch(ego_rect)
        ax.annotate(f'Ego\n{ev:.0f} m/s', (ex, 1.8), fontsize=9, ha='center',
                    color='#1565C0', fontweight='bold', zorder=11)

        # 画障碍物（红色）
        obs_rect = patches.FancyBboxPatch((ox - 2.15, -0.5), 4.3, 1.0,
                                           boxstyle="round,pad=0.05",
                                           facecolor='#F44336', edgecolor='white', linewidth=2, zorder=10)
        ax.add_patch(obs_rect)
        ax.annotate(f'Obs\n{ov:.0f} m/s', (ox, -2.0), fontsize=9, ha='center',
                    color='#C62828', fontweight='bold', zorder=11)

        # 碰撞标注
        if collision_step >= 0 and i >= collision_step:
            mid_x = (ex + ox) / 2
            ax.annotate('COLLISION!', (mid_x, 3.5), fontsize=16, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red'),
                        zorder=12)

        # 距离标注
        dist = abs(ex - ox)
        mid_x = (ex + ox) / 2
        ax.annotate(f'{dist:.1f}m', (mid_x, -3.0), fontsize=10, ha='center', color='#333')

        # 时间标注
        t = i * dt
        ax.set_title(f'{title}  |  t = {t:.1f}s', fontsize=13, fontweight='bold')

        ax.set_xlim(road_left, road_right)
        ax.set_ylim(-4, 5)
        ax.set_aspect('equal')
        ax.set_xlabel('X (m)', fontsize=10)

        filepath = os.path.join(figs_dir, f"frame_{i:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    duration = 0.3 if collision_step < 0 else 0.25
    with imageio.get_writer(output_path, mode='I', duration=duration) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))

    for fn in filenames:
        os.remove(fn)

    tag = f"COLLISION at t={collision_step * dt:.1f}s" if collision_step >= 0 else "SAFE"
    print(f"  {tag} -> {output_path}")


def main():
    os.makedirs(ANIM_DIR, exist_ok=True)

    # 定义场景：(描述, ego初始位置, ego速度, obs初始位置, obs速度)
    scenarios = [
        # === 碰撞场景 ===
        ("Collision: 5m, ego=30m/s, obs=0m/s",
         0, 30, 5, 0, True),

        ("Collision: 10m, ego=30m/s, obs=1m/s",
         0, 30, 10, 1, True),

        ("Collision: 15m, ego=25m/s, obs=0m/s",
         0, 25, 15, 0, True),

        ("Collision: 20m, ego=30m/s, obs=3m/s",
         0, 30, 20, 3, True),

        # === 安全场景 ===
        ("Safe: 20m, ego=10m/s, obs=5m/s",
         0, 10, 20, 5, False),

        ("Safe: 30m, ego=15m/s, obs=10m/s",
         0, 15, 30, 10, False),

        ("Safe: 50m, ego=20m/s, obs=10m/s",
         0, 20, 50, 10, False),
    ]

    print("Generating experiment GIFs...")
    print("=" * 60)

    for desc, ego_x0, ego_v0, obs_x0, obs_v0, is_collision in scenarios:
        ego轨迹, obs轨迹, collision_step = simulate(ego_x0, ego_v0, obs_x0, obs_v0)

        prefix = "collision" if collision_step >= 0 else "safe"
        idx = sum(1 for s in scenarios if (s[5] == is_collision)) if is_collision else 0
        filename = f"exp_{prefix}_{desc.split(':')[0].strip().lower().replace(' ', '_')}_{abs(obs_x0 - ego_x0):.0f}m_{ego_v0:.0f}mps.gif"
        filename = filename.replace(":", "").replace(",", "")
        output_path = os.path.join(ANIM_DIR, filename)

        print(f"[{desc}]")
        render_gif(ego轨迹, obs轨迹, collision_step, desc, output_path)

    print("=" * 60)
    print(f"Done! GIFs saved to: {ANIM_DIR}")


if __name__ == '__main__':
    main()
