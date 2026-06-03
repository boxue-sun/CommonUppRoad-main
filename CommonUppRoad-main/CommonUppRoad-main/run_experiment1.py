#!/usr/bin/env python3
"""
实验 1: 参数对必撞概率的影响分析（参数敏感性实验）

对标论文 Table 5.1 / Figure 5.3
"""

import os
import sys
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from adversarial_search import ScenarioMutator, PARAM_SPACE


def run_experiment_1():
    """参数敏感性实验"""
    print("=" * 60)
    print("Experiment 1: Parameter Sensitivity Analysis")
    print("=" * 60)

    # 1. 生成场景变体
    print("\n[Step 1] Generating scenario variants...")
    scenario_path = os.path.join(ROOT, 'scenarios', 'DEU_Ffb-1_3_T-1.xml')
    mutator = ScenarioMutator(scenario_path)

    # 小规模网格搜索（便于手工 UPPAAL 验证）
    mutator.grid_search(param_keys=[
        'obs_initial_speed_factor',    # 4 个值: 0.5, 1.0, 1.5, 2.0
        'ego_initial_speed_factor',    # 4 个值: 0.5, 1.0, 1.5, 2.0
        'obs_longitudinal_offset',     # 5 个值: -30, -15, 0, 15, 30
    ])  # 总共 4×4×5 = 80 变体

    output_dir = os.path.join(ROOT, 'experiments', 'exp1')
    os.makedirs(output_dir, exist_ok=True)

    # 2. 导出参数表
    table_path = os.path.join(output_dir, 'param_table.json')
    mutator.export_param_table(table_path)

    # 3. 导出 CSV 模板
    csv_path = os.path.join(output_dir, 'results.csv')
    print(f"\n[Step 2] Creating results CSV template...")
    from experiments.collect_results import ResultCollector
    collector = ResultCollector.__new__(ResultCollector)
    collector.export_csv_template(csv_path, table_path)

    # 4. 打印摘要
    print(f"\n{'=' * 60}")
    print(f"Generated {len(mutator.mutations)} scenario variants")
    print(f"Parameter table: {table_path}")
    print(f"Results template: {csv_path}")
    print(f"\nNext steps:")
    print(f"  1. Generate UPPAAL models:")
    print(f"     python adversarial_search.py --scenario {scenario_path} \\")
    print(f"         --method grid --generate-models --output {output_dir}")
    print(f"  2. Open models in Windows UPPAAL GUI (Verifier tab)")
    print(f"  3. For each variant, run: A[] !cps_i_state.detection.collide")
    print(f"  4. Record results in: {csv_path}")
    print(f"  5. Analyze with:")
    print(f"     python experiments/collect_results.py \\")
    print(f"         --results {csv_path} --output {output_dir}")
    print(f"{'=' * 60}")

    # 5. 建议 LHS 采样缩减
    print(f"\n[Tip] For pre-experiment, use LHS with 20 samples:")
    print(f"  python adversarial_search.py --scenario {scenario_path} "
          f"--method lhs --n-samples 20 --output experiments/exp1_pre/")

    return mutator


def run_experiment_2():
    """多场景类型对比实验"""
    print("=" * 60)
    print("Experiment 2: Multi-Scenario Type Comparison")
    print("=" * 60)

    scenarios = [
        ('highway', 'scenarios/DEU_Ffb-1_3_T-1.xml',
         'Highway with dynamic obstacles'),
        ('merging', 'scenarios/ZAM_Ramp-1_1-T-1.xml',
         'Ramp merging scenario'),
        ('t_junction', 'scenarios/ZAM_Tjunction-1_216_T-1.xml',
         'T-junction intersection'),
    ]

    all_params = list(PARAM_SPACE.keys())
    np.random = __import__('numpy').random

    for scene_type, scene_path, scene_desc in scenarios:
        full_path = os.path.join(ROOT, scene_path)
        if not os.path.exists(full_path):
            print(f"  [Skip] {scene_type}: file not found ({scene_path})")
            continue

        print(f"\n[Scene] {scene_type}: {scene_desc}")
        mutator = ScenarioMutator(full_path)
        mutator.latin_hypercube(n_samples=50, param_keys=all_params)

        output_dir = os.path.join(ROOT, 'experiments', 'exp2', scene_type)
        os.makedirs(output_dir, exist_ok=True)
        table_path = os.path.join(output_dir, 'param_table.json')
        mutator.export_param_table(table_path)

        print(f"  Generated {len(mutator.mutations)} variants -> {output_dir}")

    print(f"\n[Done] Multi-scenario parameter tables generated")
    print(f"[Next] Run UPPAAL verification on each scenario type's variants")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run Adversarial Mining Experiments')
    parser.add_argument('--exp', type=str, default='1', choices=['1', '2'],
                       help='Experiment number (1=parameter sensitivity, 2=multi-scenario)')
    args = parser.parse_args()

    if args.exp == '1':
        run_experiment_1()
    else:
        run_experiment_2()
