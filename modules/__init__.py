import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
ALERTS_DIR = BASE_DIR / 'alerts'
LOGS_DIR = BASE_DIR / 'logs'

DOWNLOADS_DIR = Path.home() / 'Downloads'
WANGWANG_DIR = Path.home() / 'My WangWang'

# Agent配置
CONFIG = {
    'agent_name': 'PDD运营监控Agent',
    'version': '1.0',
    'scan_interval_minutes': 60,
    'alert_webhook': None,
    'alert_thresholds': {
        'sales_decline_pct': -15,
        'roi_min': 3.0,
        'roi_max': 50.0,
        'spend_drop_pct': -30,
        'activity_expire_days': 7,
    },
    'promotion_rules': {
        'min_roi': 5.0,
        'target_roi': 10.0,
        'max_daily_spend': 500,
        'bid_adjust_step': 0.1,
    }
}

for d in [DATA_DIR, ALERTS_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)
