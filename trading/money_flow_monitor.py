"""
资金流入监控器
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy import func

from data_collection.longport_client import LongPortClient
from database.db_manager import DatabaseManager
from database.models import StockInfo, MinuteData, MoneyFlowAlert, TradingSignal
from utils.logger import logger
from utils.email_notifier import EmailNotifier


class MoneyFlowMonitor:
    """资金流入监控器"""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager, client: LongPortClient):
        """
        初始化资金流入监控器
        
        Args:
            config: 配置字典
            db_manager: 数据库管理器
            client: LongPort客户端
        """
        self.config = config
        self.db = db_manager
        self.client = client
        
        # 监控配置
        monitor_config = config.get('money_flow_monitor', {})
        self.enabled = monitor_config.get('enabled', False)
        self.interval = monitor_config.get('interval', 60)  # 监控间隔（秒）
        self.lookback_minutes = monitor_config.get('lookback_minutes', 30)  # 回溯分钟数
        
        # 告警阈值
        self.volume_ratio_threshold = monitor_config.get('volume_ratio_threshold', 3.0)  # 成交量倍数阈值
        self.turnover_ratio_threshold = monitor_config.get('turnover_ratio_threshold', 3.0)  # 成交额倍数阈值
        self.price_change_threshold = monitor_config.get('price_change_threshold', 0.05)  # 价格变动阈值（5%）

        # 自动交易配置
        self.auto_trade = monitor_config.get('auto_trade', False)  # 是否自动生成买入信号
        self.send_email = monitor_config.get('send_email', False)  # 是否发送邮件

        # 邮件通知
        if self.send_email:
            email_config = config.get('notification', {}).get('email', {})
            self.email_notifier = EmailNotifier(email_config)
        else:
            self.email_notifier = None
        
        # 监控股票列表
        self.watch_list: List[str] = []
        
        # 缓存：用于存储历史数据，避免频繁查询数据库
        self.minute_data_cache: Dict[str, List[MinuteData]] = defaultdict(list)
        
        logger.info("资金流入监控器初始化完成")
    
    def load_watch_list(self, symbols: Optional[List[str]] = None):
        """
        加载监控股票列表
        
        Args:
            symbols: 股票代码列表，如果为None则从数据库加载高分股票
        """
        if symbols:
            self.watch_list = symbols
            logger.info(f"加载监控列表: {len(symbols)} 只股票")
        else:
            # 从数据库加载所有港股通股票
            with self.db.get_session() as session:
                from database.models import StockInfo

                # 获取所有港股通股票
                stocks = session.query(StockInfo).filter(
                    StockInfo.market == 'HK',
                    StockInfo.is_hk_connect == True
                ).all()

                if not stocks:
                    logger.warning("没有找到港股通股票，监控列表为空")
                    return

                self.watch_list = [stock.symbol for stock in stocks]
                logger.info(f"加载所有港股通股票: {len(self.watch_list)} 只")
    
    def fetch_minute_data(self, symbol: str, count: int = 60) -> List[Dict[str, Any]]:
        """
        获取分钟K线数据

        Args:
            symbol: 股票代码
            count: 获取数量

        Returns:
            分钟数据字典列表
        """
        try:
            # 从LongPort获取1分钟K线数据
            candlesticks = self.client.get_candlesticks(symbol, '1min', count)

            if not candlesticks:
                return []

            minute_data_list = []
            for candle in candlesticks:
                # 使用字典而不是ORM对象，避免session问题
                minute_data = {
                    'symbol': symbol,
                    'trade_datetime': candle.timestamp,
                    'open': float(candle.open),
                    'high': float(candle.high),
                    'low': float(candle.low),
                    'close': float(candle.close),
                    'volume': float(candle.volume),
                    'turnover': float(candle.turnover)
                }
                minute_data_list.append(minute_data)

            return minute_data_list

        except Exception as e:
            logger.error(f"获取分钟数据失败 {symbol}: {e}")
            return []
    
    def save_minute_data(self, minute_data_list: List[Dict[str, Any]]):
        """
        保存分钟数据到数据库

        Args:
            minute_data_list: 分钟数据字典列表
        """
        if not minute_data_list:
            return

        try:
            with self.db.get_session() as session:
                for data_dict in minute_data_list:
                    # 检查是否已存在
                    existing = session.query(MinuteData).filter(
                        MinuteData.symbol == data_dict['symbol'],
                        MinuteData.trade_datetime == data_dict['trade_datetime']
                    ).first()

                    if not existing:
                        # 从字典创建ORM对象
                        data = MinuteData(**data_dict)
                        session.add(data)

                session.commit()
                logger.debug(f"保存 {len(minute_data_list)} 条分钟数据")

        except Exception as e:
            logger.error(f"保存分钟数据失败: {e}")
    
    def calculate_money_flow_indicators(self, symbol: str, minute_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算资金流入指标

        Args:
            symbol: 股票代码
            minute_data_list: 分钟数据字典列表

        Returns:
            指标字典
        """
        if len(minute_data_list) < 2:
            return {}

        # 最新一分钟数据
        latest = minute_data_list[-1]

        # 计算平均成交量和成交额（排除最新一分钟）
        historical_data = minute_data_list[:-1]

        # 直接访问字典，无需担心session问题
        avg_volume = sum(d.get('volume', 0) for d in historical_data) / len(historical_data) if historical_data else 0
        avg_turnover = sum(d.get('turnover', 0) for d in historical_data) / len(historical_data) if historical_data else 0

        latest_volume = latest.get('volume', 0)
        latest_turnover = latest.get('turnover', 0)
        latest_close = latest.get('close', 0)

        # 计算倍数
        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0
        turnover_ratio = latest_turnover / avg_turnover if avg_turnover > 0 else 0

        # 计算价格变动
        first_close = minute_data_list[0].get('close', 0)
        price_change_pct = (latest_close - first_close) / first_close if first_close > 0 else 0

        # 获取交易时间
        alert_datetime = latest.get('trade_datetime', datetime.now())

        return {
            'symbol': symbol,
            'current_volume': latest_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'current_turnover': latest_turnover,
            'avg_turnover': avg_turnover,
            'turnover_ratio': turnover_ratio,
            'current_price': latest_close,
            'price_change_pct': price_change_pct * 100,  # 转换为百分比
            'alert_datetime': alert_datetime
        }
    
    def check_alert_conditions(self, indicators: Dict[str, Any]) -> Optional[str]:
        """
        检查是否触发告警条件
        
        Args:
            indicators: 指标字典
            
        Returns:
            告警类型，如果不触发则返回None
        """
        volume_ratio = indicators.get('volume_ratio', 0)
        turnover_ratio = indicators.get('turnover_ratio', 0)
        price_change_pct = abs(indicators.get('price_change_pct', 0))
        
        # 成交量激增
        if volume_ratio >= self.volume_ratio_threshold:
            return 'volume_surge'
        
        # 成交额激增
        if turnover_ratio >= self.turnover_ratio_threshold:
            return 'turnover_surge'
        
        # 价格异动
        if price_change_pct >= self.price_change_threshold * 100:
            return 'price_surge'
        
        # 综合异动（成交量和成交额都超过阈值的80%）
        if (volume_ratio >= self.volume_ratio_threshold * 0.8 and 
            turnover_ratio >= self.turnover_ratio_threshold * 0.8):
            return 'combined'
        
        return None

    def create_alert(self, indicators: Dict[str, Any], alert_type: str) -> MoneyFlowAlert:
        """
        创建告警记录

        Args:
            indicators: 指标字典
            alert_type: 告警类型

        Returns:
            告警记录
        """
        # 获取股票名称
        stock_name = ''
        with self.db.get_session() as session:
            stock = session.query(StockInfo).filter(StockInfo.symbol == indicators['symbol']).first()
            if stock:
                stock_name = stock.name

        alert = MoneyFlowAlert(
            symbol=indicators['symbol'],
            alert_datetime=indicators['alert_datetime'],
            alert_type=alert_type,
            current_volume=indicators['current_volume'],
            avg_volume=indicators['avg_volume'],
            volume_ratio=indicators['volume_ratio'],
            current_turnover=indicators['current_turnover'],
            avg_turnover=indicators['avg_turnover'],
            turnover_ratio=indicators['turnover_ratio'],
            price_change_pct=indicators['price_change_pct'],
            current_price=indicators['current_price'],
            stock_name=stock_name,
            is_sent=False
        )

        return alert

    def save_alert(self, alert: MoneyFlowAlert):
        """
        保存告警记录到数据库

        Args:
            alert: 告警记录
        """
        try:
            with self.db.get_session() as session:
                # 检查是否已存在相同告警（5分钟内）
                recent_time = alert.alert_datetime - timedelta(minutes=5)
                existing = session.query(MoneyFlowAlert).filter(
                    MoneyFlowAlert.symbol == alert.symbol,
                    MoneyFlowAlert.alert_datetime >= recent_time
                ).first()

                if existing:
                    logger.debug(f"告警已存在，跳过: {alert.symbol}")
                    return

                session.add(alert)
                session.commit()
                logger.info(f"✅ 保存告警记录: {alert.symbol} - {alert.alert_type}")

        except Exception as e:
            logger.error(f"保存告警记录失败: {e}")

    def create_buy_signals(self, alerts: List[MoneyFlowAlert]) -> int:
        """
        根据告警创建买入信号

        Args:
            alerts: 告警记录列表

        Returns:
            创建的信号数量
        """
        if not alerts:
            return 0

        count = 0
        today = datetime.now().date()

        with self.db.get_session() as session:
            for alert in alerts:
                # 检查是否已有今日买入信号
                existing = session.query(TradingSignal).filter(
                    TradingSignal.symbol == alert.symbol,
                    TradingSignal.signal_date == today,
                    TradingSignal.signal_type == 'BUY',
                    TradingSignal.is_executed == False
                ).first()

                if existing:
                    logger.debug(f"今日已有买入信号，跳过: {alert.symbol}")
                    continue

                # 计算信号强度（基于成交量和成交额倍数）
                strength = min(1.0, (alert.volume_ratio + alert.turnover_ratio) / 10.0)

                # 创建买入信号
                signal = TradingSignal(
                    symbol=alert.symbol,
                    signal_date=today,
                    signal_type='BUY',
                    signal_strength=strength,
                    signal_price=alert.current_price,
                    source='money_flow_monitor',
                    reason=f'{alert.alert_type}: 成交量{alert.volume_ratio:.1f}x, 成交额{alert.turnover_ratio:.1f}x, 价格变动{alert.price_change_pct:+.2f}%',
                    is_executed=False
                )
                session.add(signal)
                count += 1

                logger.info(
                    f"✅ 创建买入信号: {alert.symbol} ({alert.stock_name}) | "
                    f"强度: {strength:.2f} | 价格: {alert.current_price:.2f}"
                )

            session.commit()

        return count

    def send_alerts(self, alerts: List[MoneyFlowAlert]):
        """
        发送告警邮件

        Args:
            alerts: 告警记录列表
        """
        if not alerts or not self.send_email or not self.email_notifier:
            return

        # 转换为字典格式
        alert_dicts = []
        for alert in alerts:
            alert_dicts.append({
                'symbol': alert.symbol,
                'stock_name': alert.stock_name,
                'alert_type': alert.alert_type,
                'current_price': alert.current_price,
                'price_change_pct': alert.price_change_pct,
                'volume_ratio': alert.volume_ratio,
                'turnover_ratio': alert.turnover_ratio,
                'alert_datetime': alert.alert_datetime.strftime('%Y-%m-%d %H:%M:%S')
            })

        # 发送邮件
        success = self.email_notifier.send_money_flow_alert(alert_dicts)

        if success:
            # 更新发送状态
            with self.db.get_session() as session:
                for alert in alerts:
                    db_alert = session.query(MoneyFlowAlert).filter(
                        MoneyFlowAlert.id == alert.id
                    ).first()
                    if db_alert:
                        db_alert.is_sent = True
                        db_alert.sent_at = datetime.now()
                session.commit()

    def monitor_once(self):
        """执行一次监控"""
        if not self.watch_list:
            logger.warning("监控列表为空，跳过监控")
            return

        logger.info(f"开始监控 {len(self.watch_list)} 只股票...")

        alerts = []

        for symbol in self.watch_list:
            try:
                # 获取分钟数据
                minute_data_list = self.fetch_minute_data(symbol, self.lookback_minutes)

                if not minute_data_list:
                    logger.debug(f"没有分钟数据: {symbol}")
                    continue

                # 保存分钟数据
                self.save_minute_data(minute_data_list)

                # 计算指标
                indicators = self.calculate_money_flow_indicators(symbol, minute_data_list)

                if not indicators:
                    continue

                # 检查告警条件
                alert_type = self.check_alert_conditions(indicators)

                if alert_type:
                    # 创建告警
                    alert = self.create_alert(indicators, alert_type)
                    self.save_alert(alert)
                    alerts.append(alert)

                    logger.warning(
                        f"🚨 资金流入告警: {symbol} - {alert_type} | "
                        f"成交量倍数: {indicators['volume_ratio']:.2f}x | "
                        f"成交额倍数: {indicators['turnover_ratio']:.2f}x | "
                        f"价格变动: {indicators['price_change_pct']:+.2f}%"
                    )

                # 避免请求过快
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"监控股票失败 {symbol}: {e}")
                continue

        # 处理告警
        if alerts:
            logger.info(f"发现 {len(alerts)} 个告警")

            # 自动生成买入信号
            if self.auto_trade:
                signal_count = self.create_buy_signals(alerts)
                logger.info(f"✅ 已生成 {signal_count} 个买入信号")

            # 发送邮件（可选）
            if self.send_email:
                logger.info("准备发送邮件...")
                self.send_alerts(alerts)
        else:
            logger.info("未发现异常资金流入")

    def start(self):
        """启动监控"""
        if not self.enabled:
            logger.warning("资金流入监控未启用")
            return

        logger.info("=" * 60)
        logger.info("启动资金流入监控")
        logger.info("=" * 60)
        logger.info(f"监控间隔: {self.interval}秒")
        logger.info(f"回溯时间: {self.lookback_minutes}分钟")
        logger.info(f"成交量倍数阈值: {self.volume_ratio_threshold}x")
        logger.info(f"成交额倍数阈值: {self.turnover_ratio_threshold}x")
        logger.info(f"价格变动阈值: {self.price_change_threshold * 100}%")
        logger.info("=" * 60)

        # 加载监控列表
        self.load_watch_list()

        if not self.watch_list:
            logger.error("监控列表为空，无法启动监控")
            return

        try:
            while True:
                logger.info(f"\n[{datetime.now().strftime('%H:%M:%S')}] 执行监控...")
                self.monitor_once()

                # 等待下一次监控
                logger.info(f"等待 {self.interval} 秒...")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("\n监控已停止")
        except Exception as e:
            logger.error(f"监控出错: {e}")
            raise

    def stop(self):
        """停止监控"""
        logger.info("停止资金流入监控")

