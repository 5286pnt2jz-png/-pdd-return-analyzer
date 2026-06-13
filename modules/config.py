CONFIG = {
    'agent_name': 'PDD运营监控Agent',
    'version': '1.0',
    'scan_interval_minutes': 60,
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
