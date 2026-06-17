checkStatus();

let collectedShopGoods = [];
let collectedMerchantGoods = [];

// Tab切换
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    this.classList.add('active');
    document.getElementById(this.dataset.tab).classList.add('active');
  });
});

async function doCapture() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

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

async function autoCapture() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url && tab.url.includes('goods_id=')) await doCapture();
  } catch (e) {}
}

let collectedChats = [];

async function checkStatus() {
  try {
    await fetch('http://127.0.0.1:8765/api/status');
    document.getElementById('status').className = 'pill ok';
    document.getElementById('statusText').innerText = '就绪';
    document.getElementById('agentTip').style.display = 'none';
  } catch (e) {
    document.getElementById('status').className = 'pill warn';
    document.getElementById('statusText').innerText = 'Agent未运行';
    document.getElementById('agentTip').style.display = 'block';
  }
  autoCapture();
}

// 打开退货分析按钮
document.getElementById('openAnalysisBtn').onclick = async function() {
  try {
    await fetch('http://127.0.0.1:8765/api/status');
    window.open('http://127.0.0.1:8765/return_analysis', '_blank');
  } catch (e) {
    document.getElementById('agentTip').style.display = 'block';
  }
};

// 启动Agent按钮
document.getElementById('startAgentBtn').onclick = async function() {
  const btn = this;
  const originalText = btn.textContent;
  btn.textContent = '启动中...';
  btn.disabled = true;

  try {
    const res = await fetch('http://127.0.0.1:8766/api/watcher/start', { method: 'POST' });
    const data = await res.json();
    
    if (data.status === 'started' || data.status === 'already_running') {
      btn.textContent = '已启动';
      for (let i = 0; i < 15; i++) {
        await new Promise(r => setTimeout(r, 1000));
        try {
          await fetch('http://127.0.0.1:8765/api/status');
          btn.textContent = '就绪';
          checkStatus();
          window.open('http://127.0.0.1:8765/return_analysis', '_blank');
          break;
        } catch (e) {}
      }
    } else {
      btn.textContent = '启动失败';
    }
  } catch (e) {
    btn.textContent = '未连接';
    document.getElementById('agentTip').style.display = 'block';
  }

  btn.disabled = false;
  setTimeout(() => { btn.textContent = originalText; }, 3000);
};

// 店铺商品导出
document.getElementById('goodsCollectBtn').onclick = async function() {
  const resultEl = document.getElementById('goodsCollectResult');
  const progressBar = document.getElementById('goodsProgressBar');
  const progressEl = document.getElementById('goodsProgress');
  const goodsList = document.getElementById('goodsList');
  
  resultEl.style.display = 'block';
  resultEl.style.background = '#e3f2fd';
  resultEl.style.color = '#1565c0';
  resultEl.textContent = '正在采集商品数据...';
  progressEl.style.display = 'block';
  progressBar.style.width = '0%';
  goodsList.style.display = 'block';
  goodsList.innerHTML = '';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url.includes('yangkeduo.com')) {
      resultEl.style.background = '#fff8e1';
      resultEl.style.color = '#f57f17';
      resultEl.textContent = '请先打开拼多多店铺页面';
      progressEl.style.display = 'none';
      return;
    }

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const results = [];
        const seen = new Set();
        const cards = document.querySelectorAll('div[class*="goodsItem_"]');
        
        cards.forEach(card => {
          const text = card.innerText || '';
          if (text.length < 10) return;
          const goods = { goods_id: '', goods_name: '', price: '', sales: '', raw: text.slice(0, 200) };
          
          const priceMatch = text.match(/[¥￥]\s*(\d+\.?\d*)/);
          if (priceMatch) goods.price = '¥' + priceMatch[1];
          
          const salesMatch = text.match(/已抢([\d,.]+件)/) || text.match(/([\d,.]+万人已拼)/) || text.match(/([\d,.]+)人已拼/);
          if (salesMatch) goods.sales = salesMatch[0];
          
          const nameEl = card.querySelector('div[class*="goodsName_"]');
          if (nameEl) {
            const img = nameEl.querySelector('img');
            const nameText = nameEl.innerText || (img ? img.alt : '') || '';
            goods.goods_name = nameText.replace(/^[^a-zA-Z\u4e00-\u9fa5]+/, '').trim().substring(0, 80);
          }
          
          if (!goods.goods_name) {
            const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 5 && !l.match(/[¥￥]|已抢|百亿补贴|秒杀|品牌|预计|正品|收藏/));
            if (lines.length > 0) goods.goods_name = lines[0].substring(0, 80);
          }
          
          if (!goods.goods_id) {
            const keys = Object.keys(card);
            for (const key of keys) {
              if (key.startsWith('__reactFiber$') || key.startsWith('__reactInternalInstance$')) {
                try {
                  let fiber = card[key];
                  for (let i = 0; i < 15 && fiber; i++) {
                    const props = fiber.memoizedProps || fiber.pendingProps || {};
                    const tracking = props.trackingInfo || props.extraImprParams || {};
                    if (tracking.rec_goods_id) {
                      goods.goods_id = String(tracking.rec_goods_id);
                      break;
                    }
                    if (props.goodsId || props.goods_id || props.goodsID) {
                      goods.goods_id = String(props.goodsId || props.goods_id || props.goodsID);
                      break;
                    }
                    fiber = fiber.return;
                  }
                } catch(e) {}
              }
              if (goods.goods_id) break;
            }
          }
          
          const key = (goods.goods_name || '') + '|' + (goods.price || '');
          if (key !== '|' && !seen.has(key)) {
            seen.add(key);
            results.push(goods);
          }
        });
        
        return results;
      }
    });

    const goods = results[0]?.result || [];
    collectedShopGoods = goods;

    goods.forEach(g => {
      const itemDiv = document.createElement('div');
      itemDiv.className = 'goods-item';
      itemDiv.innerHTML = `
        <span class="goods-name" title="${(g.goods_name || '').replace(/"/g, '&quot;')}">${g.goods_id ? '[' + g.goods_id + '] ' : ''}${g.goods_name || '未知商品'}</span>
        <span class="goods-price">${g.price || '未知价格'}</span>
      `;
      goodsList.appendChild(itemDiv);
    });

    progressBar.style.width = '100%';
    resultEl.style.background = '#e8f5e9';
    resultEl.style.color = '#2e7d32';
    resultEl.textContent = '采集到 ' + goods.length + ' 个商品';
    setTimeout(() => { progressEl.style.display = 'none'; }, 1000);

  } catch (e) {
    resultEl.style.background = '#fee';
    resultEl.style.color = '#e74c3c';
    resultEl.textContent = '采集失败: ' + e.message;
    progressEl.style.display = 'none';
  }
};

document.getElementById('goodsExportBtn').onclick = function() {
  if (collectedShopGoods.length === 0) {
    const el = document.getElementById('goodsCollectResult');
    el.style.display = 'block';
    el.style.background = '#fff8e1';
    el.style.color = '#f57f17';
    el.textContent = '请先采集商品数据';
    return;
  }

  const headers = ['商品ID', '商品名称', '价格', '销量'];
  const csvRows = [headers.join(',')];

  collectedShopGoods.forEach(goods => {
    const row = [
      goods.goods_id,
      '"' + (goods.goods_name || '').replace(/"/g, '""') + '"',
      goods.price,
      '"' + (goods.sales || '').replace(/"/g, '""') + '"'
    ];
    csvRows.push(row.join(','));
  });

  const csvContent = '\uFEFF' + csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'pdd_shop_goods_' + new Date().toISOString().slice(0, 10) + '.csv';
  link.click();
  URL.revokeObjectURL(url);

  const el = document.getElementById('goodsCollectResult');
  el.style.display = 'block';
  el.style.background = '#e8f5e9';
  el.style.color = '#2e7d32';
  el.textContent = '已导出 ' + collectedShopGoods.length + ' 个商品到CSV文件';
};

// 商家商品活动价导出
document.getElementById('merchantGoodsCollectBtn').onclick = async function() {
  const resultEl = document.getElementById('merchantGoodsCollectResult');
  const progressBar = document.getElementById('merchantGoodsProgressBar');
  const progressEl = document.getElementById('merchantGoodsProgress');
  
  resultEl.style.display = 'block';
  resultEl.style.background = '#e3f2fd';
  resultEl.style.color = '#1565c0';
  resultEl.textContent = '正在采集商品数据...';
  progressEl.style.display = 'block';
  progressBar.style.width = '0%';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url.includes('mms.pinduoduo.com')) {
      resultEl.style.background = '#fff8e1';
      resultEl.style.color = '#f57f17';
      resultEl.textContent = '请先打开商家后台商品页面';
      progressEl.style.display = 'none';
      return;
    }

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const results = [];
        const tableSelectors = ['table', '.ant-table', '[class*="goods-list"]', '[class*="product-list"]', '[class*="table"]'];

        for (const selector of tableSelectors) {
          const tables = document.querySelectorAll(selector);
          if (tables.length > 0) {
            tables.forEach(table => {
              const headerCells = table.querySelectorAll('th, .ant-table-thead th');
              const headers = Array.from(headerCells).map(h => h.innerText.trim());

              table.querySelectorAll('tbody tr, .ant-table-row').forEach(tr => {
                const cells = tr.querySelectorAll('td, .ant-table-cell');
                const rowText = Array.from(cells).map(c => c.innerText.trim()).join(' | ');
                const goods = { goods_id: '', goods_name: '', original_price: '', activity_price: '', final_price: '', sales: '', status: '', raw: rowText.slice(0, 300) };

                headers.forEach((h, i) => {
                  if (i >= cells.length) return;
                  const val = cells[i].innerText.trim();
                  const headerLower = h.toLowerCase();
                  if (headerLower.includes('商品id') || headerLower.includes('goods_id')) goods.goods_id = val;
                  else if (headerLower.includes('商品名称') || headerLower.includes('商品名')) goods.goods_name = val;
                  else if (headerLower.includes('原价') || headerLower.includes('市场价')) goods.original_price = val;
                  else if (headerLower.includes('活动价') || headerLower.includes('促销价')) goods.activity_price = val;
                  else if (headerLower.includes('到手价') || headerLower.includes('实付')) goods.final_price = val;
                  else if (headerLower.includes('销量') || headerLower.includes('已售')) goods.sales = val;
                  else if (headerLower.includes('状态')) goods.status = val;
                });

                if (!goods.goods_id) {
                  const idMatch = rowText.match(/(\d{10,})/);
                  if (idMatch) goods.goods_id = idMatch[1];
                }

                if (!goods.goods_name) {
                  let maxLen = 0;
                  cells.forEach(cell => {
                    const text = cell.innerText.trim();
                    if (text.length > maxLen && text.length < 100) {
                      maxLen = text.length;
                      goods.goods_name = text;
                    }
                  });
                }

                const pricePatterns = [/(\d+\.?\d+)\s*元/g, /[¥￥]\s*(\d+\.?\d+)/g, /(\d+\.?\d+)\s*¥/g];
                const prices = [];
                pricePatterns.forEach(pattern => {
                  const matches = rowText.matchAll(pattern);
                  for (const match of matches) prices.push(parseFloat(match[1]));
                });
                if (prices.length >= 2) {
                  goods.original_price = prices[0].toString();
                  goods.activity_price = prices[1].toString();
                  if (prices.length >= 3) goods.final_price = prices[2].toString();
                } else if (prices.length === 1) goods.activity_price = prices[0].toString();

                const salesMatch = rowText.match(/(\d+\.?\d*)\s*(?:万\+?|件|销量|已售)/);
                if (salesMatch) goods.sales = salesMatch[0];

                if (goods.goods_id || goods.goods_name) results.push(goods);
              });
            });
            break;
          }
        }
        return results;
      }
    });

    const goods = results[0]?.result || [];
    collectedMerchantGoods = goods;

    progressBar.style.width = '100%';
    resultEl.style.background = '#e8f5e9';
    resultEl.style.color = '#2e7d32';
    resultEl.textContent = '采集到 ' + goods.length + ' 个商品';
    setTimeout(() => { progressEl.style.display = 'none'; }, 1000);

  } catch (e) {
    resultEl.style.background = '#fee';
    resultEl.style.color = '#e74c3c';
    resultEl.textContent = '采集失败: ' + e.message;
    progressEl.style.display = 'none';
  }
};

document.getElementById('merchantGoodsExportBtn').onclick = function() {
  if (collectedMerchantGoods.length === 0) {
    const el = document.getElementById('merchantGoodsCollectResult');
    el.style.display = 'block';
    el.style.background = '#fff8e1';
    el.style.color = '#f57f17';
    el.textContent = '请先采集商品数据';
    return;
  }

  const headers = ['商品ID', '商品名称', '原价', '活动价', '到手价', '销量', '状态'];
  const csvRows = [headers.join(',')];

  collectedMerchantGoods.forEach(goods => {
    const row = [
      goods.goods_id,
      '"' + (goods.goods_name || '').replace(/"/g, '""') + '"',
      goods.original_price,
      goods.activity_price,
      goods.final_price,
      goods.sales,
      goods.status
    ];
    csvRows.push(row.join(','));
  });

  const csvContent = '\uFEFF' + csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'pdd_goods_activity_price_' + new Date().toISOString().slice(0, 10) + '.csv';
  link.click();
  URL.revokeObjectURL(url);

  const el = document.getElementById('merchantGoodsCollectResult');
  el.style.display = 'block';
  el.style.background = '#e8f5e9';
  el.style.color = '#2e7d32';
  el.textContent = '已导出 ' + collectedMerchantGoods.length + ' 个商品到CSV文件';
};
