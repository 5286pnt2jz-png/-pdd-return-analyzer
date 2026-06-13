checkStatus();

let collectedReturnOrders = [];

async function doCapture() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    if (tab.url.includes('mms.pinduoduo.com')) {
      await collectMerchantData(tab);
      return;
    }

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const bodyText = document.body.innerText;
        const data = { url: window.location.href, title: document.title, timestamp: new Date().toISOString(), goodsId: '', price: '', sales: '', shop: '', coupons: [], activities: [] };

        const gidMatch = window.location.href.match(/goods_id[=](\d+)/);
        if (gidMatch) data.goodsId = gidMatch[1];

        const priceMatch = bodyText.match(/券后[¥￥]?\s*(\d+\.?\d*)/) || bodyText.match(/[¥￥]\s*(\d+\.?\d*)/);
        if (priceMatch) data.price = '¥' + priceMatch[1];

        const salesPatterns = [/已拼([\d,.]+万?\+*)件/, /已售([\d,.]+万?\+*)件/, /([\d,.]+万?\+*)人已拼/];
        for (const p of salesPatterns) { const m = bodyText.match(p); if (m) { data.sales = m[0]; break; } }

        const shopPatterns = [/([^\n]{2,15}旗舰店)/, /([^\n]{2,15}官方旗舰)/, /([^\n]{2,15}专营店)/];
        for (const p of shopPatterns) { const m = bodyText.match(p); if (m) { data.shop = m[0].trim(); break; } }

        const couponPatterns = [/(\d+元无门槛\w*券)/g, /(\d+元优惠券)/g, /满(\d+)[-～~]?(\d*)减(\d+)/g];
        couponPatterns.forEach(pattern => { for (const match of bodyText.matchAll(pattern)) { if (!data.coupons.includes(match[0]) && match[0].length < 30) data.coupons.push(match[0]); } });

        const actKeywords = ['百亿补贴', '万人团', '限时秒杀', '拼单返', '折扣', '拼团', '官方补贴', '618', '大促'];
        actKeywords.forEach(kw => { if (bodyText.includes(kw) && !data.activities.includes(kw)) data.activities.push(kw); });

        return data;
      }
    });

    const data = results[0]?.result || {};
    await fetch('http://127.0.0.1:8765/api/data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });

    document.getElementById('resultArea').style.display = 'block';
    document.getElementById('rTitle').innerText = (data.goodsId ? 'ID:' + data.goodsId + ' ' : '') + (data.title || '');
    document.getElementById('rPrice').innerText = data.price || '-';
    document.getElementById('rSales').innerText = data.sales || '-';
    document.getElementById('rShop').innerText = data.shop || '-';
    document.getElementById('rCoupons').innerHTML = data.coupons.length > 0 ? data.coupons.map(c => '<span class="tag orange">' + c + '</span>').join('') : '<span class="empty">暂无</span>';
    document.getElementById('rActivities').innerHTML = data.activities.length > 0 ? data.activities.map(a => '<span class="tag green">' + a + '</span>').join('') : '<span class="empty">暂无</span>';
  } catch (e) {}
}

async function collectMerchantData(tab) {
  const resultEl = document.getElementById('collectResult');
  resultEl.style.display = 'block';
  resultEl.style.background = '#e3f2fd';
  resultEl.style.color = '#1565c0';
  resultEl.textContent = '正在读取页面数据...';

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      world: 'MAIN',
      func: () => {
        const orders = [];

        document.querySelectorAll('table').forEach(table => {
          const ths = table.querySelectorAll('th');
          if (ths.length === 0) return;
          const headers = Array.from(ths).map(h => h.innerText.trim());

          table.querySelectorAll('tbody tr').forEach(tr => {
            const cells = tr.querySelectorAll('td');
            if (cells.length < 3) return;
            const rowText = Array.from(cells).map(c => c.innerText.trim()).join(' | ');

            if (!rowText.match(/退货|退款|售后|退回|仅退款/)) return;

            const orderNo = (rowText.match(/(\d{4,6}-\d{10,})/) || ['', ''])[1];
            if (!orderNo) return;

            const order = { order_no: orderNo, amount: '', reason: '未填写', time: '', status: '' };

            headers.forEach((h, i) => {
              if (i >= cells.length) return;
              const val = cells[i].innerText.trim();
              if (h.includes('金额') || h.includes('实收')) order.amount = (val.match(/[\d.]+/) || [''])[0];
              if (h.includes('原因')) order.reason = val || '未填写';
              if (h.includes('时间')) order.time = val;
              if (h.includes('状态') || h.includes('类型')) order.status = order.status || val;
            });

            orders.push(order);
          });
        });

        if (orders.length === 0) {
          const allText = document.body.innerText;
          const orderMatches = allText.match(/订单号[：:]\s*(\d{4,6}-\d{10,})/g) || [];
          const reasons = allText.match(/售后原因[：:]\s*([^\s,，|]+)/g) || [];
          const amounts = allText.match(/实收[：:]\s*¥?([\d.]+)/g) || [];

          for (let i = 0; i < orderMatches.length; i++) {
            const orderNo = (orderMatches[i].match(/(\d{4,6}-\d{10,})/) || ['', ''])[1];
            const reason = reasons[i] ? (reasons[i].match(/售后原因[：:]\s*([^\s,，|]+)/) || ['', '未填写'])[1] : '未填写';
            const amount = amounts[i] ? (amounts[i].match(/([\d.]+)/) || ['', ''])[1] : '';
            orders.push({ order_no: orderNo, amount: amount, reason: reason, time: '', status: '' });
          }
        }

        return orders;
      }
    });

    const orders = results[0]?.result || [];
    collectedReturnOrders = collectedReturnOrders.concat(orders);

    if (orders.length > 0) {
      resultEl.style.background = '#e8f5e9';
      resultEl.style.color = '#2e7d32';
      resultEl.textContent = '采集到 ' + orders.length + ' 条 (总计: ' + collectedReturnOrders.length + ' 条)';

      document.getElementById('returnOrders').style.display = 'block';
      document.getElementById('returnOrders').innerHTML = orders.slice(0, 10).map(o =>
        '<div class="history-item"><span class="h-left">' + o.order_no.slice(0, 15) + ' | ' + o.reason + '</span><span class="h-right">¥' + o.amount + '</span></div>'
      ).join('');
    } else {
      resultEl.style.background = '#fff8e1';
      resultEl.style.color = '#f57f17';
      resultEl.textContent = '未采集到数据，请先筛选售后订单列表';
    }

  } catch (e) {
    resultEl.style.background = '#fee';
    resultEl.style.color = '#e74c3c';
    resultEl.textContent = '读取失败: ' + e.message;
  }
}

async function autoCapture() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url && tab.url.includes('goods_id=')) await doCapture();
  } catch (e) {}
}

document.getElementById('collectBtn').onclick = doCapture;

let collectedChats = [];

document.getElementById('chatCollectBtn').onclick = async function() {
  const resultEl = document.getElementById('chatCollectResult');
  resultEl.style.display = 'block';
  resultEl.style.background = '#e3f2fd';
  resultEl.style.color = '#1565c0';
  resultEl.textContent = '正在读取聊天记录...';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const debuggee = { tabId: tab.id };

    await chrome.debugger.attach(debuggee, '1.3');
    await chrome.debugger.sendCommand(debuggee, 'Runtime.enable');

    const expression = `(() => {
      // 先找到聊天记录区域
      const result = { structure: '', chatTexts: [], allTextSample: '' };

      // 获取页面所有元素的类名，用于调试
      const classNames = new Set();
      document.querySelectorAll('*').forEach(el => {
        if (el.className && typeof el.className === 'string') {
          el.className.split(' ').forEach(c => {
            if (c.length > 2) classNames.add(c);
          });
        }
      });
      result.structure = Array.from(classNames).filter(c =>
        c.match(/chat|msg|message|list|item|content|record|history|talk|im|dialog/)
      ).join(', ');

      // 获取页面文本的前2000字符用于分析
      result.allTextSample = document.body.innerText.slice(0, 2000);

      // 尝试直接获取表格内容
      const tables = document.querySelectorAll('table');
      if (tables.length > 0) {
        tables.forEach((table, idx) => {
          table.querySelectorAll('tr').forEach((tr, rowIdx) => {
            const cells = tr.querySelectorAll('td, th');
            const rowText = Array.from(cells).map(c => c.innerText.trim()).join(' | ');
            if (rowText.length > 5) {
              result.chatTexts.push('TABLE' + idx + '_ROW' + rowIdx + ': ' + rowText.slice(0, 200));
            }
          });
        });
      }

      return JSON.stringify(result);
    })()`;

    const result = await chrome.debugger.sendCommand(debuggee, 'Runtime.evaluate', {
      expression: expression,
      returnByValue: true
    });

    await chrome.debugger.detach(debuggee);

    let debugInfo = {};
    try {
      debugInfo = JSON.parse(result.result.value || '{}');
    } catch(e) {}

    // 显示调试信息
    resultEl.style.background = '#e3f2fd';
    resultEl.style.color = '#1565c0';
    resultEl.textContent = '页面类名: ' + (debugInfo.structure || '无') + ' | 表格内容: ' + (debugInfo.chatTexts?.length || 0) + ' 行';

    // 将调试信息保存以便查看
    collectedChats = [{ message: '调试信息-类名: ' + debugInfo.structure, buyer: '系统', time: '', category: '其他' }];
    if (debugInfo.chatTexts) {
      debugInfo.chatTexts.forEach(t => {
        collectedChats.push({ message: t, buyer: '调试', time: '', category: '其他' });
      });
    }
    if (debugInfo.allTextSample) {
      collectedChats.push({ message: '页面文本前500字: ' + debugInfo.allTextSample.slice(0, 500), buyer: '调试', time: '', category: '其他' });
    }

  } catch (e) {
    resultEl.style.background = '#fff8e1';
    resultEl.style.color = '#f57f17';
    resultEl.textContent = '采集失败: ' + e.message;
  }
};

document.getElementById('chatSaveBtn').onclick = async function() {
  if (collectedChats.length === 0) {
    const el = document.getElementById('chatCollectResult');
    el.style.display = 'block';
    el.style.background = '#fff8e1';
    el.style.color = '#f57f17';
    el.textContent = '请先采集聊天记录';
    return;
  }
  try {
    await fetch('http://127.0.0.1:8765/api/return/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orders: [], chats: collectedChats, export_time: new Date().toISOString(), source: 'chat_collect' })
    });
    const el = document.getElementById('chatCollectResult');
    el.style.background = '#e8f5e9';
    el.style.color = '#2e7d32';
    el.textContent = '已保存 ' + collectedChats.length + ' 条聊天记录到分析系统!';
  } catch (e) {
    const el = document.getElementById('chatCollectResult');
    el.style.background = '#fee';
    el.style.color = '#e74c3c';
    el.textContent = '保存失败: Agent未运行';
  }
};

document.getElementById('saveBtn').onclick = async function() {
  if (collectedReturnOrders.length === 0) {
    showResult('请先采集数据', '#fff8e1', '#f57f17');
    return;
  }
  try {
    await fetch('http://127.0.0.1:8765/api/return/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orders: collectedReturnOrders, chats: [], export_time: new Date().toISOString() })
    });
    showResult('已保存 ' + collectedReturnOrders.length + ' 条到分析系统!', '#e8f5e9', '#2e7d32');
  } catch (e) {
    showResult('保存失败: Agent未运行', '#fee', '#e74c3c');
  }
};

function showResult(msg, bg, color) {
  const el = document.getElementById('collectResult');
  el.style.display = 'block';
  el.style.background = bg;
  el.style.color = color;
  el.textContent = msg;
}

async function checkStatus() {
  try {
    await fetch('http://127.0.0.1:8765/api/status');
    document.getElementById('status').className = 'pill ok';
    document.getElementById('statusText').innerText = '就绪';
  } catch (e) {
    document.getElementById('status').className = 'pill warn';
    document.getElementById('statusText').innerText = 'Agent未运行';
  }
  autoCapture();
}
