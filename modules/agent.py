import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict
from .data_collector import DataCollector
from .activity_analyzer import ActivityAnalyzer
from .sales_monitor import SalesMonitor
from .promotion_analyzer import PromotionAnalyzer
from .alert_manager import AlertManager
from .adjustment_advisor import AdjustmentAdvisor
from .config import CONFIG

LOGS_DIR = Path(__file__).parent.parent / 'logs'


class PDDAgent:
    """拼多多运营监控Agent主程序"""

    def __init__(self):
        self.collector = DataCollector()
        self.activity_analyzer = ActivityAnalyzer()
        self.sales_monitor = SalesMonitor()
        self.promo_analyzer = PromotionAnalyzer()
        self.alert_manager = AlertManager()
        self.advisor = AdjustmentAdvisor()

    def run_once(self) -> Dict:
        """执行一次完整分析"""
        print(f'\n{"="*60}')
        print(f'  {CONFIG["agent_name"]} v{CONFIG["version"]}')
        print(f'  执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'{"="*60}')

        # 1. 数据收集
        print('\n[1/5] 收集数据...')
        collected = self.collector.collect_all()
        data = collected['excel']
        print(f'  Excel文件: {sum(1 for v in data.values() for _ in [1])}类')
        for k, v in data.items():
            print(f'    {k}: {len(v)}条记录')

        # 2. 活动分析
        print('\n[2/5] 分析竞品活动...')
        activity_result = self.activity_analyzer.analyze(data)
        self._print_activity_summary(activity_result)

        # 3. 销量监控
        print('\n[3/5] 监控销量下滑...')
        monitor_result = self.sales_monitor.monitor(data)

        # 4. 推广分析
        print('\n[4/5] 分析付费推广ROI...')
        promo_result = self.promo_analyzer.analyze(data)
        self._print_promo_summary(promo_result)

        # 5. 告警处理
        print('\n[5/5] 处理告警...')
        self.alert_manager.process_alerts(monitor_result)

        # 6. 生成调整方案
        plan = self.advisor.generate_plan(monitor_result, promo_result)
        self.advisor.print_plan(plan)
        plan_file = self.advisor.save_plan(plan)

        # 保存日志
        self._save_log({
            'timestamp': datetime.now().isoformat(),
            'activity_summary': len(activity_result.get('活动总览', [])),
            'alerts': len(monitor_result.get('alerts', [])),
            'severity': monitor_result.get('severity'),
            'plan_file': plan_file,
        })

        return {
            'activity': activity_result,
            'monitor': monitor_result,
            'promotion': promo_result,
            'plan': plan,
        }

    def run_loop(self):
        """持续监控模式"""
        interval = CONFIG['scan_interval_minutes'] * 60
        print(f'\n  启动持续监控模式，间隔 {CONFIG["scan_interval_minutes"]} 分钟')
        print(f'  按 Ctrl+C 停止\n')

        while True:
            try:
                self.run_once()
                print(f'\n  下次执行: {datetime.now().timestamp() + interval:.0f}')
                time.sleep(interval)
            except KeyboardInterrupt:
                print('\n  监控已停止')
                break
            except Exception as e:
                print(f'\n  [错误] {e}')
                time.sleep(60)

    def _print_activity_summary(self, result: Dict):
        activities = result.get('活动总览', [])
        if activities:
            print(f'  共{len(activities)}个活动:')
            for a in activities[:5]:
                name = a.get('活动名称', 'N/A')
                skus = a.get('SKU数量', 0)
                disc = a.get('折扣率', 'N/A')
                print(f'    {name}: {skus}个SKU, 折扣{disc}%')

        expiring = result.get('即将到期活动', [])
        if expiring:
            print(f'  [!] {len(expiring)}个活动即将到期')

    def _print_promo_summary(self, result: Dict):
        overall = result.get('整体ROI')
        if overall:
            print(f'  总花费: CNY {overall["总花费"]}')
            print(f'  总成交: CNY {overall["总成交"]}')
            print(f'  整体ROI: {overall["ROI"]}')

        eff = result.get('花费效率', {})
        if eff:
            print(f'  点击率: {eff.get("点击率", "N/A")}%')
            print(f'  千次曝光成本: CNY {eff.get("千次曝光花费", "N/A")}')

    def _save_log(self, log: Dict):
        LOGS_DIR.mkdir(exist_ok=True)
        log_file = LOGS_DIR / f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
