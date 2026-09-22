"""
generate_gifs.py
ISO 15622 模型实验 GIF 动画生成器
按距离/速度分类保存到不同文件夹
"""
import os
import sys
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "experiments", "animation", "iso15622")
os.makedirs(OUTPUT_BASE, exist_ok=True)

# ISO 15622 参数
V_SET = 30.0
T_HW = 1.8
S0 = 2.0
A_MAX = 1.5
COMFORT_BRAKE = -2.0
EMERGENCY_BRAKE = -6.0
BRAKE_RATE = 3.0
REACTION_TIME = 1.5
DANGER_TTC = 1.5
WARNING_TTC = 3.0
APPROACH_DIST = 80.0
P_GAIN = 0.4

DT = 0.1
STEPS = 100  # 10秒


def simulate_iso15622(ego_speed, obs_speed, distance):
    """模拟 ISO 15622 ACC 模型，返回每步状态"""
    ego_pos = 0.0
    ego_vel = ego_speed
    ego_acc = 0.0
    obs_pos = float(distance)
    obs_vel = float(obs_speed)

    danger_detected = False
    reaction_step = 0

    trajectory = []
    collision = False
    mode = 0  # 0=free, 1=approach, 2=follow, 3=brake

    for step in range(STEPS):
        t = step * DT
        gap = obs_pos - ego_pos - 2.25  # 车头到车尾

        trajectory.append({
            't': t, 'ego_pos': ego_pos, 'ego_vel': ego_vel,
            'ego_acc': ego_acc, 'obs_pos': obs_pos, 'obs_vel': obs_vel,
            'gap': gap, 'mode': mode
        })

        if gap < 0 and not collision:
            collision = True

        # TTC
        rel_vel = ego_vel - obs_vel
        if rel_vel > 0.1:
            ttc = gap / rel_vel
        else:
            ttc = 999.0

        # 层1: 反应延迟
        if ttc < WARNING_TTC:
            if not danger_detected:
                danger_detected = True
                reaction_step = 0
            reaction_step += 1
        else:
            danger_detected = False
            reaction_step = 0

        if danger_detected and reaction_step * DT < REACTION_TIME:
            # 反应延迟: 不干预
            pass
        else:
            # 层2: 四模式决策
            desired_gap = S0 + ego_vel * T_HW

            if gap > APPROACH_DIST:
                mode = 0
                target_acc = A_MAX if ego_vel < V_SET else 0.0
            elif gap > desired_gap + 5.0:
                mode = 1
                denom = APPROACH_DIST - desired_gap - 5.0
                if denom < 1.0:
                    denom = 1.0
                gap_ratio = max(0.0, min(1.0, (APPROACH_DIST - gap) / denom))
                target_acc = -gap_ratio * 2.0
                if ego_vel < obs_vel:
                    target_acc = 0.0
            elif gap > S0:
                mode = 2
                gap_error = gap - desired_gap
                target_acc = P_GAIN * gap_error - 0.5 * rel_vel
                target_acc = max(COMFORT_BRAKE, min(A_MAX, target_acc))
            else:
                mode = 3
                target_acc = EMERGENCY_BRAKE

            # 层3: 紧急制动覆盖
            if ttc < DANGER_TTC:
                mode = 3
                target_acc = EMERGENCY_BRAKE
            elif ttc < WARNING_TTC and mode != 2:
                if target_acc > COMFORT_BRAKE:
                    target_acc = COMFORT_BRAKE

            # 渐进刹车
            acc_step = BRAKE_RATE * DT
            if target_acc < ego_acc - acc_step:
                ego_acc = ego_acc - acc_step
            elif target_acc > ego_acc + acc_step:
                ego_acc = ego_acc + acc_step
            else:
                ego_acc = target_acc

        # 更新速度和位置
        ego_vel = ego_vel + ego_acc * DT
        if ego_vel < 0:
            ego_vel = 0.0
        ego_pos = ego_pos + ego_vel * DT
        obs_pos = obs_pos + obs_vel * DT

    return trajectory, collision


def get_mode_name(mode):
    return ['Free', 'Approach', 'Follow', 'Brake'][mode]


def get_mode_color(mode):
    return ['#4CAF50', '#FF9800', '#2196F3', '#F44336'][mode]


def generate_gif(trajectory, collision, ego_speed, obs_speed, distance, filename):
    """生成 GIF 动画"""
    # 计算画面范围
    max_pos = max(max(f['ego_pos'] for f in trajectory),
                  max(f['obs_pos'] for f in trajectory)) + 30
    x_min = -10
    x_max = max(max_pos, distance + 50)
    road_width = 7.0

    # 高度: 道路 + 上方留空显示信息
    img_height = 260
    img_width = 900
    y_road_top = 100
    y_road_bottom = y_road_top + road_width * 4  # 4条车道
    y_center = (y_road_top + y_road_bottom) / 2

    def x_to_px(x):
        return int((x - x_min) / (x_max - x_min) * (img_width - 60) + 30)

    def y_to_px(y):
        return int(y_road_bottom - (y - (-road_width)) / (road_width * 5) * (y_road_bottom - y_road_top + 60) - 30)

    frames = []
    step_skip = 2  # 每2步取一帧

    for i in range(0, len(trajectory), step_skip):
        f = trajectory[i]
        img = Image.new('RGB', (img_width, img_height), '#f5f5f5')
        draw = ImageDraw.Draw(img)

        # 画道路
        for lane in range(4):
            yt = y_road_top + lane * road_width * 4 // 4
            yb = yt + road_width * 4 // 4
            color = '#FFB74D' if lane % 2 == 0 else '#FFA726'
            draw.rectangle([0, yt, img_width, yb], fill=color)

        # 画车道线
        for lane in range(5):
            y = y_road_top + lane * road_width * 4 // 4
            draw.line([(0, y), (img_width, y)], fill='white', width=2)

        # 画 ego 车
        ex = x_to_px(f['ego_pos'])
        ew, eh = 36, 14
        ey = y_center - eh // 2
        draw.rectangle([ex - ew // 2, ey, ex + ew // 2, ey + eh], fill='#1565C0', outline='white', width=1)
        draw.text((ex - ew // 2, ey - 14), f'Ego {f["ego_vel"]:.1f}', fill='#1565C0')

        # 画障碍物
        ox = x_to_px(f['obs_pos'])
        ow, oh = 36, 14
        oy = y_center - oh // 2
        draw.rectangle([ox - ow // 2, oy, ox + ow // 2, oy + oh], fill='#E53935', outline='white', width=1)
        draw.text((ox - ow // 2, oy + oh + 2), f'Obs {f["obs_vel"]:.1f}', fill='#E53935')

        # 画间隙线
        if f['gap'] > 0:
            draw.line([(ex + ew // 2, y_center), (ox - ow // 2, y_center)], fill='#333', width=1)
            gap_text = f'{f["gap"]:.1f}m'
            gap_x = (ex + ox) // 2
            draw.text((gap_x - 10, y_center - 18), gap_text, fill='#333')

        # 顶部信息栏
        mode_color = get_mode_color(f['mode'])
        mode_name = get_mode_name(f['mode'])
        status = 'COLLISION!' if collision and i == len(trajectory) - step_skip else ''

        info = f'T={f["t"]:.1f}s  Mode={mode_name}  TTC={min(f["gap"]/(f["ego_vel"]-f["obs_vel"]+0.01), 999):.1f}s'
        draw.rectangle([0, 0, img_width, 25], fill='#333')
        draw.text((10, 4), info, fill='white')

        # 底部状态栏
        draw.rectangle([0, img_height - 22, img_width, img_height], fill='#333')
        result_text = f'ego={ego_speed}m/s obs={obs_speed}m/s dist={distance}m  '
        result_text += f'Result: {"COLLISION" if collision else "SAFE"}'
        if collision and f['gap'] < 0:
            result_text += '  ** CRASH **'
        draw.text((10, img_height - 18), result_text, fill='#FF5252' if collision else '#4CAF50')

        # 模式指示灯
        draw.rectangle([img_width - 120, 3, img_width - 100, 20], fill=mode_color)
        draw.text((img_width - 95, 4), mode_name, fill='white')

        frames.append(img)

    # 保存 GIF
    filepath = os.path.join(OUTPUT_BASE, filename)
    frames[0].save(filepath, save_all=True, append_images=frames[1:],
                   duration=80, loop=0, optimize=True)
    return filepath


def main():
    # 参数空间
    distances = [3, 5, 8, 10, 15, 20, 30, 50]
    obs_speeds = [0, 1, 3, 5, 10]
    ego_speeds = [10, 15, 20, 25, 30]

    # 按距离分类的子文件夹
    for d in distances:
        os.makedirs(os.path.join(OUTPUT_BASE, f'dist_{d}m'), exist_ok=True)

    total = len(distances) * len(obs_speeds) * len(ego_speeds)
    print(f"Generating {total} GIFs...")
    print(f"Output: {OUTPUT_BASE}")
    print("=" * 60)

    count = 0
    collision_gifs = []
    safe_gifs = []

    for dist in distances:
        for obs_spd in obs_speeds:
            for ego_spd in ego_speeds:
                traj, collision = simulate_iso15622(ego_spd, obs_spd, dist)

                result_tag = "collision" if collision else "safe"
                fname = f"{result_tag}_ego{ego_spd}_obs{obs_spd}_dist{dist}.gif"

                subfolder = os.path.join(OUTPUT_BASE, f'dist_{dist}m')
                filepath = generate_gif(traj, collision, ego_spd, obs_spd, dist, fname)
                # 同时保存到子文件夹
                import shutil
                shutil.copy2(filepath, os.path.join(subfolder, fname))

                count += 1
                tag = "COLLISION!" if collision else "safe"
                print(f"[{count:3d}/{total}] dist={dist:2d}m obs={obs_spd:2d} ego={ego_spd:2d} -> {tag}")

                if collision:
                    collision_gifs.append(filepath)
                else:
                    safe_gifs.append(filepath)

    print("\n" + "=" * 60)
    print(f"Total: {total} GIFs generated")
    print(f"Collision: {len(collision_gifs)}")
    print(f"Safe: {len(safe_gifs)}")
    print(f"Output: {OUTPUT_BASE}")


if __name__ == '__main__':
    main()
