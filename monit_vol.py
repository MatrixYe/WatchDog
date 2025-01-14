# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         bigvol
# Author:       yepeng
# Date:         2024/9/11 01:58
# Description:监控成交量异动
# -------------------------------------------------------------------------------
import json
import time

import pandas as pd
import requests as r

from utils.logger import MyLogger
from utils.util import load_toml_config


lg = MyLogger.new()

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


# 小数位格式化
def rd(v: float, d: int = 4):
    return round(v, d)


# noinspection PyMethodMayBeStatic
class Strategy:
    def __init__(self, **kwargs):
        # 目标 比如BTCUSDT
        self.symbols: list = kwargs.get('symbols')  # type: ignore
        # k线周期，比如1d
        self.interval: str = kwargs.get('interval')  # type: ignore
        # 飞书消息推送机器人地址
        self.feishu: str = kwargs.get('feishu')  # type: ignore
        # 定时循环查询
        self.slp: int = kwargs.get('slp')  # type: ignore
        # 关键参数，交易量倍数阈值，如2.0表示交易量超过2.5倍就报警
        self.x: float = kwargs.get('x')  # type: ignore
        self.n: int = kwargs.get('n')  # type: ignore

    # 消息推送，飞书
    def send_feishu(self, msg: str):
        if not self.feishu or not msg:
            return

        date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:
            text = {
                "msg_type": "text",
                "content": {
                    "text": f"{date}\n{msg}"
                }
            }
            r.post(url=self.feishu, json=text)
        except Exception as e:
            lg.error(e)

    # 获取k线数据，从币安接口
    def get_kline(self, symbol: str, interval: str, limit: int):
        url = f'https://data-api.binance.vision/api/v3/klines?symbol={
            symbol}&interval={interval}&limit={limit}'
        resp = r.get(url)
        if not resp:
            return None
        if resp.status_code != 200:
            lg.info(f'code:{resp.status_code}')
            lg.info(f'resp:{resp.text}')
            return None
        data = resp.json()
        bars = []
        for x in data:
            open_time = x[0]
            open_ = float(x[1])
            high = float(x[2])
            low = float(x[3])
            close = float(x[4])
            volume = float(x[5])
            bars.append((open_time, open_, high, low, close, volume))
        return bars

    # 计算平均成交量
    def cal_vol_ma(self, data: list, n: int):
        # 定义列名称
        columns = ['open_time', 'open', 'high', 'low', 'close', 'volume']

        # 将数据转换为 DataFrame
        df = pd.DataFrame(data, columns=columns)
        # 将 open_time 列的时间戳转换为日期时间格式（毫秒级）
        df['date_time'] = pd.to_datetime(df['open_time'], unit='ms')
        # 计算周期为 n 的成交量平均值
        df['vol_ma'] = df['volume'].rolling(window=n).mean()
        # 计算成交量与上一个平均成交量的比值
        df['vol_ratio'] = df['volume'] / df['vol_ma'].shift(1)
        return df

    # 核心方法
    def _core(self, symbol):
        kl = self.get_kline(symbol, self.interval, 30)
        if not kl:
            return
        df = self.cal_vol_ma(kl, n=self.n)
        row = df.iloc[-1]
        date_time = row['date_time']
        volume = row['volume']
        vol_ma = row['vol_ma']
        vol_ratio = row['vol_ratio']
        msg = f"标的:{symbol} 周期{self.interval} 成交量:{volume} 平均成交量:{
            vol_ma} 取样区间{self.n} 交易量变动倍数:{rd(vol_ratio, 2)}G"
        lg.info(msg)
        if vol_ratio >= self.x:
            lg.info(msg)
            self.send_feishu(msg)

    def init_system(self):
        lg.info('系统自检... ...')
        if self.x <= 1:
            raise Exception('x is miss,must x>=1')
        if not self.feishu:
            lg.warning('feishu is miss')
        if self.slp <= 0:
            raise Exception('slp is error')
        lg.info('系统自检完成')
        lg.info(f"目标货币:{self.symbols}")
        lg.info(f"K线周期:{self.interval}")
        lg.info(f"交易量倍数阈值:{self.x}")
        lg.info(f"平均值取样空间大小:{self.n}")
        lg.info(f"循环检测周期: {self.slp}s")

    # 启动把手
    def run(self):
        # self.send_feishu("【系统消息】成交量指标监控启动")

        self.init_system()
        while True:
            for s in self.symbols:
                self._core(s)
            time.sleep(self.slp)


def main():
    conf = load_toml_config()

    args = {
        'symbols': conf['VOL']['symbols'],
        'interval': conf['VOL']['interval'],
        'x': conf['VOL']['x'],
        'feishu': conf['VOL']['feishu'],
        'slp': conf['VOL']['slp'],
        'n': conf['VOL']['n']
    }
    lg.info(json.dumps(args, indent=4))
    st = Strategy(**args)
    st.run()


# 测试模式
def debug():
    pass


if __name__ == '__main__':
    main()
