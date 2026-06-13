import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from .config import CONFIG


class AdjustmentAdvisor:
    """推广调整顾问：基于分析结果给出具体操作建议"""

    def __init__(self):
        self.rules = CONFIG['promotion_rules']

    def generate_plan(self, monitor_result: Dict, promotion_result: Dict) -> Dict:
        plan = {
            '生成时间': datetime.now().isoformat(),
            '紧急操作': [],
            '优化建议': [],
            '预算调整': [],
            '出价策略': [],
            '活动操作': [],
        }

        alerts = monitor_result.get('alerts', [])

        # 1. 紧急操作
        for alert in alerts:
            if alert.get('severity') in ('critical', 'high'):
                plan['紧急操作'].append({
                    '优先级': 'P0' if alert['severity'] == 'critical' else 'P1',
                    '操作': alert.get('suggestion', ''),
                    '原因': alert.get('message', ''),
                })

        # 2. 推广调整建议
        suggestions = promotion_result.get('调整建议', [])
        for s in suggestions:
            if s['action'] == '降低出价':
                plan['出价策略'].append({
                    '操作': f'降低出价{self.rules["bid_adjust_step"]*100:.0f}%',
                    '原因': s['reason'],
                    '执行方式': '在推广后台批量调整出价',
                })
            elif s['action'] == '加大投放':
                plan['出价策略'].append({
                    '操作': f'提高出价{self.rules["bid_adjust_step"]*100:.0f}%',
                    '原因': s['reason'],
                    '执行方式': '在推广后台批量调整出价',
                })
            elif s['action'] == '优化亏损时段':
                plan['预算调整'].append({
                    '操作': '暂停或降低亏损时段预算',
                    '原因': s['reason'],
                    '执行方式': '分时段投放设置中调整',
                })
            elif s['action'] == '扩大高效时段':
                plan['预算调整'].append({
                    '操作': '增加高效时段预算',
                    '原因': s['reason'],
                    '执行方式': '分时段投放设置中调整',
                })

        # 3. 活动操作
        analysis = monitor_result.get('analysis', {})
        for risk in analysis.get('活动风险', []):
            if risk.get('type') == 'activity_expiring':
                plan['活动操作'].append({
                    '操作': '续期即将到期活动',
                    '原因': risk['message'],
                    '执行方式': '在单品宝后台续期',
                })
            elif risk.get('type') == 'activity_expired':
                plan['活动操作'].append({
                    '操作': '创建新活动替代过期活动',
                    '原因': risk['message'],
                    '执行方式': '在单品宝后台新建活动',
                })

        # 4. 综合优化建议
        overall_roi = promotion_result.get('整体ROI', {})
        if overall_roi:
            roi = overall_roi.get('ROI', 0)
            spend = overall_roi.get('总花费', 0)
            if roi > 0:
                # 计算最优预算分配
                target_spend = min(
                    spend * (self.rules['target_roi'] / max(roi, 1)),
                    self.rules['max_daily_spend']
                )
                plan['优化建议'].append({
                    '建议': f'目标日预算调整为{target_spend:.0f}元',
                    '依据': f'当前ROI={roi:.2f}，目标ROI={self.rules["target_roi"]}',
                })

        return plan

    def save_plan(self, plan: Dict) -> str:
        plan_file = Path(__file__).parent.parent / 'alerts' / f'plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        return str(plan_file)

    def print_plan(self, plan: Dict):
        print(f'\n{"="*60}')
        print(f'  推广调整方案 | {plan["生成时间"]}')
        print(f'{"="*60}')

        if plan['紧急操作']:
            print('\n  [紧急操作]')
            for op in plan['紧急操作']:
                print(f"    {op['优先级']} | {op['操作']}")
                print(f"         原因: {op['原因']}")

        if plan['出价策略']:
            print('\n  [出价策略]')
            for op in plan['出价策略']:
                print(f"    - {op['操作']}")
                print(f"      原因: {op['原因']}")

        if plan['预算调整']:
            print('\n  [预算调整]')
            for op in plan['预算调整']:
                print(f"    - {op['操作']}")
                print(f"      原因: {op['原因']}")

        if plan['活动操作']:
            print('\n  [活动操作]')
            for op in plan['活动操作']:
                print(f"    - {op['操作']}")
                print(f"      原因: {op['原因']}")

        if plan['优化建议']:
            print('\n  [优化建议]')
            for op in plan['优化建议']:
                print(f"    - {op['建议']}")

        print(f'\n{"="*60}\n')
