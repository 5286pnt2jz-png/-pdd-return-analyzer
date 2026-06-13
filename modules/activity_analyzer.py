import pandas as pd
from typing import Dict, List
from datetime import datetime


class ActivityAnalyzer:
    """竞品活动ID明细分析器"""

    def analyze(self, data: Dict[str, pd.DataFrame]) -> Dict:
        result = {
            '活动总览': [],
            '活动价格策略': [],
            '即将到期活动': [],
            '竞品活动对比': [],
        }

        df = data.get('danpinbao')
        if df is None or len(df) == 0:
            return result

        cols = df.columns.tolist()
        act_id = self._find_col(cols, '活动ID')
        act_tag = self._find_col(cols, '活动标签')
        act_name = self._find_col(cols, '活动名称')
        act_status = self._find_col(cols, '活动状态')
        start_col = self._find_col(cols, '活动开始')
        end_col = self._find_col(cols, '活动结束')
        price_col = self._find_col(cols, '价格', exclude='优惠后')
        disc_col = self._find_col(cols, '优惠后价格')
        prod_col = self._find_col(cols, '商品ID')
        prod_name = self._find_col(cols, '商品名称')

        # 1. 活动总览
        if act_id:
            group = [c for c in [act_id, act_tag, act_name, act_status, start_col, end_col] if c]
            summary = df.groupby(group).agg(
                SKU数量=(act_id, 'count'),
            ).reset_index()

            if price_col and disc_col:
                ps = df.groupby(act_id).agg(
                    原价均值=(price_col, 'mean'),
                    活动价均值=(disc_col, 'mean'),
                ).reset_index()
                summary = summary.merge(ps, on=act_id, how='left')
                summary['折扣率'] = (summary['活动价均值'] / summary['原价均值'] * 100).round(1)
                summary['让利幅度'] = (summary['原价均值'] - summary['活动价均值']).round(1)

            result['活动总览'] = summary.to_dict('records')

        # 2. 即将到期活动
        if end_col:
            df[end_col] = pd.to_datetime(df[end_col], errors='coerce')
            now = pd.Timestamp.now()
            upcoming = df[df[end_col].between(now, now + pd.Timedelta(days=7))]
            if len(upcoming) > 0 and act_id:
                expire_list = upcoming.groupby(act_id).agg(
                    结束时间=(end_col, 'min'),
                    涉及SKU数=(act_id, 'count')
                ).reset_index()
                result['即将到期活动'] = expire_list.to_dict('records')

        # 3. 价格策略分析
        if price_col and disc_col and act_id:
            strategy = df.groupby(act_id).agg(
                最高价=(price_col, 'max'),
                最低价=(price_col, 'min'),
                活动最高价=(disc_col, 'max'),
                活动最低价=(disc_col, 'min'),
                SKU数=(act_id, 'count'),
            ).reset_index()
            strategy['价差幅度'] = (strategy['最高价'] - strategy['最低价']).round(1)
            result['活动价格策略'] = strategy.to_dict('records')

        return result

    def get_activity_detail(self, data: Dict, activity_id: str) -> Dict:
        """获取指定活动的SKU明细"""
        df = data.get('danpinbao')
        if df is None:
            return {}
        cols = df.columns.tolist()
        act_id = self._find_col(cols, '活动ID')
        if not act_id:
            return {}
        detail = df[df[act_id].astype(str) == str(activity_id)]
        return detail.to_dict('records')

    def _find_col(self, cols, keyword, exclude=None):
        for c in cols:
            cl = str(c)
            if keyword in cl and (exclude is None or exclude not in cl):
                return c
        return None
