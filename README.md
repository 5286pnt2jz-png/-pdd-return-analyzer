# PDD 退货分析工具

拼多多商家必备 - 自动分析退货原因，智能分类买家反馈，生成改进建议报告。

## 功能

- **退货原因分析** - 自动统计退货原因分布，数据可视化
- **聊天记录分析** - 导入消费者聊天记录，AI自动分类反馈
- **CSV批量导入** - 支持拼多多售后工作台导出的XLSX/CSV格式
- **智能改进建议** - 根据退货数据自动生成改进建议

## 快速开始

### 方式一：exe直接运行（推荐）

1. 下载 `PDD退货分析.exe`（见 Releases）
2. 双击运行，自动打开浏览器
3. 导入CSV数据即可分析

### 方式二：源码运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/pdd-return-analyzer.git
cd pdd-return-analyzer

# 安装依赖
pip install pandas openpyxl

# 启动服务
python main.py
```

浏览器打开 http://127.0.0.1:8765

## 使用方法

### 1. 导出售后数据

登录拼多多商家后台 → 售后管理 → 售后工作台 → 筛选商品和时间 → 批量导出

### 2. 导入分析

打开退货分析页面，拖入导出的XLSX/CSV文件，点击「分析导入数据」

### 3. 查看报告

系统自动生成：
- 退货原因分布图表
- 买家反馈记录分类
- 智能改进建议

## 浏览器扩展

扩展位于 `chrome_extension/` 目录，安装方法：

1. 打开 Edge/Chrome，地址栏输入 `edge://extensions` 或 `chrome://extensions`
2. 打开「开发者模式」
3. 点击「加载已解压的扩展程序」，选择 `chrome_extension` 文件夹

## 文件结构

```
pdd_agent/
├── main.py              # 后端服务
├── tray_app.py          # 托盘启动入口
├── start.bat            # Windows启动脚本
├── templates/           # HTML页面
│   └── return_analysis.html
├── chrome_extension/    # 浏览器扩展
├── website/             # 下载页面
└── data/                # 数据存储（不上传）
```

## 环境要求

- Python 3.8+
- 浏览器（Edge/Chrome）

## 许可证

MIT License
