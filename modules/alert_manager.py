import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

ALERTS_DIR = Path(__file__).parent.parent / 'alerts'


class AlertManager:
    """告警管理器"""

    def __init__(self):
        ALERTS_DIR.mkdir(exist_ok=True)

    def process_alerts(self, monitor_result: Dict) -> List[Dict]:
        alerts = monitor_result.get('alerts', [])
        severity = monitor_result.get('severity', 'low')

        if not alerts:
            return []

        # 保存告警记录
        alert_record = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'alert_count': len(alerts),
            'alerts': alerts,
        }

        alert_file = ALERTS_DIR / f'alert_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert_record, f, ensure_ascii=False, indent=2)

        # 控制台输出
        self._print_alerts(alerts, severity)

        return alerts

    def _print_alerts(self, alerts: List[Dict], severity: str):
        icons = {
            'critical': '[!!!]',
            'high': '[!! ]',
            'medium': '[!  ]',
            'info': '[i  ]',
        }

        severity_label = {
            'critical': '严重',
            'high': '高',
            'medium': '中',
            'low': '低',
            'info': '信息',
        }

        print(f'\n{"="*60}')
        print(f'  告警通知 | 级别: {severity_label.get(severity, severity)} | 共{len(alerts)}条')
        print(f'{"="*60}')

        for i, alert in enumerate(alerts, 1):
            icon = icons.get(alert.get('severity', 'info'), '[  ]')
            print(f'\n  {icon} [{i}] {alert.get("message", "")}')
            if alert.get('detail'):
                print(f'       详情: {alert["detail"]}')
            if alert.get('suggestion'):
                print(f'       建议: {alert["suggestion"]}')

        print(f'\n{"="*60}\n')

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """获取最近N小时的告警"""
        cutoff = datetime.now().timestamp() - hours * 3600
        alerts = []
        for f in sorted(ALERTS_DIR.glob('alert_*.json'), reverse=True):
            if f.stat().st_mtime < cutoff:
                break
            with open(f, 'r', encoding='utf-8') as fp:
                alerts.append(json.load(fp))
        return alerts

    def clear_old_alerts(self, days: int = 30):
        """清理过期告警"""
        cutoff = datetime.now().timestamp() - days * 86400
        for f in ALERTS_DIR.glob('alert_*.json'):
            if f.stat().st_mtime < cutoff:
                f.unlink()
