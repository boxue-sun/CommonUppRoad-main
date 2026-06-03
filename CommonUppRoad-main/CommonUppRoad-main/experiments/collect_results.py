#!/usr/bin/env python3
"""
collect_results.py — 收集 UPPAAL GUI 验证结果，生成分析报告

工作流程:
  1. 用户手动在 UPPAAL GUI 中运行每个模型的验证查询
  2. 将结果填入 results.csv（模板由本脚本生成）
  3. 本脚本做汇总分析：统计、参数敏感性、LaTeX 表格
"""

import os
import sys
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict


class ResultCollector:
    """UPPAAL 验证结果收集器"""

    def __init__(self, results_csv):
        self.results = []
        self._load(results_csv)

    def _load(self, csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'params' in row and row['params']:
                    try:
                        row['params'] = json.loads(row['params'])
                    except json.JSONDecodeError:
                        row['params'] = {}
                else:
                    row['params'] = {}
                row['collision_found'] = row.get('collision_found', '').upper() == 'TRUE'
                row['outside_found'] = row.get('outside_found', '').upper() == 'TRUE'
                row['reach_possible'] = row.get('reach_possible', '').upper() == 'TRUE'
                self.results.append(row)

    def summary(self):
        """生成汇总统计"""
        total = len(self.results)
        collisions = sum(1 for r in self.results if r['collision_found'])
        outsides = sum(1 for r in self.results if r['outside_found'])
        reaches = sum(1 for r in self.results if r['reach_possible'])

        return {
            'total_scenarios': total,
            'collision_scenarios': collisions,
            'outside_scenarios': outsides,
            'safe_scenarios': total - collisions,
            'reach_possible': reaches,
            'collision_rate': collisions / total if total > 0 else 0,
        }

    def by_param(self, param_name):
        """按参数分组统计碰撞率"""
        groups = defaultdict(lambda: {'total': 0, 'collisions': 0})
        for r in self.results:
            val = r['params'].get(param_name, 'unknown')
            groups[val]['total'] += 1
            if r['collision_found']:
                groups[val]['collisions'] += 1

        return {val: g['collisions'] / max(g['total'], 1)
                for val, g in sorted(groups.items(), key=lambda x: float(x[0]) if isinstance(x[0], (int, float)) else 0)}

    def plot_param_sensitivity(self, output_path='experiments/param_sensitivity.png'):
        """参数敏感性分析图"""
        key_params = [
            ('obs_initial_speed_factor', 'Obs Initial Speed Factor'),
            ('ego_initial_speed_factor', 'Ego Initial Speed Factor'),
            ('obs_longitudinal_offset', 'Obs Longitudinal Offset (m)'),
            ('obs_max_speed_factor', 'Obs Max Speed Factor'),
            ('obs_brake_aggressiveness', 'Brake Aggressiveness (m/s^2)'),
            ('ego_target_speed', 'Ego Target Speed (m/s)'),
        ]

        available = [(k, label) for k, label in key_params
                     if any(k in r['params'] for r in self.results)]

        if not available:
            print("[Plot] No parameter data available for sensitivity analysis")
            return

        n = len(available)
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
        if n == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        for ax, (param, label) in zip(axes, available):
            groups = self.by_param(param)
            if groups:
                keys = list(groups.keys())
                vals = [groups[k] for k in keys]
                bars = ax.bar(range(len(keys)), vals, color='steelblue', edgecolor='white')
                ax.set_xticks(range(len(keys)))
                ax.set_xticklabels([f'{k:.1f}' if isinstance(k, float) else str(k)
                                   for k in keys], rotation=45, ha='right', fontsize=8)
                ax.set_title(label, fontsize=10)
                ax.set_ylabel('Collision Rate')
                ax.set_ylim(0, 1.1)
                for bar, v in zip(bars, vals):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                            f'{v:.2f}', ha='center', fontsize=7)

        for ax in axes[n:]:
            ax.set_visible(False)

        fig.suptitle('Parameter Sensitivity — Collision Rate Analysis', fontsize=14)
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[Plot] Saved to {output_path}")

    def export_latex_table(self, output_path='experiments/results_table.tex'):
        """生成 LaTeX 表格"""
        summary = self.summary()

        latex = r"""\begin{table}[htbp]
\centering
\caption{Adversarial Scenario Mining Results}
\label{tab:adversarial_results}
\begin{tabular}{lcc}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
"""
        latex += f"Total Scenarios     & {summary['total_scenarios']} \\\\\n"
        latex += f"Collision Scenarios & {summary['collision_scenarios']} \\\\\n"
        latex += f"Safe Scenarios      & {summary['safe_scenarios']} \\\\\n"
        latex += f"Collision Rate      & {summary['collision_rate']*100:.1f}\\% \\\\\n"
        latex += r"""\hline
\end{tabular}
\end{table}
"""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex)
        print(f"[LaTeX] Table saved to {output_path}")

    def export_csv_template(self, output_path, param_table_path=None):
        """导出 results.csv 模板供用户填写"""
        # If we have param_table.json, use it to populate params column
        params_map = {}
        if param_table_path and os.path.exists(param_table_path):
            with open(param_table_path, 'r') as f:
                data = json.load(f)
            for m in data.get('mutations', []):
                params_map[f"variant_{m['id']:04d}"] = json.dumps(m['params'])

        fieldnames = ['variant_id', 'params',
                      'collision_found', 'outside_found', 'reach_possible',
                      'collision_time', 'collision_speed', 'notes']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for variant_id in sorted(params_map.keys()):
                writer.writerow({
                    'variant_id': variant_id,
                    'params': params_map.get(variant_id, ''),
                    'collision_found': '',
                    'outside_found': '',
                    'reach_possible': '',
                    'collision_time': '',
                    'collision_speed': '',
                    'notes': '',
                })
        print(f"[Template] CSV template saved to {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='UPPAAL Result Collection and Analysis')
    parser.add_argument('--results', type=str, default='experiments/exp_adversarial/results.csv',
                       help='results.csv 文件路径')
    parser.add_argument('--output', type=str, default='experiments/exp_adversarial',
                       help='输出目录')
    parser.add_argument('--param-table', type=str,
                       default='experiments/exp_adversarial/param_table.json',
                       help='参数表 JSON 路径（用于生成 CSV 模板）')
    parser.add_argument('--export-template', action='store_true',
                       help='仅导出 CSV 模板')
    args = parser.parse_args()

    # If only creating template
    if args.export_template or not os.path.exists(args.results):
        collector = ResultCollector.__new__(ResultCollector)
        collector.export_csv_template(args.results, args.param_table)
        if args.export_template:
            return

    if not os.path.exists(args.results):
        print(f"[Error] Results file not found: {args.results}")
        print(f"        Run with --export-template to create a CSV template first")
        sys.exit(1)

    collector = ResultCollector(args.results)
    summary = collector.summary()

    print("=" * 50)
    print("Adversarial Scenario Mining — Results Summary")
    print("=" * 50)
    print(f"Total Scenarios:     {summary['total_scenarios']}")
    print(f"Collision Scenarios: {summary['collision_scenarios']}")
    print(f"Outside Scenarios:   {summary['outside_scenarios']}")
    print(f"Safe Scenarios:      {summary['safe_scenarios']}")
    print(f"Collision Rate:      {summary['collision_rate']*100:.1f}%")
    print(f"Reach Possible:      {summary['reach_possible']}")
    print("=" * 50)

    collector.plot_param_sensitivity(
        os.path.join(args.output, 'param_sensitivity.png')
    )
    collector.export_latex_table(
        os.path.join(args.output, 'results_table.tex')
    )


if __name__ == '__main__':
    main()
