"""
Flask Web应用
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from loguru import logger


def create_app(config):
    """
    创建Flask应用

    Args:
        config: 配置字典

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)

    # 配置
    web_config = config.get('web', {})
    app.config['SECRET_KEY'] = web_config.get('secret_key', 'dev-secret-key')

    # 启用CORS
    CORS(app)

    # 注册路由
    register_routes(app, config)

    return app


def register_routes(app, config):
    """注册路由"""

    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        """仪表板"""
        return render_template('dashboard.html')

    @app.route('/kline')
    def kline():
        """K线图表页面"""
        return render_template('kline.html')

    @app.route('/selections')
    def selections():
        """选股结果页面"""
        return render_template('selections.html')

    @app.route('/compare')
    def compare():
        """股票对比页面"""
        return render_template('compare.html')

    @app.route('/trading-signals')
    def trading_signals():
        """买卖信号页面"""
        return render_template('trading_signals.html')


    @app.route('/api/health')
    def health():
        """健康检查"""
        return jsonify({
            'status': 'ok',
            'message': '长桥证券量化交易系统运行中'
        })

    @app.route('/trading')
    def trading_page():
        return render_template('trading.html')

    @app.route('/api/stocks')
    def get_stocks():
        """获取股票列表"""
        try:
            from database import get_db_manager
            from database.models import StockInfo

            db_manager = get_db_manager()

            # 获取查询参数
            market = request.args.get('market', 'HK')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))

            with db_manager.get_session() as session:
                # 查询股票
                query = session.query(StockInfo).filter_by(market=market, is_active=True)
                total = query.count()

                stocks = query.offset((page - 1) * per_page).limit(per_page).all()

                return jsonify({
                    'success': True,
                    'data': {
                        'stocks': [
                            {
                                'symbol': s.symbol,
                                'name': s.name,
                                'market': s.market,
                                'sector': s.sector,
                                'market_cap': s.market_cap
                            }
                            for s in stocks
                        ],
                        'total': total,
                        'page': page,
                        'per_page': per_page
                    }
                })
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/stock/<symbol>')
    def get_stock_detail(symbol):
        """获取股票详情"""
        try:
            from database import get_db_manager
            from database.models import StockInfo, DailyData
            from datetime import datetime, timedelta

            db_manager = get_db_manager()

            with db_manager.get_session() as session:
                # 查询股票信息
                stock = session.query(StockInfo).filter_by(symbol=symbol).first()
                if not stock:
                    return jsonify({
                        'success': False,
                        'error': '股票不存在'
                    }), 404

                # 查询最近30天的日线数据
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)

                daily_data = session.query(DailyData).filter(
                    DailyData.symbol == symbol,
                    DailyData.trade_date >= start_date,
                    DailyData.trade_date <= end_date
                ).order_by(DailyData.trade_date).all()

                return jsonify({
                    'success': True,
                    'data': {
                        'stock': {
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'market': stock.market,
                            'sector': stock.sector,
                            'market_cap': stock.market_cap
                        },
                        'daily_data': [
                            {
                                'date': d.trade_date.isoformat(),
                                'open': d.open,
                                'high': d.high,
                                'low': d.low,
                                'close': d.close,
                                'volume': d.volume
                            }
                            for d in daily_data
                        ]
                    }
                })
        except Exception as e:
            logger.error(f"获取股票详情失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/stock/<symbol>/kline')
    def get_stock_kline(symbol):
        """获取股票K线数据（含技术指标）"""
        try:
            from database import get_db_manager
            from database.models import StockInfo, DailyData, TechnicalIndicator
            from datetime import datetime, timedelta

            db_manager = get_db_manager()

            # 获取查询参数
            days = int(request.args.get('days', 90))  # 默认90天

            with db_manager.get_session() as session:
                # 查询股票信息
                stock = session.query(StockInfo).filter_by(symbol=symbol).first()
                if not stock:
                    return jsonify({
                        'success': False,
                        'error': '股票不存在'
                    }), 404

                # 查询K线数据
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)

                daily_data = session.query(DailyData).filter(
                    DailyData.symbol == symbol,
                    DailyData.trade_date >= start_date,
                    DailyData.trade_date <= end_date
                ).order_by(DailyData.trade_date).all()

                # 查询技术指标
                indicators = session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.symbol == symbol,
                    TechnicalIndicator.trade_date >= start_date,
                    TechnicalIndicator.trade_date <= end_date
                ).order_by(TechnicalIndicator.trade_date).all()

                # 构建指标字典（按日期索引）
                indicator_dict = {ind.trade_date: ind for ind in indicators}

                # 组合数据
                kline_data = []
                for d in daily_data:
                    ind = indicator_dict.get(d.trade_date)

                    item = {
                        'date': d.trade_date.isoformat(),
                        'open': float(d.open) if d.open else None,
                        'high': float(d.high) if d.high else None,
                        'low': float(d.low) if d.low else None,
                        'close': float(d.close) if d.close else None,
                        'volume': float(d.volume) if d.volume else None,
                    }

                    # 添加技术指标
                    if ind:
                        item.update({
                            'ma5': float(ind.ma5) if ind.ma5 else None,
                            'ma10': float(ind.ma10) if ind.ma10 else None,
                            'ma20': float(ind.ma20) if ind.ma20 else None,
                            'ma60': float(ind.ma60) if ind.ma60 else None,
                            'macd': float(ind.macd) if ind.macd else None,
                            'macd_signal': float(ind.macd_signal) if ind.macd_signal else None,
                            'macd_hist': float(ind.macd_hist) if ind.macd_hist else None,
                            'rsi': float(ind.rsi) if ind.rsi else None,
                            'kdj_k': float(ind.kdj_k) if ind.kdj_k else None,
                            'kdj_d': float(ind.kdj_d) if ind.kdj_d else None,
                            'kdj_j': float(ind.kdj_j) if ind.kdj_j else None,
                            'boll_upper': float(ind.boll_upper) if ind.boll_upper else None,
                            'boll_middle': float(ind.boll_middle) if ind.boll_middle else None,
                            'boll_lower': float(ind.boll_lower) if ind.boll_lower else None,
                        })

                    kline_data.append(item)

                return jsonify({
                    'success': True,
                    'data': {
                        'stock': {
                            'symbol': stock.symbol,
                            'name': stock.name,
                            'market': stock.market
                        },
                        'kline': kline_data
                    }
                })
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/selections')
    def get_selections():
        """获取选股结果"""
        try:
            from database import get_db_manager
            from database.models import StockSelection, StockInfo
            from datetime import datetime

            db_manager = get_db_manager()

            # 获取查询参数
            market = request.args.get('market', 'HK')  # 默认港股
            date_str = request.args.get('date')
            if date_str:
                selection_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                selection_date = datetime.now().date()

            with db_manager.get_session() as session:
                # 查询选股结果（按市场过滤）
                selections = session.query(StockSelection, StockInfo).join(
                    StockInfo, StockSelection.symbol == StockInfo.symbol
                ).filter(
                    StockInfo.market == market,
                    StockSelection.selection_date == selection_date
                ).order_by(
                    StockSelection.total_score.desc()
                ).limit(50).all()

                return jsonify({
                    'success': True,
                    'data': {
                        'date': selection_date.isoformat(),
                        'selections': [
                            {
                                'rank': sel.rank,
                                'symbol': sel.symbol,
                                'name': stock.name,
                                'total_score': sel.total_score,
                                'technical_score': sel.technical_score,
                                'volume_score': sel.volume_score,
                                'trend_score': sel.trend_score,
                                'pattern_score': sel.pattern_score,
                                'latest_price': sel.latest_price,
                                'current_price': sel.current_price,
                                'reason': sel.reason
                            }
                            for sel, stock in selections
                        ]
                    }
                })
        except Exception as e:
            logger.error(f"获取选股结果失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/stock/<symbol>/trading-signals')
    def get_trading_signals(symbol):
        """获取股票买卖信号"""
        try:
            from database import get_db_manager
            from database.models import StockInfo, DailyData, TechnicalIndicator
            from analysis.trading_signals import TradingSignalAnalyzer

            db_manager = get_db_manager()

            with db_manager.get_session() as session:
                # 获取股票信息
                stock = session.query(StockInfo).filter_by(symbol=symbol).first()
                if not stock:
                    return jsonify({
                        'success': False,
                        'error': f'股票 {symbol} 不存在'
                    }), 404

                # 获取K线数据和技术指标
                query = session.query(
                    DailyData, TechnicalIndicator
                ).outerjoin(
                    TechnicalIndicator,
                    (DailyData.symbol == TechnicalIndicator.symbol) &
                    (DailyData.trade_date == TechnicalIndicator.trade_date)
                ).filter(
                    DailyData.symbol == symbol
                ).order_by(
                    DailyData.trade_date
                )

                results = query.all()

                if not results:
                    return jsonify({
                        'success': False,
                        'error': f'股票 {symbol} 没有数据'
                    }), 404

                # 转换为字典列表
                kline_data = []
                for daily, indicator in results:
                    data = {
                        'date': daily.trade_date.strftime('%Y-%m-%d'),
                        'open': daily.open,
                        'high': daily.high,
                        'low': daily.low,
                        'close': daily.close,
                        'volume': daily.volume
                    }

                    if indicator:
                        data.update({
                            'ma5': indicator.ma5,
                            'ma10': indicator.ma10,
                            'ma20': indicator.ma20,
                            'ma60': indicator.ma60,
                            'macd': indicator.macd,
                            'signal': indicator.macd_signal,
                            'rsi': indicator.rsi,
                            'kdj_k': indicator.kdj_k,
                            'kdj_d': indicator.kdj_d,
                            'kdj_j': indicator.kdj_j,
                            'boll_upper': indicator.boll_upper,
                            'boll_middle': indicator.boll_middle,
                            'boll_lower': indicator.boll_lower,
                            'atr': indicator.atr
                        })

                    kline_data.append(data)

                # 创建分析器
                analyzer = TradingSignalAnalyzer(kline_data)

                # 生成分析结果
                result = {
                    'symbol': symbol,
                    'name': stock.name,
                    'current_price': kline_data[-1]['close'],
                    'buy_signals': analyzer.generate_buy_signals(),
                    'sell_signals': analyzer.generate_sell_signals(),
                    'support_resistance': analyzer.calculate_support_resistance(),
                    'target_prices': analyzer.calculate_target_prices(),
                    'best_historical_trades': analyzer.find_best_historical_trades()
                }
                return jsonify({
                    'success': True,
                    'data': result
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    # ======== Trading (HK Paper) Minimal APIs ========
    from datetime import datetime as _dt
    from sqlalchemy import func as _func

    RISK_MAX_PER_POSITION = 0.05   # 单票≤5%
    RISK_MAX_GROSS = 0.80          # 总仓≤80%
    DEFAULT_INITIAL_CASH = 1000000.0
    DEFAULT_SLIPPAGE = 0.003       # 0.3%

    def _get_latest_price(session, symbol: str):
        from database.models import DailyData
        row = (
            session.query(DailyData)
            .filter(DailyData.symbol == symbol)
            .order_by(DailyData.trade_date.desc())
            .first()
        )
        return row.close if row else None

    def _get_portfolio_state(session):
        from database.models import Position, PortfolioSnapshot, DailyData
        # 取最近快照
        snapshot = (
            session.query(PortfolioSnapshot)
            .order_by(PortfolioSnapshot.snapshot_time.desc())
            .first()
        )
        cash = snapshot.cash if snapshot else DEFAULT_INITIAL_CASH
        # 计算当前持仓市值
        positions = session.query(Position).all()
        equity = 0.0
        for p in positions:
            last_price = _get_latest_price(session, p.symbol) or p.avg_price or 0.0
            equity += (p.quantity or 0) * (last_price or 0.0)
        total_value = cash + equity
        return cash, equity, total_value

    @app.route('/api/trading/order', methods=['POST'])
    def place_order():
        """下单（支持本地Paper/LongPort模拟/实盘，根据配置自动切换）"""
        try:
            from trading.engine_factory import get_trading_engine

            payload = request.get_json(force=True) or {}
            symbol = str(payload.get('symbol', '')).upper().strip()
            side = str(payload.get('side', '')).upper().strip()  # BUY/SELL
            order_type = str(payload.get('order_type', 'LIMIT')).upper().strip()
            price = payload.get('price')
            quantity = int(payload.get('quantity') or 0)
            strategy_tag = payload.get('strategy_tag')

            if not symbol or side not in ('BUY', 'SELL') or quantity <= 0:
                return jsonify({'success': False, 'error': '参数不完整或不合法'}), 400
            if order_type != 'LIMIT' or price is None:
                return jsonify({'success': False, 'error': '当前仅支持限价单且必须提供价格'}), 400
            if not symbol.endswith('.HK'):
                return jsonify({'success': False, 'error': '当前仅支持HK市场标的（如 0700.HK）'}), 400

            # 使用交易引擎下单（自动根据配置选择本地Paper/LongPort模拟/实盘）
            engine = get_trading_engine()
            logger.info(f"使用交易引擎: {engine.__class__.__name__}")
            result = engine.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                price=float(price),
                quantity=quantity,
                strategy_tag=strategy_tag
            )

            return jsonify({'success': True, 'data': result})

        except Exception as e:
            logger.error(f"下单失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/trading/mode')
    def get_trading_mode():
        """获取当前交易模式"""
        try:
            from trading.engine_factory import get_trading_engine
            engine = get_trading_engine()
            engine_name = engine.__class__.__name__

            # 根据引擎类型推断模式
            if engine_name == 'LocalPaperEngine':
                mode = 'local_paper'
            elif engine_name == 'LongPortPaperEngine':
                mode = 'longport_paper'
            else:
                mode = 'unknown'

            return jsonify({
                'success': True,
                'data': {
                    'mode': mode,
                    'engine': engine_name,
                    'description': {
                        'local_paper': '本地模拟交易（即刻撮合）',
                        'longport_paper': 'LongPort 模拟账号',
                        'longport_live': 'LongPort 实盘交易'
                    }.get(mode, '未知模式')
                }
            })
        except Exception as e:
            logger.error(f"获取交易模式失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/positions')
    def list_positions():
        try:
            from database import get_db_manager
            from database.models import Position
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                rows = session.query(Position).all()
                data = [
                    {
                        'symbol': r.symbol,
                        'quantity': r.quantity,
                        'avg_price': r.avg_price,
                        'market': r.market,
                        'updated_at': (r.updated_at or _dt.now()).isoformat()
                    }
                    for r in rows
                ]
                return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/orders')
    def list_orders():
        try:
            from database import get_db_manager
            from database.models import Order
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                rows = (
                    session.query(Order)
                    .order_by(Order.created_at.desc())
                    .limit(100)
                    .all()
                )
                data = [
                    {
                        'id': r.id,
                        'symbol': r.symbol,
                        'side': r.side,
                        'type': r.order_type,
                        'price': r.price,
                        'quantity': r.quantity,
                        'status': r.status,
                        'filled_quantity': r.filled_quantity,
                        'avg_fill_price': r.avg_fill_price,
                        'created_at': (r.created_at or _dt.now()).isoformat(),
                    }
                    for r in rows
                ]
                return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/portfolio/overview')
    def portfolio_overview():
        try:
            from database import get_db_manager
            from database.models import PortfolioSnapshot
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                cash, equity, total_value = _get_portfolio_state(session)
                initial = DEFAULT_INITIAL_CASH
                from datetime import datetime as _d
                today = _d.now().date()
                first_today = (
                    session.query(PortfolioSnapshot)
                    .filter(_func.date(PortfolioSnapshot.snapshot_time) == today)
                    .order_by(PortfolioSnapshot.snapshot_time.asc())
                    .first()
                )
                base = first_today.total_value if first_today else total_value
                daily_pnl = total_value - base
                return jsonify({'success': True, 'data': {
                    'cash': cash,
                    'equity': equity,
                    'total_value': total_value,
                    'daily_pnl': daily_pnl,
                    'cumulative_pnl': total_value - initial
                }})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    # ======== Scheduler APIs ========
    from trading.scheduler import get_scheduler

    @app.route('/api/scheduler/status')
    def scheduler_status():
        s = get_scheduler()
        return jsonify({"success": True, "data": s.status()})

    @app.route('/api/scheduler/start', methods=['POST'])
    def scheduler_start():
        s = get_scheduler()
        interval = int((request.get_json(silent=True) or {}).get('interval_sec', 60))
        started = s.start(interval_sec=interval)
        return jsonify({"success": True, "data": s.status(), "started": started})

    @app.route('/api/scheduler/stop', methods=['POST'])
    def scheduler_stop():
        s = get_scheduler()
        stopped = s.stop()
        return jsonify({"success": True, "data": s.status(), "stopped": stopped})


    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({
            'success': False,
            'error': 'Not Found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        return jsonify({
            'success': False,
            'error': 'Internal Server Error'
        }), 500

