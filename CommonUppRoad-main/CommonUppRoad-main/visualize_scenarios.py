"""
visualize_scenarios.py
生成场景可视化图片，展示道路布局和车辆位置
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "experiments", "scenario_figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def draw_scenario(title, ego_pos, ego_vel, ego_heading, obs_list, road_xlim, road_ylim, filename):
    """
    画一个场景的俯视图
    ego_pos: (x, y)
    obs_list: [(x, y, vel, label), ...]
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 5))

    # 画道路（3条车道，每条宽7m）
    lane_width = 7
    for i in range(3):
        y_bottom = -lane_width + i * lane_width
        y_top = y_bottom + lane_width
        color = '#f0f0f0' if i % 2 == 0 else '#e8e8e8'
        ax.fill_between(road_xlim, y_bottom, y_top, color=color, alpha=0.5)

    # 画车道线
    for i in range(4):
        y = -lane_width + i * lane_width
        style = '--' if i == 1 or i == 2 else '-'
        ax.plot(road_xlim, [y, y], style, color='gray', linewidth=0.8, alpha=0.6)

    # 画ego车
    ex, ey = ego_pos
    ego_rect = patches.FancyBboxPatch((ex - 2.25, ey - 0.5), 4.5, 1.0,
                                       boxstyle="round,pad=0.05",
                                       facecolor='#2196F3', edgecolor='white', linewidth=1.5, zorder=5)
    ax.add_patch(ego_rect)
    ax.annotate(f'Ego\n{ego_vel:.0f} m/s', (ex, ey), fontsize=8, ha='center', va='center',
                color='white', fontweight='bold', zorder=6)

    # 画障碍物
    colors = ['#F44336', '#FF9800', '#9C27B0', '#4CAF50', '#795548']
    for i, (ox, oy, ovel, label) in enumerate(obs_list):
        c = colors[i % len(colors)]
        obs_rect = patches.FancyBboxPatch((ox - 2.25, oy - 0.5), 4.5, 1.0,
                                           boxstyle="round,pad=0.05",
                                           facecolor=c, edgecolor='white', linewidth=1.5, zorder=5)
        ax.add_patch(obs_rect)
        ax.annotate(f'{label}\n{ovel:.0f} m/s', (ox, oy), fontsize=7, ha='center', va='center',
                    color='white', fontweight='bold', zorder=6)

    # 画运动方向箭头
    arrow_len = 5
    dx = arrow_len * np.cos(ego_heading)
    dy = arrow_len * np.sin(ego_heading)
    ax.annotate('', xy=(ex + dx, ey + dy), xytext=(ex, ey),
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5), zorder=4)

    ax.set_xlim(road_xlim)
    ax.set_ylim(road_ylim)
    ax.set_aspect('equal')
    ax.set_xlabel('X (m)', fontsize=10)
    ax.set_ylabel('Y (m)', fontsize=10)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filepath}")
    return filepath


# === 场景1: ZAM_Tutorial (原始场景，不会碰撞) ===
draw_scenario(
    title="ZAM_Tutorial - Original (A[] !collide = TRUE, SAFE)",
    ego_pos=(15, 0),
    ego_vel=22,
    ego_heading=0,
    obs_list=[
        (2.25, 3.5, 23, 'Obs0'),
        (50.0, 0.0, 22, 'Obs1'),
    ],
    road_xlim=(-10, 80),
    road_ylim=(-10, 15),
    filename="01_zam_tutorial_original.png"
)

# === 场景2: DEU_Ffb (原始高速场景，不会碰撞) ===
draw_scenario(
    title="DEU_Ffb - Highway (A[] !collide = TRUE, SAFE)",
    ego_pos=(0, 0),
    ego_vel=12,
    ego_heading=0,
    obs_list=[
        (25.9, -0.3, 10, 'Obs0'),
        (71.0, -14.1, 12, 'Obs1'),
        (66.3, 24.9, 10, 'Obs2'),
        (65.7, 45.0, 9, 'Obs3'),
    ],
    road_xlim=(-15, 100),
    road_ylim=(-20, 55),
    filename="02_deu_ffb_original.png"
)

# === 场景3: 测试碰撞场景 (必撞) ===
draw_scenario(
    title="test_adversarial - Dangerous (A[] !collide = FALSE, COLLISION!)",
    ego_pos=(15, 0),
    ego_vel=22,
    ego_heading=0,
    obs_list=[
        (18.0, 0.0, 1, 'Obs0\n(3m ahead!)'),
    ],
    road_xlim=(-10, 50),
    road_ylim=(-10, 15),
    filename="03_test_adversarial_collision.png"
)

# === 场景4: 原理分析图 ===
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 左图：安全场景
ax = axes[0]
ax.fill_between([-10, 80], -7, 0, color='#f0f0f0', alpha=0.5)
ax.fill_between([-10, 80], 0, 7, color='#e8e8e8', alpha=0.5)
ax.fill_between([-10, 80], 7, 14, color='#f0f0f0', alpha=0.5)
ax.plot([-10, 80], [0, 0], '--', color='gray', alpha=0.5)
ax.plot([-10, 80], [7, 7], '--', color='gray', alpha=0.5)
ax.add_patch(patches.FancyBboxPatch((15-2.25, -0.5), 4.5, 1, boxstyle="round,pad=0.05", fc='#2196F3', ec='white', lw=1.5))
ax.add_patch(patches.FancyBboxPatch((50-2.25, -0.5), 4.5, 1, boxstyle="round,pad=0.05", fc='#F44336', ec='white', lw=1.5))
ax.annotate('', xy=(25, 0), xytext=(19, 0), arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2))
ax.annotate('', xy=(60, 0), xytext=(54, 0), arrowprops=dict(arrowstyle='->', color='#F44336', lw=2))
ax.annotate('35m', xy=(32, 2), fontsize=12, ha='center', color='green', fontweight='bold')
ax.annotate('IDM has enough\ndistance to brake', xy=(32, -3), fontsize=9, ha='center', color='green')
ax.set_xlim(-10, 80)
ax.set_ylim(-8, 15)
ax.set_aspect('equal')
ax.set_title('Safe: Far enough, IDM reacts in time', fontsize=11, fontweight='bold')
ax.set_xlabel('X (m)')

# 中图：碰撞场景
ax = axes[1]
ax.fill_between([-10, 50], -7, 0, color='#f0f0f0', alpha=0.5)
ax.fill_between([-10, 50], 0, 7, color='#e8e8e8', alpha=0.5)
ax.fill_between([-10, 50], 7, 14, color='#f0f0f0', alpha=0.5)
ax.plot([-10, 50], [0, 0], '--', color='gray', alpha=0.5)
ax.plot([-10, 50], [7, 7], '--', color='gray', alpha=0.5)
ax.add_patch(patches.FancyBboxPatch((15-2.25, -0.5), 4.5, 1, boxstyle="round,pad=0.05", fc='#2196F3', ec='white', lw=1.5))
ax.add_patch(patches.FancyBboxPatch((18-2.25, -0.5), 4.5, 1, boxstyle="round,pad=0.05", fc='#F44336', ec='white', lw=1.5))
ax.annotate('', xy=(22, 0), xytext=(19, 0), arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2))
ax.annotate('3m!', xy=(16.5, 2), fontsize=14, ha='center', color='red', fontweight='bold')
ax.annotate('Need 60m\nto stop!', xy=(30, -4), fontsize=10, ha='center', color='red')
ax.annotate('X', xy=(18.5, 0.5), fontsize=20, ha='center', color='red', fontweight='bold')
ax.set_xlim(-10, 50)
ax.set_ylim(-8, 15)
ax.set_aspect('equal')
ax.set_title('Collision: Too close, cannot stop!', fontsize=11, fontweight='bold', color='red')
ax.set_xlabel('X (m)')

# 右图：穷举位置的思路
ax = axes[2]
ax.fill_between([-10, 80], -7, 0, color='#f0f0f0', alpha=0.5)
ax.fill_between([-10, 80], 0, 7, color='#e8e8e8', alpha=0.5)
ax.fill_between([-10, 80], 7, 14, color='#f0f0f0', alpha=0.5)
ax.plot([-10, 80], [0, 0], '--', color='gray', alpha=0.5)
ax.plot([-10, 80], [7, 7], '--', color='gray', alpha=0.5)
ax.add_patch(patches.FancyBboxPatch((15-2.25, -0.5), 4.5, 1, boxstyle="round,pad=0.05", fc='#2196F3', ec='white', lw=1.5))

# 画多个可能的障碍物位置
positions = [(20, 0), (25, 0), (30, 0), (35, 0), (40, 0), (25, 3.5), (30, 3.5), (20, -3.5)]
for i, (px, py) in enumerate(positions):
    c = '#F44336' if px < 25 else '#FF9800' if px < 35 else '#4CAF50'
    ax.add_patch(patches.FancyBboxPatch((px-2.25, py-0.5), 4.5, 1, boxstyle="round,pad=0.05", fc=c, ec='white', lw=1, alpha=0.7))

ax.annotate('Python enumerates\n80 param combos', xy=(50, 8), fontsize=10, ha='center', color='#333', fontweight='bold')
ax.annotate('Red=Danger\nOrange=Edge\nGreen=Safe', xy=(50, -4), fontsize=9, ha='center', color='#666')
ax.set_xlim(-10, 80)
ax.set_ylim(-8, 15)
ax.set_aspect('equal')
ax.set_title('Next: Python enumerates positions + UPPAAL enumerates behaviors', fontsize=11, fontweight='bold', color='#1565C0')
ax.set_xlabel('X (m)')

plt.tight_layout()
filepath = os.path.join(OUTPUT_DIR, "04_analysis_comparison.png")
plt.savefig(filepath, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {filepath}")

print("\nDone! All figures saved to:", OUTPUT_DIR)
