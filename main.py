import sys
import argparse
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'
captured_data = []


class AgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/api/health', '/api/status'):
            self._json_response(200, {"status": "running"})
        elif self.path == '/api/data/list':
            self._json_response(200, {"data": captured_data[-50:]})
        elif self.path == '/return_analysis':
            html_path = Path(__file__).parent / 'templates' / 'return_analysis.html'
            if html_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_path.read_bytes())
            else:
                self._json_response(404, {"error": "页面不存在"})
        elif self.path == '/' or self.path == '/index.html':
            html_path = Path(__file__).parent / 'website' / 'index.html'
            if html_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_path.read_bytes())
            else:
                self._json_response(404, {"error": "页面不存在"})
        elif self.path.startswith('/download/'):
            file_name = self.path.split('/download/', 1)[1]
            file_path = Path(__file__).parent / 'website' / 'download' / file_name
            if file_path.exists():
                self.send_response(200)
                if file_name.endswith('.exe'):
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{file_name}"')
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self._json_response(404, {"error": "文件不存在"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/data':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                captured_data.append(data)
                if len(captured_data) > 500:
                    captured_data[:] = captured_data[-500:]
                DATA_DIR.mkdir(exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                with open(DATA_DIR / f'capture_{ts}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._json_response(200, {"status": "ok"})
            except Exception as e:
                self._json_response(400, {"error": str(e)})
        elif self.path == '/api/return/save':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            return_dir = DATA_DIR / 'returns'
            return_dir.mkdir(exist_ok=True)
            with open(return_dir / f'return_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._json_response(200, {"status": "ok"})
        elif self.path == '/api/return/analyze':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            params = json.loads(body)
            result = self._analyze_returns(params)
            self._json_response(200, result)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _json_response(self, code, obj):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False, indent=2).encode())

    def _analyze_returns(self, params):
        goods_id = params.get('goods_id', '')
        date_start = params.get('date_start', '')
        date_end = params.get('date_end', '')

        if not goods_id:
            return {"error": "请输入商品链接或ID"}

        import re
        m = re.search(r'(\d+)', goods_id)
        if m:
            goods_id = m.group(1)

        return_dir = DATA_DIR / 'returns'
        return_dir.mkdir(exist_ok=True)

        orders = []
        chats = []

        orders_file = return_dir / f'orders_{goods_id}.json'
        chats_file = return_dir / f'chats_{goods_id}.json'

        if orders_file.exists():
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders = json.load(f)
        if chats_file.exists():
            with open(chats_file, 'r', encoding='utf-8') as f:
                chats = json.load(f)

        if not orders:
            for f in return_dir.glob('return_*.json'):
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        d = json.load(fp)
                        if d.get('orders'):
                            orders.extend(d['orders'])
                        if d.get('chats'):
                            chats.extend(d['chats'])
                except:
                    pass

        if not chats:
            import re as _re
            for order in orders:
                raw = order.get('raw', {})
                note = raw.get('备注', '') or raw.get('客服备注', '') or raw.get('售后备注', '')
                if note and len(note) > 10:
                    cat = '其他'
                    if _re.search(r'质量|破损|瑕疵|污渍|线头|抽丝|起球|脱线|开裂|鼓包|勾丝|起泡|褪色', note):
                        cat = '质量问题'
                    elif _re.search(r'尺码|偏大|偏小|大小|不合适|尺码', note):
                        cat = '尺寸问题'
                    elif _re.search(r'物流|快递|发货|配送', note):
                        cat = '物流问题'
                    elif _re.search(r'颜色|色差|描述|不符|图片|款式', note):
                        cat = '与描述不符'
                    elif _re.search(r'不喜欢|不想要|买错', note):
                        cat = '不想要'

                    clean = note.replace('\\', '/').replace(';', '；')
                    parts = [p.strip() for p in clean.split('/') if p.strip() and len(p.strip()) > 3]
                    feedback = '；'.join(parts[-3:]) if parts else note[:200]

                    chats.append({
                        'message': feedback[:300],
                        'buyer': order.get('buyer', '买家'),
                        'time': raw.get('申请时间', '') or order.get('time', ''),
                        'category': cat
                    })

        if not orders:
            return {
                "goods_id": goods_id,
                "date_range": f"{date_start}~{date_end}",
                "total_orders": 0, "total_amount": 0, "return_rate": 0,
                "orders": [], "chats": [],
                "reasons": [
                    {"reason": "商品质量问题", "count": 0},
                    {"reason": "尺寸/颜色不符", "count": 0},
                    {"reason": "物流问题", "count": 0},
                    {"reason": "与描述不符", "count": 0},
                    {"reason": "不喜欢/不想要", "count": 0}
                ],
                "suggestions": [
                    {"title": "暂无数据", "detail": "请在商家后台打开退货订单页面，让插件采集数据后再分析"},
                    {"title": "如何采集", "detail": "打开 mms.pinduoduo.com → 交易 → 退款管理 → 选择商品和时间 → 插件自动采集"}
                ]
            }

        reason_counts = {}
        for order in orders:
            reason = order.get('reason', '其他原因')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        reasons = [{"reason": k, "count": v} for k, v in sorted(reason_counts.items(), key=lambda x: -x[1])]

        total_amount = sum(float(o.get('amount', 0)) for o in orders)

        chat_categories = {}
        for chat in chats:
            cat = chat.get('category', '其他')
            chat_categories[cat] = chat_categories.get(cat, 0) + 1

        suggestions = []
        for cat, count in sorted(chat_categories.items(), key=lambda x: -x[1])[:3]:
            if cat == '质量问题':
                suggestions.append({"title": "提升商品质量", "detail": f"共{count}条反馈涉及质量问题，建议加强品控"})
            elif cat == '尺寸问题':
                suggestions.append({"title": "优化尺码说明", "detail": f"共{count}条反馈涉及尺寸，建议完善尺码表"})
            elif cat == '物流问题':
                suggestions.append({"title": "改善物流体验", "detail": f"共{count}条反馈涉及物流，建议更换物流商"})
            elif cat == '与描述不符':
                suggestions.append({"title": "完善商品描述", "detail": f"共{count}条反馈与描述不符，建议实拍图片"})

        if not suggestions:
            suggestions.append({"title": "数据充足", "detail": "建议定期分析退货趋势，持续优化商品和服务"})

        return {
            "goods_id": goods_id,
            "date_range": f"{date_start}~{date_end}",
            "total_orders": len(orders),
            "total_amount": round(total_amount, 2),
            "return_rate": round(len(orders) / max(len(orders) * 5, 1) * 100, 1) if orders else 0,
            "orders": orders,
            "chats": chats,
            "reasons": reasons if reasons else [
                {"reason": "商品质量问题", "count": 0},
                {"reason": "尺寸/颜色不符", "count": 0},
                {"reason": "物流问题", "count": 0}
            ],
            "suggestions": suggestions
        }

    def log_message(self, format, *args):
        pass


def start_server(port=8765):
    server = HTTPServer(('0.0.0.0', port), AgentHandler)
    print(f'[Agent] http://127.0.0.1:{port}')
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='PDD Agent')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()

    print(f'{"="*50}')
    print(f'  PDD Agent 已启动')
    print(f'  首页下载: http://127.0.0.1:{args.port}')
    print(f'  竞品监控: 打开拼多多商品页自动抓取')
    print(f'  退货分析: http://127.0.0.1:{args.port}/return_analysis')
    print(f'{"="*50}')
    start_server(args.port)


if __name__ == '__main__':
    main()
