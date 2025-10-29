"""测试Period类型"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("测试1: 直接导入Period")
try:
    from longport.openapi import Period
    print(f"  Period类型: {type(Period)}")
    print(f"  Period属性: {[x for x in dir(Period) if not x.startswith('_')]}")
except Exception as e:
    print(f"  错误: {e}")

print("\n测试2: 导入Period并使用别名")
try:
    from longport.openapi import Period as LPPeriod
    print(f"  LPPeriod类型: {type(LPPeriod)}")
    print(f"  LPPeriod属性: {[x for x in dir(LPPeriod) if not x.startswith('_')]}")
except Exception as e:
    print(f"  错误: {e}")

print("\n测试3: 导入整个模块")
try:
    import longport.openapi as lp
    print(f"  lp.Period类型: {type(lp.Period)}")
    print(f"  lp.Period属性: {[x for x in dir(lp.Period) if not x.startswith('_')]}")
except Exception as e:
    print(f"  错误: {e}")

print("\n测试4: 检查是否有内置Period")
try:
    import builtins
    if hasattr(builtins, 'Period'):
        print(f"  警告: builtins中有Period! {type(builtins.Period)}")
    else:
        print(f"  OK: builtins中没有Period")
except Exception as e:
    print(f"  错误: {e}")

print("\n测试5: 尝试使用Period.Day")
try:
    from longport.openapi import Period
    day_period = Period.Day
    print(f"  Period.Day = {day_period}")
    print(f"  类型: {type(day_period)}")
except Exception as e:
    print(f"  错误: {e}")

print("\n测试6: 检查longport版本和所有导出")
try:
    import longport
    print(f"  longport版本: {longport.__version__ if hasattr(longport, '__version__') else '未知'}")
    import longport.openapi
    exports = [x for x in dir(longport.openapi) if not x.startswith('_')]
    print(f"  longport.openapi导出: {exports[:20]}...")  # 只显示前20个
except Exception as e:
    print(f"  错误: {e}")

