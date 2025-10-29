#!/bin/bash

echo "========================================"
echo "A股数据分析 - 一键执行"
echo "========================================"
echo

echo "[1/3] 计算技术指标..."
echo
python scripts/calculate_indicators.py --batch --market CN
if [ $? -ne 0 ]; then
    echo
    echo "❌ 错误: 技术指标计算失败"
    exit 1
fi
echo
echo "✅ 技术指标计算完成"
echo

echo "[2/3] 运行选股分析..."
echo
python scripts/run_stock_selection.py --market CN --top 50
if [ $? -ne 0 ]; then
    echo
    echo "❌ 错误: 选股分析失败"
    exit 1
fi
echo
echo "✅ 选股分析完成"
echo

echo "[3/3] 启动Web服务..."
echo
echo "🌐 访问地址: http://localhost:5000"
echo "📊 A股选股: http://localhost:5000/selections?market=CN"
echo
echo "按 Ctrl+C 停止服务"
echo
python app.py

