#!/usr/bin/env python3
"""
adversarial_search.py — 自动化必撞场景挖掘框架
用于硕士论文：基于形式化验证(UPPAAL)的自动驾驶对抗性测试方法研究

工作流程:
  1. 读取基础 CommonRoad 场景
  2. 在参数空间内产生变异
  3. 为每个变异生成 UPPAAL 模型
  4. 用户在 UPPAAL GUI 中批量验证
  5. 收集结果，统计必撞场景
"""

import os
import sys
import copy
import itertools
import json
import numpy as np

from commonroad.common.file_reader import CommonRoadFileReader

ROOT = os.path.dirname(os.path.abspath(__file__))

# === 参数空间定义 ===
PARAM_SPACE = {
    'obs_initial_speed_factor': {
        'type': 'continuous',
        'range': [0.5, 2.0],
        'step': 0.5,
        'description': '障碍物初始速度系数 (×原始速度)',
    },
    'obs_longitudinal_offset': {
        'type': 'continuous',
        'range': [-30.0, 30.0],
        'step': 15.0,
        'description': '障碍物纵向偏移 (m)',
    },
    'obs_count': {
        'type': 'discrete',
        'values': [1, 2, 3],
        'description': '障碍车数量',
    },
    'obs_max_speed_factor': {
        'type': 'continuous',
        'range': [0.8, 2.5],
        'step': 0.5,
        'description': '障碍物最大速度系数',
    },
    'obs_brake_aggressiveness': {
        'type': 'continuous',
        'range': [2.0, 8.0],
        'step': 2.0,
        'description': '急刹车减速度 (m/s^2)',
    },
    'ego_initial_speed_factor': {
        'type': 'continuous',
        'range': [0.5, 2.0],
        'step': 0.5,
        'description': 'Ego车初始速度系数',
    },
    'ego_target_speed': {
        'type': 'continuous',
        'range': [10.0, 35.0],
        'step': 10.0,
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
        """网格搜索：穷举所有参数组合"""
        if param_keys is None:
            param_keys = ['obs_initial_speed_factor', 'ego_initial_speed_factor',
                         'obs_longitudinal_offset']

        param_specs = {k: PARAM_SPACE[k] for k in param_keys if k in PARAM_SPACE}
        values_list = []

        for key, spec in param_specs.items():
            if spec['type'] == 'continuous':
                r = spec['range']
                values = np.arange(r[0], r[1] + spec['step'] / 2, spec['step']).tolist()
                values_list.append(values)
            elif spec['type'] == 'discrete':
                values_list.append(spec['values'])

        for combo in itertools.product(*values_list):
            params = dict(zip(param_keys, combo))
            self.mutations.append(params)

        print(f"[GridSearch] {len(self.mutations)} parameter combinations generated")
        return self.mutations

    def latin_hypercube(self, n_samples=100, param_keys=None):
        """拉丁超立方采样：均匀覆盖大参数空间"""
        if param_keys is None:
            param_keys = list(PARAM_SPACE.keys())

        n_dims = len(param_keys)
        segments = np.linspace(0, 1, n_samples + 1)
        samples = np.zeros((n_samples, n_dims))

        for i in range(n_dims):
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
                    idx = min(idx, len(spec['values']) - 1)
                    params[key] = spec['values'][idx]
            self.mutations.append(params)

        print(f"[LHS] {n_samples} samples generated for {n_dims} parameters")
        return self.mutations

    def apply_mutation(self, params):
        """将参数应用到场景，返回修改后的场景副本"""
        mutated = copy.deepcopy(self.scenario)

        # 修改动态障碍物初始状态
        for obs in mutated.dynamic_obstacles:
            init = obs.initial_state
            if 'obs_initial_speed_factor' in params:
                factor = params['obs_initial_speed_factor']
                init.velocity = init.velocity * factor
            if 'obs_longitudinal_offset' in params:
                offset = params['obs_longitudinal_offset']
                dx = offset * np.cos(init.orientation) if hasattr(init, 'orientation') else offset
                dy = offset * np.sin(init.orientation) if hasattr(init, 'orientation') else 0
                init.position = np.array([
                    init.position[0] + dx,
                    init.position[1] + dy,
                ])
            # 修改行为参数中的最大速度系数和刹車力度
            obs._adversarial_params = {
                'max_speed_factor': params.get('obs_max_speed_factor', 1.0),
                'brake_aggressiveness': params.get('obs_brake_aggressiveness', 4.0),
            }

        # 修改 obstacle 数量（删除或保留）
        if 'obs_count' in params:
            target_count = int(params['obs_count'])
            while len(mutated.dynamic_obstacles) > target_count:
                mutated.remove_obstacle(mutated.dynamic_obstacles[-1])

        # 修改 ego 初始速度
        for pp in self.planning_problem_set.planning_problem_dict.values():
            if 'ego_initial_speed_factor' in params:
                pp.initial_state.velocity *= params['ego_initial_speed_factor']

        return mutated

    def export_param_table(self, output_path='experiments/param_table.json'):
        """导出参数表"""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        export_data = {
            'param_space': {k: {kk: str(vv) if isinstance(vv, list) else vv
                                for kk, vv in v.items()}
                           for k, v in PARAM_SPACE.items()},
            'mutations': [
                {'id': i, 'params': {k: round(v, 4) if isinstance(v, float) else v
                                      for k, v in p.items()}}
                for i, p in enumerate(self.mutations)
            ],
            'total_count': len(self.mutations),
        }
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"[Export] Parameter table saved to {output_path}")


class UppaalModelBatchGenerator:
    """UPPAAL 模型批量生成器"""

    def __init__(self, template_path, output_dir):
        self.template_path = template_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(self, mutator):
        """为每个变异生成 UPPAAL 模型"""
        from generate_uppaal_models import generate_model_for_scenario

        models = []
        for i, params in enumerate(mutator.mutations):
            model_name = f"variant_{i:04d}"
            model_path = os.path.join(self.output_dir, f"{model_name}.xml")

            mutated_scenario = mutator.apply_mutation(params)
            try:
                generate_model_for_scenario(
                    mutated_scenario,
                    mutator.planning_problem_set,
                    model_path
                )
                models.append({
                    'id': i,
                    'params': params,
                    'model_path': model_path,
                    'status': 'generated',
                })
            except Exception as e:
                print(f"[WARN] Failed to generate variant {i}: {e}")
                models.append({
                    'id': i,
                    'params': params,
                    'status': f'failed: {e}',
                })

        print(f"[Generate] {len(models)} UPPAAL models generated")
        return models


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Adversarial Scenario Mining Framework')
    parser.add_argument('--scenario', type=str,
                       default=os.path.join(ROOT, 'scenarios/DEU_Ffb-1_3_T-1.xml'),
                       help='基础 CommonRoad 场景路径')
    parser.add_argument('--method', type=str, default='grid',
                       choices=['grid', 'lhs'],
                       help='参数搜索方法')
    parser.add_argument('--n-samples', type=int, default=100,
                       help='LHS 采样数量')
    parser.add_argument('--output', type=str,
                       default=os.path.join(ROOT, 'experiments/exp_adversarial'),
                       help='输出目录')
    parser.add_argument('--export-table', action='store_true', default=True,
                       help='导出参数表 JSON')
    parser.add_argument('--generate-models', action='store_true',
                       help='生成 UPPAAL 模型 (需要 template.xml)')

    args = parser.parse_args()

    # 1. 场景变异
    print("=" * 50)
    print("必撞场景挖掘框架")
    print("=" * 50)
    print(f"基础场景: {args.scenario}")
    print(f"搜索方法: {args.method}")

    mutator = ScenarioMutator(args.scenario)
    if args.method == 'grid':
        mutator.grid_search()
    else:
        mutator.latin_hypercube(n_samples=args.n_samples)

    if args.export_table:
        table_path = os.path.join(args.output, 'param_table.json')
        mutator.export_param_table(table_path)

    # 2. 生成 UPPAAL 模型批次
    if args.generate_models:
        template = os.path.join(ROOT, 'uppaal/template.xml')
        model_dir = os.path.join(args.output, 'models')
        generator = UppaalModelBatchGenerator(template, model_dir)
        models = generator.generate_all(mutator)

        # 保存生成报告
        report_path = os.path.join(args.output, 'generation_report.json')
        with open(report_path, 'w') as f:
            json.dump(models, f, indent=2, default=str)
        print(f"[Report] Generation report saved to {report_path}")

    print(f"\n[Done] Generated {len(mutator.mutations)} scenario variants")
    print(f"[Next] Open models in Windows UPPAAL GUI to verify")
    print(f"       运行查询: A[] !cps_i_state.detection.collide")
    print(f"       结果填入: {os.path.join(args.output, 'results.csv')}")


if __name__ == '__main__':
    main()
