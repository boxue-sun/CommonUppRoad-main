"""
experiment_lateral.py
实验：变化障碍物横向位置和朝向，找到碰撞场景
"""
import os
import sys
import copy
import json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from commonroad.common.file_reader import CommonRoadFileReader
from generate_uppaal_models import generate_model_for_scenario

BASE_SCENARIO = os.path.join(os.path.dirname(__file__), "scenarios", "DEU_Ffb-1_3_T-1.xml")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "experiments", "exp_lateral")
MODELS_DIR = os.path.join(OUTPUT_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# 参数空间：3个维度
LATERAL_OFFSETS = [-15, -10, -5, 0, 5, 10, 15]  # 横向偏移（米），负=向右靠近ego
HEADING_OFFSETS = [-1.5, -0.8, 0, 0.8, 1.5]     # 朝向偏移（弧度），负=转向ego方向
SPEED_FACTORS = [0.5, 1.0, 1.5]                   # 障碍物速度系数

# 只改 Obs 200（在 ego 同车道最近的那辆）
TARGET_OBS_INDEX = 0  # Obs 200

def run_experiment():
    scenario, pps = CommonRoadFileReader(BASE_SCENARIO).open()

    print(f"Base scenario: {BASE_SCENARIO}")
    print(f"Target obstacle: index={TARGET_OBS_INDEX}")
    print(f"  Original pos: ({scenario.dynamic_obstacles[TARGET_OBS_INDEX].initial_state.position[0]:.1f}, "
          f"{scenario.dynamic_obstacles[TARGET_OBS_INDEX].initial_state.position[1]:.1f})")
    print(f"  Original vel: {scenario.dynamic_obstacles[TARGET_OBS_INDEX].initial_state.velocity:.1f}")
    print()

    variants = []
    vid = 0

    for speed_factor in SPEED_FACTORS:
        for lat_offset in LATERAL_OFFSETS:
            for head_offset in HEADING_OFFSETS:
                variants.append({
                    'id': vid,
                    'speed_factor': speed_factor,
                    'lateral_offset': lat_offset,
                    'heading_offset': head_offset,
                })
                vid += 1

    print(f"Total variants: {len(variants)}")
    print("=" * 60)

    # 生成参数表
    param_table = {
        'param_space': {
            'speed_factor': {'values': SPEED_FACTORS, 'description': 'Obstacle speed multiplier'},
            'lateral_offset': {'values': LATERAL_OFFSETS, 'description': 'Lateral offset (m), negative=toward ego'},
            'heading_offset': {'values': HEADING_OFFSETS, 'description': 'Heading offset (rad), negative=toward ego'},
        },
        'mutations': variants,
        'total_count': len(variants),
    }
    with open(os.path.join(OUTPUT_DIR, 'param_table.json'), 'w') as f:
        json.dump(param_table, f, indent=2)

    # 为每个变体生成 UPPAAL 模型
    obs = scenario.dynamic_obstacles[TARGET_OBS_INDEX]
    orig_x = obs.initial_state.position[0]
    orig_y = obs.initial_state.position[1]
    orig_vel = obs.initial_state.velocity
    orig_heading = obs.initial_state.orientation

    for v in variants:
        # 复制场景
        s = copy.deepcopy(scenario)
        target_obs = s.dynamic_obstacles[TARGET_OBS_INDEX]

        # 修改障碍物参数
        new_y = orig_y + v['lateral_offset']         # 横向偏移
        new_heading = orig_heading + v['heading_offset']  # 朝向偏移
        new_vel = orig_vel * v['speed_factor']         # 速度

        target_obs.initial_state.position = np.array([orig_x, new_y])
        target_obs.initial_state.orientation = new_heading
        target_obs.initial_state.velocity = new_vel

        # 生成 UPPAAL 模型
        model_path = os.path.join(MODELS_DIR, f"variant_{v['id']:04d}.xml")
        try:
            generate_model_for_scenario(s, pps, model_path)
            status = "OK"
        except Exception as e:
            status = f"ERROR: {e}"

        if v['id'] % 10 == 0 or v['id'] == len(variants) - 1:
            print(f"[{v['id']:3d}/{len(variants)}] lat={v['lateral_offset']:+4.0f}m "
                  f"head={v['heading_offset']:+.1f}rad vel×{v['speed_factor']:.1f} -> {status}")

    print(f"\nGenerated {len(variants)} models in {MODELS_DIR}")
    print(f"Next: run batch_verify_lateral.py to verify all models")


if __name__ == '__main__':
    run_experiment()
