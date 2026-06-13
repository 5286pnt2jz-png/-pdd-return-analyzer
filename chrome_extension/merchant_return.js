(function() {
  if (!window.location.href.includes('mms.pinduoduo.com')) return;

  const style = document.createElement('style');
  style.textContent = `
    #pdd-rc-panel {
      position: fixed; bottom: 20px; right: 20px; z-index: 99999;
      background: #fff; border-radius: 16px; width: 380px;
      box-shadow: 0 4px 30px rgba(0,0,0,0.15);
      font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
      font-size: 13px; color: #1d1d1f;
    }
    .rc-header {
      padding: 14px 18px; background: linear-gradient(135deg, #6c5ce7, #a29bfe);
      border-radius: 16px 16px 0 0; display: flex; align-items: center; gap: 10px;
    }
    .rc-header-icon {
      width: 32px; height: 32px; border-radius: 8px; background: rgba(255,255,255,0.2);
      display: flex; align-items: center; justify-content: center;
      color: white; font-size: 16px; font-weight: 700;
    }
    .rc-header-text { flex: 1; }
    .rc-header-title { color: #fff; font-size: 14px; font-weight: 600; }
    .rc-header-sub { color: rgba(255,255,255,0.7); font-size: 11px; }
    .rc-close {
      width: 28px; height: 28px; border-radius: 8px; background: rgba(255,255,255,0.2);
      border: none; color: white; font-size: 16px; cursor: pointer;
    }
    .rc-body { padding: 14px 18px; }
    .rc-status {
      padding: 10px 14px; border-radius: 10px; font-size: 12px; margin-bottom: 10px;
    }
    .rc-status.info { background: #e3f2fd; color: #1565c0; }
    .rc-status.success { background: #e8f5e9; color: #2e7d32; }
    .rc-status.warn { background: #fff8e1; color: #f57f17; }
    .rc-btn {
      width: 100%; padding: 10px; border: none; border-radius: 10px;
      font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit;
    }
    .rc-btn-primary { background: #6c5ce7; color: white; margin-bottom: 8px; }
    .rc-btn-primary:hover { background: #5b4cdb; }
    .rc-btn-success { background: #27ae60; color: white; margin-bottom: 8px; }
    .rc-btn-secondary { background: #f2f2f7; color: #1d1d1f; }
    .rc-tip {
      font-size: 11px; color: #86868b; line-height: 1.5; margin-top: 8px;
      padding: 8px 10px; background: #f8f9fa; border-radius: 8px;
    }
  `;
  document.head.appendChild(style);

  const panel = document.createElement('div');
  panel.id = 'pdd-rc-panel';
  panel.innerHTML = `
    <div class="rc-header">
      <div class="rc-header-icon">R</div>
      <div class="rc-header-text">
        <div class="rc-header-title">退货数据采集</div>
        <div class="rc-header-sub" id="rc-sub">自动采集退货订单</div>
      </div>
      <button class="rc-close" id="rc-close">×</button>
    </div>
    <div class="rc-body">
      <div class="rc-status info" id="rc-status">
        打开「售后管理 → 售后工作台」后点击采集
      </div>
      <button class="rc-btn rc-btn-primary" id="rc-collect">采集当前页面数据</button>
      <button class="rc-btn rc-btn-success" id="rc-export">保存到分析系统</button>
      <div class="rc-tip">
        <b>操作步骤：</b><br>
        1. 左侧菜单 → 售后管理 → 售后工作台<br>
        2. 筛选商品ID和时间范围<br>
        3. 点击"采集当前页面数据"<br>
        4. 点击"保存到分析系统"
      </div>
    </div>
  `;
  document.body.appendChild(panel);

  document.getElementById('rc-close').onclick = () => { panel.style.display = 'none'; };

  let collectedOrders = [];

  document.getElementById('rc-collect').onclick = function() {
    const statusEl = document.getElementById('rc-status');
    statusEl.className = 'rc-status info';
    statusEl.textContent = '正在采集...';

    const results = [];

    const rows = document.querySelectorAll('tr, [class*="row"], [class*="item"]');
    rows.forEach(row => {
      const text = row.innerText || '';
      if (text.length < 20) return;

      const hasReturn = text.match(/退货|仅退款|退款退货|售后|退回|退货退款/);
      if (!hasReturn) return;

      const orderNo = (text.match(/订单编号[：:]\s*(\d[\d-]+)/) || text.match(/(\d{4,6}-\d{10,})/) || ['', ''])[1];
      const amount = (text.match(/(\d+\.?\d+)\s*元?/) || ['', ''])[1];
      const reason = (text.match(/原因[：:]\s*([^\s,，]+)/) || text.match(/退货原因[：:]\s*([^\s,，]+)/) || ['', ''])[1];
      const time = (text.match(/(\d{4}[-\/]\d{1,2}[-\/]\d{1,2}\s*\d{1,2}:\d{2})/) || ['', ''])[1];
      const status = (text.match(/(仅退款|退货退款|已退货|退货中|退款中|已完成)/) || ['', ''])[1];

      if (orderNo) {
        results.push({
          order_no: orderNo,
          amount: amount,
          reason: reason || '未填写',
          time: time,
          status: status,
          raw: text.slice(0, 200)
        });
      }
    });

    if (results.length === 0) {
      document.querySelectorAll('table').forEach(table => {
        const headerCells = table.querySelectorAll('th, .ant-table-thead th');
        const headers = Array.from(headerCells).map(h => h.innerText.trim());

        table.querySelectorAll('tbody tr, .ant-table-row').forEach(tr => {
          const cells = tr.querySelectorAll('td, .ant-table-cell');
          const rowText = Array.from(cells).map(c => c.innerText.trim()).join(' | ');

          if (rowText.match(/退货|退款|售后|退回/)) {
            const orderNo = (rowText.match(/(\d{4,6}-\d{10,})/) || ['', ''])[1];
            const amount = (rowText.match(/(\d+\.?\d+)/) || ['', ''])[1];

            const order = { order_no: orderNo, amount: amount, reason: '未填写', time: '', status: '', raw: rowText.slice(0, 200) };

            headers.forEach((h, i) => {
              const val = cells[i] ? cells[i].innerText.trim() : '';
              if (h.includes('原因')) order.reason = val || '未填写';
              if (h.includes('时间') || h.includes('日期')) order.time = val;
              if (h.includes('状态')) order.status = val;
            });

            if (orderNo) results.push(order);
          }
        });
      });
    }

    collectedOrders = collectedOrders.concat(results);

    statusEl.className = 'rc-status success';
    statusEl.textContent = '采集到 ' + results.length + ' 条退货数据 (总计: ' + collectedOrders.length + ' 条)';
    document.getElementById('rc-sub').textContent = '已采集 ' + collectedOrders.length + ' 条';
  };

  document.getElementById('rc-export').onclick = function() {
    if (collectedOrders.length === 0) {
      document.getElementById('rc-status').className = 'rc-status warn';
      document.getElementById('rc-status').textContent = '请先采集数据';
      return;
    }

    fetch('http://127.0.0.1:8765/api/return/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        orders: collectedOrders,
        chats: [],
        export_time: new Date().toISOString()
      })
    }).then(r => r.json()).then(result => {
      document.getElementById('rc-status').className = 'rc-status success';
      document.getElementById('rc-status').textContent = '已保存 ' + collectedOrders.length + ' 条数据到分析系统!';
    }).catch(e => {
      document.getElementById('rc-status').className = 'rc-status warn';
      document.getElementById('rc-status').textContent = '保存失败: Agent未运行';
    });
  };
})();
