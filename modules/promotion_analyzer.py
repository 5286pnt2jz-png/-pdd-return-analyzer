import pandas as pd
from typing import Dict, List
from .config import CONFIG


class PromotionAnalyzer:
    """付费推广曝光ROI分析与调整建议"""

    def __init__(self):
        self.rules = CONFIG['promotion_rules']

    def analyze(self, data: Dict[str, pd.DataFrame]) -> Dict:
        result = {
            '整体ROI': None,
            '时段分析': [],
            '花费效率': {},
            '调整建议': [],
        }

        shi = data.get('zhibo_shi')
        if shi is None or len(shi) == 0:
            return result

        cols = shi.columns.tolist()
        roi_col = self._find_col(cols, ['ROI', '投产'])
        spend_col = self._find_col(cols, ['花费', '消耗'])
        gmv_col = self._find_col(cols, ['成交金额', 'GMV', '交易额'])
        exposure_col = self._find_col(cols, ['曝光', '展现'])
        click_col = self._find_col(cols, ['点击'])
        conv_col = self._find_col(cols, ['成交笔数', '订单数'])

        # 整体ROI
        if spend_col and gmv_col:
            total_spend = pd.to_numeric(shi[spend_col], errors='coerce').sum()
            total_gmv = pd.to_numeric(shi[gmv_col], errors='coerce').sum()
            if total_spend > 0:
                result['整体ROI'] = {
                    '总花费': round(total_spend, 2),
                    '总成交': round(total_gmv, 2),
                    'ROI': round(total_gmv / total_spend, 2),
                    '千次曝光成本': round(total_spend / max(pd.to_numeric(shi[exposure_col], errors='coerce').sum() / 1000, 1), 2) if exposure_col else None,
                }

        # 时段分析
        if roi_col:
            roi = pd.to_numeric(shi[roi_col], errors='coerce')
            for idx, val in roi.items():
                if pd.notna(val):
                    row = shi.iloc[idx]
                    entry = {
                        'ROI': round(val, 2),
                        '花费': round(float(row[spend_col]), 2) if spend_col and pd.notna(row.get(spend_col)) else 0,
                        '成交': round(float(row[gmv_col]), 2) if gmv_col and pd.notna(row.get(gmv_col)) else 0,
                    }
                    # 效率评级
                    if val >= self.rules['target_roi']:
                        entry['评级'] = '优秀'
                    elif val >= self.rules['min_roi']:
                        entry['评级'] = '良好'
                    elif val >= 3:
                        entry['评级'] = '一般'
                    else:
                        entry['评级'] = '亏损'
                    result['时段分析'].append(entry)

        # 花费效率分析
        if exposure_col and click_col and spend_col:
            exp = pd.to_numeric(shi[exposure_col], errors='coerce').sum()
            clk = pd.to_numeric(shi[click_col], errors='coerce').sum()
            spd = pd.to_numeric(shi[spend_col], errors='coerce').sum()
            if exp > 0:
                result['花费效率'] = {
                    '总曝光': int(exp),
                    '总点击': int(clk),
                    '点击率': round(clk / exp * 100, 2),
                    '平均点击花费': round(spd / max(clk, 1), 2),
                    '千次曝光花费': round(spd / max(exp / 1000, 1), 2),
                }

        # 调整建议
        result['调整建议'] = self._generate_suggestions(result)

        return result

    def _generate_suggestions(self, analysis: Dict) -> List[Dict]:
        suggestions = []
        overall = analysis.get('整体ROI')
        if overall:
            roi = overall['ROI']
            if roi < self.rules['min_roi']:
                suggestions.append({
                    'action': '降低出价',
                    'reason': f'整体ROI({roi:.2f})低于目标({self.rules["min_roi"]})',
                    'detail': f'建议降低出价{self.rules["bid_adjust_step"]*100:.0f}%，优化人群定向',
                })
            elif roi >= self.rules['target_roi']:
                suggestions.append({
                    'action': '加大投放',
                    'reason': f'整体ROI({roi:.2f})超过目标({self.rules["target_roi"]})',
                    'detail': f'建议提高出价{self.rules["bid_adjust_step"]*100:.0f}%，扩大曝光量',
                })
            else:
                suggestions.append({
                    'action': '维持现状',
                    'reason': f'整体ROI({roi:.2f})在目标范围内',
                    'detail': '当前投放效率良好，保持现有策略',
                })

        # 检查亏损时段
        loss_periods = [p for p in analysis.get('时段分析', []) if p.get('评级') == '亏损']
        if loss_periods:
            suggestions.append({
                'action': '优化亏损时段',
                'reason': f'{len(loss_periods)}个时段ROI<3',
                'detail': '建议降低亏损时段出价或暂停投放，将预算转移到高ROI时段',
            })

        # 检查高效时段
        best_periods = [p for p in analysis.get('时段分析', []) if p.get('评级') == '优秀']
        if best_periods:
            suggestions.append({
                'action': '扩大高效时段',
                'reason': f'{len(best_periods)}个时段ROI>={self.rules["target_roi"]}',
                'detail': '建议增加高效时段预算，抢占更多流量',
            })

        return suggestions

    def _find_col(self, cols, keywords):
        for c in cols:
            cl = str(c)
            if any(kw in cl for kw in keywords):
                return c
        return None
