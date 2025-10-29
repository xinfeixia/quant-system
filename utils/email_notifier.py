"""
邮件通知模块
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any
from utils.logger import logger


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化邮件通知器
        
        Args:
            config: 邮件配置字典
        """
        self.enabled = config.get('enabled', False)
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.from_addr = config.get('from_addr', '')
        self.to_addrs = config.get('to_addrs', [])
        
        if not self.enabled:
            logger.warning("邮件通知未启用")
    
    def send_money_flow_alert(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        发送资金流入告警邮件
        
        Args:
            alerts: 告警信息列表
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.warning("邮件通知未启用，跳过发送")
            return False
        
        if not alerts:
            logger.info("没有告警信息，跳过发送")
            return False
        
        try:
            # 构建邮件内容
            subject = f"🚨 资金流入告警 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            body = self._build_alert_email_body(alerts)
            
            # 发送邮件
            return self._send_email(subject, body)
            
        except Exception as e:
            logger.error(f"发送告警邮件失败: {e}")
            return False
    
    def _build_alert_email_body(self, alerts: List[Dict[str, Any]]) -> str:
        """
        构建告警邮件正文
        
        Args:
            alerts: 告警信息列表
            
        Returns:
            邮件正文HTML
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h2 { color: #d32f2f; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th { background-color: #f44336; color: white; padding: 12px; text-align: left; }
                td { border: 1px solid #ddd; padding: 10px; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .highlight { background-color: #ffeb3b; font-weight: bold; }
                .footer { margin-top: 30px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <h2>🚨 资金流入告警通知</h2>
            <p>检测到以下股票有大量资金流入，请及时关注：</p>
            
            <table>
                <tr>
                    <th>股票代码</th>
                    <th>股票名称</th>
                    <th>告警类型</th>
                    <th>当前价格</th>
                    <th>价格变动</th>
                    <th>成交量倍数</th>
                    <th>成交额倍数</th>
                    <th>告警时间</th>
                </tr>
        """
        
        for alert in alerts:
            alert_type_map = {
                'volume_surge': '成交量激增',
                'turnover_surge': '成交额激增',
                'price_surge': '价格异动',
                'combined': '综合异动'
            }
            alert_type_text = alert_type_map.get(alert.get('alert_type', ''), alert.get('alert_type', ''))
            
            price_change = alert.get('price_change_pct', 0)
            price_change_color = 'red' if price_change > 0 else 'green'
            
            html += f"""
                <tr>
                    <td><strong>{alert.get('symbol', '')}</strong></td>
                    <td>{alert.get('stock_name', '')}</td>
                    <td class="highlight">{alert_type_text}</td>
                    <td>¥{alert.get('current_price', 0):.2f}</td>
                    <td style="color: {price_change_color};">{price_change:+.2f}%</td>
                    <td class="highlight">{alert.get('volume_ratio', 0):.2f}x</td>
                    <td class="highlight">{alert.get('turnover_ratio', 0):.2f}x</td>
                    <td>{alert.get('alert_datetime', '')}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <div class="footer">
                <p>此邮件由长桥量化交易系统自动发送，请勿回复。</p>
                <p>发送时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_email(self, subject: str, body: str) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文（HTML格式）
            
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            
            # 添加HTML正文
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 连接SMTP服务器
            logger.info(f"连接SMTP服务器: {self.smtp_server}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # 登录
            logger.info(f"登录邮箱: {self.username}")
            server.login(self.username, self.password)
            
            # 发送邮件
            logger.info(f"发送邮件到: {self.to_addrs}")
            server.send_message(msg)
            server.quit()
            
            logger.info("✅ 邮件发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        发送测试邮件
        
        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.warning("邮件通知未启用")
            return False
        
        subject = "📧 长桥量化系统 - 邮件测试"
        body = """
        <html>
        <body>
            <h2>邮件测试</h2>
            <p>这是一封测试邮件，用于验证邮件配置是否正确。</p>
            <p>如果您收到此邮件，说明邮件通知功能已正常工作。</p>
            <p>发送时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </body>
        </html>
        """
        
        return self._send_email(subject, body)

