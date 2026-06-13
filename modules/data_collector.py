import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from .config import CONFIG

DATA_DIR = Path(__file__).parent.parent / 'data'


class DataCollector:
    """数据收集器：从Excel和Chrome插件两个来源采集数据"""

    FILE_PATTERNS = {
        'danpinbao': ['单品宝'],
        'baoming': ['报名记录'],
        'zhibo_tian': ['直播推广', '分天数据'],
        'zhibo_shi': ['直播推广', '分时数据'],
        'shangpin': ['导出商品编码'],
        'shengyi': ['生意参谋'],
    }

    def __init__(self):
        self.downloads = Path.home() / 'Downloads'
        self.wangwang = Path.home() / 'My WangWang'
        self.chrome_data = DATA_DIR / 'chrome_captured'
        self.chrome_data.mkdir(exist_ok=True)
        self.collected = {}

    def scan_excel_files(self) -> Dict[str, List[Path]]:
        """扫描所有数据源目录的Excel文件"""
        result = {}
        for search_dir in [self.downloads, self.wangwang]:
            if not search_dir.exists():
                continue
            for f in search_dir.iterdir():
                if f.suffix.lower() not in ('.xlsx', '.xls') or f.name.startswith('~'):
                    continue
                ftype = self._classify(f.name)
                if ftype not in result:
                    result[ftype] = []
                result[ftype].append(f)
        return result

    def _classify(self, filename: str) -> str:
        for ftype, keywords in self.FILE_PATTERNS.items():
            if all(kw in filename for kw in keywords):
                return ftype
        return 'other'

    def load_excel_data(self) -> Dict[str, pd.DataFrame]:
        """加载所有Excel数据"""
        files = self.scan_excel_files()
        data = {}
        for ftype, file_list in files.items():
            dfs = []
            for f in sorted(file_list):
                try:
                    if f.suffix.lower() == '.xls':
                        df = pd.read_excel(f, engine='xlrd')
                    else:
                        df = pd.read_excel(f)
                    df = df.dropna(how='all')
                    if len(df) > 0:
                        df['_file'] = f.name
                        df['_date'] = datetime.fromtimestamp(f.stat().st_mtime)
                        dfs.append(df)
                except Exception:
                    pass
            if dfs:
                data[ftype] = pd.concat(dfs, ignore_index=True)
        self.collected = data
        return data

    def load_chrome_data(self) -> List[Dict]:
        """加载Chrome插件抓取的数据"""
        result = []
        for f in self.chrome_data.glob('*.json'):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    result.append(json.load(fp))
            except Exception:
                pass
        return result

    def save_snapshot(self, data: Dict):
        """保存数据快照，用于历史对比"""
        snapshot = {}
        for key, df in data.items():
            if isinstance(df, pd.DataFrame):
                snapshot[key] = {
                    'rows': len(df),
                    'columns': list(df.columns),
                    'timestamp': datetime.now().isoformat()
                }
        snap_file = DATA_DIR / f'snapshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(snap_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        return snap_file

    def get_latest_snapshot(self) -> Optional[Dict]:
        """获取最近一次快照"""
        snaps = sorted(DATA_DIR.glob('snapshot_*.json'), reverse=True)
        if len(snaps) < 2:
            return None
        with open(snaps[0], 'r', encoding='utf-8') as f:
            return json.load(f)

    def collect_all(self) -> Dict:
        """执行完整数据收集"""
        excel_data = self.load_excel_data()
        chrome_data = self.load_chrome_data()
        snapshot = self.save_snapshot(excel_data)
        return {
            'excel': excel_data,
            'chrome': chrome_data,
            'snapshot': str(snapshot),
            'timestamp': datetime.now().isoformat()
        }
