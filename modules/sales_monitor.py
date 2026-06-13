import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
from .config import CONFIG


class SalesMonitor:
    """销量下滑监控与原因分析"""

    def __init__(self):
        self.thresholds = CONFIG['alert_thresholds']

    def monitor(self, data: Dict[str, pd.DataFrame]) -> Dict:
        alerts = []
        analysis = {
            '直播花费趋势': None,
            'ROI异常': [],
            '活动风险': [],
            '停投风险': [],
            '综合诊断': [],
        }

        # 分析直播推广数据
        tian = data.get('zhibo_tian')
        if tian is not None and len(tian) > 0:
            analysis['直播花费趋势'] = self._analyze_spend_trend(tian)
            alerts.extend(self._check_spend_alerts(tian))

        # 分析分时ROI
        shi = data.get('zhibo_shi')
        if shi is not None and len(shi) > 0:
            analysis['ROI异常'] = self._analyze_roi(shi)
            alerts.extend(self._check_roi_alerts(shi))

        # 分析活动到期风险
        danpinbao = data.get('danpinbao')
        if danpinbao is not None:
            analysis['活动风险'] = self._check_activity_risk(danpinbao)
            alerts.extend(analysis['活动风险'])

        # 综合诊断
        analysis['综合诊断'] = self._diagnose(analysis)

        return {
            'alerts': alerts,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
            'severity': self._calc_severity(alerts)
        }

    def _analyze_spend_trend(self, df: pd.DataFrame) -> Dict:
        cols = df.columns.tolist()
        date_col = self._find_col(cols, ['日期', 'date'])
        spend_col = self._find_col(cols, ['花费', '消耗'])

        if not date_col or not spend_col:
            return {}

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(date_col)

        spend = pd.to_numeric(df[spend_col], errors='coerce')
        recent_7 = spend.tail(7).mean()
        prev_7 = spend.iloc[-14:-7].mean() if len(spend) >= 14 else None

        result = {
            '最近7日均花费': round(recent_7, 2),
            '前7日均花费': round(prev_7, 2) if prev_7 else None,
            '环比变化': round((recent_7 - prev_7) / prev_7 * 100, 1) if prev_7 and prev_7 > 0 else None,
            '日花费列表': spend.tail(14).tolist()
        }

        # 停投检测
        last_spend = spend.iloc[-1] if len(spend) > 0 else 0
        if last_spend == 0:
            zero_days = 0
            for s in reversed(spend.tolist()):
                if s == 0:
                    zero_days += 1
                else:
                    break
            result['停投天数'] = zero_days

        return result

    def _check_spend_alerts(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        cols = df.columns.tolist()
        spend_col = self._find_col(cols, ['花费', '消耗'])
        if not spend_col:
            return alerts

        spend = pd.to_numeric(df[spend_col], errors='coerce')
        recent_7 = spend.tail(7).mean()
        prev_7 = spend.iloc[-14:-7].mean() if len(spend) >= 14 else None

        if prev_7 and prev_7 > 0:
            change = (recent_7 - prev_7) / prev_7 * 100
            if change < self.thresholds['spend_drop_pct']:
                alerts.append({
                    'type': 'spend_decline',
                    'severity': 'high',
                    'message': f'直播推广花费下降{abs(change):.1f}%，可能影响曝光和销量',
                    'detail': f'前7日均{prev_7:.2f}元 -> 最近7日均{recent_7:.2f}元',
                    'suggestion': '检查投放计划，增加预算或调整出价'
                })

        # 连续0花费检测
        last_spend = spend.iloc[-1] if len(spend) > 0 else 0
        if last_spend == 0:
            zero_days = 0
            for s in reversed(spend.tolist()):
                if s == 0:
                    zero_days += 1
                else:
                    break
            if zero_days >= 2:
                alerts.append({
                    'type': 'no_spend',
                    'severity': 'critical',
                    'message': f'已连续{zero_days}天未投放直播推广',
                    'suggestion': '立即检查投放状态，恢复推广'
                })

        return alerts

    def _analyze_roi(self, df: pd.DataFrame) -> List[Dict]:
        cols = df.columns.tolist()
        roi_col = self._find_col(cols, ['ROI', '投产'])
        if not roi_col:
            return []

        roi = pd.to_numeric(df[roi_col], errors='coerce').dropna()
        if len(roi) == 0:
            return []

        return [{
            '平均ROI': round(roi.mean(), 2),
            '最高ROI': round(roi.max(), 2),
            '最低ROI': round(roi.min(), 2),
            '中位数ROI': round(roi.median(), 2),
            'ROI<3占比': round((roi < 3).sum() / len(roi) * 100, 1),
            'ROI>20占比': round((roi > 20).sum() / len(roi) * 100, 1),
        }]

    def _check_roi_alerts(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        cols = df.columns.tolist()
        roi_col = self._find_col(cols, ['ROI', '投产'])
        if not roi_col:
            return alerts

        roi = pd.to_numeric(df[roi_col], errors='coerce').dropna()
        if len(roi) == 0:
            return alerts

        low_roi = (roi < self.thresholds['roi_min']).sum()
        if low_roi > 0:
            alerts.append({
                'type': 'low_roi',
                'severity': 'medium',
                'message': f'{low_roi}个时段ROI低于{self.thresholds["roi_min"]}，存在亏损风险',
                'suggestion': '降低低ROI时段出价，提高高ROI时段预算'
            })

        high_roi = (roi > self.thresholds['roi_max']).sum()
        if high_roi > 0:
            alerts.append({
                'type': 'high_roi',
                'severity': 'info',
                'message': f'{high_roi}个时段ROI超过{self.thresholds["roi_max"]}，可加大投放',
                'suggestion': '适当提高出价，扩大曝光'
            })

        return alerts

    def _check_activity_risk(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        cols = df.columns.tolist()
        end_col = self._find_col(cols, ['活动结束'])
        act_id = self._find_col(cols, ['活动ID'])
        status_col = self._find_col(cols, ['活动状态'])

        if not end_col:
            return alerts

        df = df.copy()
        df[end_col] = pd.to_datetime(df[end_col], errors='coerce')
        now = pd.Timestamp.now()

        # 即将到期
        expiring = df[df[end_col].between(now, now + pd.Timedelta(days=7))]
        if len(expiring) > 0 and act_id:
            ids = expiring[act_id].unique()
            alerts.append({
                'type': 'activity_expiring',
                'severity': 'high',
                'message': f'{len(ids)}个活动将在7天内到期',
                'detail': f'活动ID: {", ".join(str(i) for i in ids[:5])}',
                'suggestion': '及时续期或创建新活动，避免活动到期导致流量下降'
            })

        # 已过期
        expired = df[df[end_col] < now]
        if len(expired) > 0 and act_id:
            ids = expired[act_id].unique()
            alerts.append({
                'type': 'activity_expired',
                'severity': 'critical',
                'message': f'{len(ids)}个活动已过期',
                'detail': f'活动ID: {", ".join(str(i) for i in ids[:5])}',
                'suggestion': '立即续期或创建替代活动'
            })

        return alerts

    def _diagnose(self, analysis: Dict) -> List[str]:
        diagnosis = []
        spend = analysis.get('直播花费趋势', {})
        if spend:
            if spend.get('停投天数', 0) >= 2:
                diagnosis.append('[严重] 直播推广已停投，流量和销量必然下滑')
            elif spend.get('环比变化') and spend['环比变化'] < -30:
                diagnosis.append('[警告] 推广花费大幅下降，曝光减少可能导致销量下滑')

        roi_data = analysis.get('ROI异常', [{}])
        if roi_data:
            r = roi_data[0]
            if r.get('ROI<3占比', 0) > 30:
                diagnosis.append('[警告] 超过30%时段ROI<3，整体推广效率偏低')
            if r.get('ROI>20占比', 0) > 20:
                diagnosis.append('[建议] 多个时段ROI>20，存在放量空间')

        act_risks = analysis.get('活动风险', [])
        if any(a.get('type') == 'activity_expired' for a in act_risks):
            diagnosis.append('[严重] 有活动已过期，商品恢复原价，转化率和销量将下降')

        return diagnosis

    def _calc_severity(self, alerts: List[Dict]) -> str:
        severities = [a.get('severity', 'info') for a in alerts]
        if 'critical' in severities:
            return 'critical'
        if 'high' in severities:
            return 'high'
        if 'medium' in severities:
            return 'medium'
        return 'low'

    def _find_col(self, cols, keywords, exclude=None):
        for c in cols:
            cl = str(c)
            if any(kw in cl for kw in keywords) and (exclude is None or exclude not in cl):
                return c
        return None
