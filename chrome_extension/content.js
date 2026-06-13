(function() {
  if (!window.location.href.match(/goods_id[=]/)) return;

  const style = document.createElement('style');
  style.textContent = `
    #pdd-agent-panel {
      position: fixed; top: 100px; left: 0; z-index: 99999;
      width: 400px; background: #fff; border-radius: 0 20px 20px 0;
      box-shadow: 0 4px 30px rgba(0,0,0,0.15);
      font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
      font-size: 14px; color: #1d1d1f;
      transition: transform 0.3s ease;
    }
    #pdd-agent-panel.collapsed { transform: translateX(-360px); }
    .pa-header {
      padding: 16px 18px; background: linear-gradient(135deg, #e74c3c, #c0392b);
      border-radius: 0 20px 0 0; display: flex; align-items: center; gap: 10px;
    }
    .pa-header-icon {
      width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.2);
      display: flex; align-items: center; justify-content: center;
      color: white; font-size: 18px; font-weight: 700;
    }
    .pa-header-text { flex: 1; }
    .pa-header-title { color: #fff; font-size: 16px; font-weight: 600; }
    .pa-header-sub { color: rgba(255,255,255,0.7); font-size: 12px; margin-top: 2px; }
    .pa-toggle {
      width: 32px; height: 32px; border-radius: 8px; background: rgba(255,255,255,0.2);
      border: none; color: white; font-size: 18px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    .pa-body { padding: 12px 18px 18px; }
    .pa-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 10px 0;
    }
    .pa-row:not(:last-child) { border-bottom: 1px solid #f2f2f7; }
    .pa-label { color: #86868b; font-size: 14px; }
    .pa-value {
      font-size: 14px; font-weight: 500; color: #1d1d1f;
      text-align: right; max-width: 260px;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .pa-value.red { color: #e74c3c; font-weight: 600; font-size: 16px; }
    .pa-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
    .pa-tag {
      padding: 5px 12px; border-radius: 14px; font-size: 12px; font-weight: 500;
    }
    .pa-tag.green { background: #e8f5e9; color: #2e7d32; }
    .pa-tag.orange { background: #fff8e1; color: #f57f17; }
    .pa-section {
      margin-top: 10px; padding-top: 10px; border-top: 1px solid #f2f2f7;
    }
    .pa-section-title {
      font-size: 11px; color: #86868b; text-transform: uppercase;
      letter-spacing: 0.5px; margin-bottom: 6px; font-weight: 600;
    }
    .pa-loading {
      text-align: center; padding: 30px; color: #86868b; font-size: 13px;
    }
    .pa-spinner {
      width: 24px; height: 24px; border: 3px solid #e5e5ea;
      border-top-color: #e74c3c; border-radius: 50%;
      animation: pa-spin 0.8s linear infinite; margin: 0 auto 10px;
    }
    @keyframes pa-spin { to { transform: rotate(360deg); } }
  `;
  document.head.appendChild(style);

  const panel = document.createElement('div');
  panel.id = 'pdd-agent-panel';
  panel.innerHTML = `
    <div class="pa-header">
      <div class="pa-header-icon">P</div>
      <div class="pa-header-text">
        <div class="pa-header-title">竞品监控</div>
        <div class="pa-header-sub">自动抓取中...</div>
      </div>
      <button class="pa-toggle" id="pa-toggle">◀</button>
    </div>
    <div class="pa-body" id="pa-body">
      <div class="pa-loading">
        <div class="pa-spinner"></div>
        正在抓取数据...
      </div>
    </div>
  `;
  document.body.appendChild(panel);

  let collapsed = false;
  document.getElementById('pa-toggle').onclick = function() {
    collapsed = !collapsed;
    panel.classList.toggle('collapsed', collapsed);
    this.textContent = collapsed ? '▶' : '◀';
  };

  function captureData() {
    const bodyText = document.body.innerText;
    const data = {
      url: window.location.href,
      title: document.title,
      timestamp: new Date().toISOString(),
      goodsId: '',
      price: '',
      sales: '',
      shop: '',
      coupons: [],
      activities: []
    };

    const gidMatch = window.location.href.match(/goods_id[=](\d+)/);
    if (gidMatch) data.goodsId = gidMatch[1];

    const priceMatch = bodyText.match(/券后[¥￥]?\s*(\d+\.?\d*)/) || bodyText.match(/[¥￥]\s*(\d+\.?\d*)/);
    if (priceMatch) data.price = '¥' + priceMatch[1];

    const salesPatterns = [/已拼([\d,.]+万?\+*)件/, /已售([\d,.]+万?\+*)件/, /([\d,.]+万?\+*)人已拼/];
    for (const p of salesPatterns) {
      const m = bodyText.match(p);
      if (m) { data.sales = m[0]; break; }
    }
    if (!data.sales) {
      const htmlSales = document.body.innerHTML.match(/已拼([\d,.]+万?\+*)件/);
      if (htmlSales) data.sales = htmlSales[0];
    }

    const shopPatterns = [/([^\n]{2,15}旗舰店)/, /([^\n]{2,15}官方旗舰)/, /([^\n]{2,15}专营店)/];
    for (const p of shopPatterns) {
      const m = bodyText.match(p);
      if (m) { data.shop = m[0].trim(); break; }
    }

    const couponPatterns = [/(\d+元无门槛\w*券)/g, /(\d+元优惠券)/g, /满(\d+)[-～~]?(\d*)减(\d+)/g];
    couponPatterns.forEach(pattern => {
      const matches = bodyText.matchAll(pattern);
      for (const match of matches) {
        if (!data.coupons.includes(match[0]) && match[0].length < 30) {
          data.coupons.push(match[0]);
        }
      }
    });

    const actKeywords = ['百亿补贴', '万人团', '限时秒杀', '拼单返', '折扣', '拼团', '官方补贴', '618', '大促'];
    actKeywords.forEach(kw => {
      if (bodyText.includes(kw) && !data.activities.includes(kw)) {
        data.activities.push(kw);
      }
    });

    try {
      fetch('http://127.0.0.1:8765/api/data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).catch(() => {});
    } catch(e) {}

    return data;
  }

  function renderData(data) {
    const body = document.getElementById('pa-body');
    let html = '';

    html += '<div class="pa-row"><span class="pa-label">价格</span><span class="pa-value red">' + (data.price || '-') + '</span></div>';
    html += '<div class="pa-row"><span class="pa-label">销量</span><span class="pa-value">' + (data.sales || '-') + '</span></div>';
    html += '<div class="pa-row"><span class="pa-label">店铺</span><span class="pa-value">' + (data.shop || '-') + '</span></div>';

    if (data.coupons && data.coupons.length > 0) {
      html += '<div class="pa-section"><div class="pa-section-title">优惠券</div><div class="pa-tags">';
      data.coupons.forEach(c => { html += '<span class="pa-tag orange">' + c + '</span>'; });
      html += '</div></div>';
    }

    if (data.activities && data.activities.length > 0) {
      html += '<div class="pa-section"><div class="pa-section-title">营销活动</div><div class="pa-tags">';
      data.activities.forEach(a => { html += '<span class="pa-tag green">' + a + '</span>'; });
      html += '</div></div>';
    }

    body.innerHTML = html;
    document.querySelector('.pa-header-sub').textContent = '已抓取 · ' + (data.price || '');
  }

  setTimeout(() => {
    const data = captureData();
    renderData(data);
  }, 2000);

  let lastUrl = location.href;
  const observer = new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      if (location.href.match(/goods_id[=]/)) {
        document.getElementById('pa-body').innerHTML = '<div class="pa-loading"><div class="pa-spinner"></div>正在抓取数据...</div>';
        setTimeout(() => {
          const data = captureData();
          renderData(data);
        }, 3000);
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
