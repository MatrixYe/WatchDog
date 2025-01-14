# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         monit_rsi
# Author:       yepeng
# Date:         2024/12/26 11:23
# Description:
# -------------------------------------------------------------------------------

import json
import time

import numpy as np
import pandas as pd
import requests as r
import talib

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
        # k线周期，比如4h
        self.interval: str = kwargs.get('interval')  # type: ignore
        # 飞书消息推送机器人地址
        self.feishu: str = kwargs.get('feishu')  # type: ignore
        # 定时循环查询
        self.slp: int = kwargs.get('slp')  # type: ignore
        # 关键参数，RSI 预警的上下阈值
        self.up: int = kwargs.get('up')  # type: ignore
        self.down: int = kwargs.get('down')  # type: ignore
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

    # 核心方法
    def _core(self, symbol):
        kl = self.get_kline(symbol, self.interval, 30)
        if not kl:
            return
        closess = [a[4] for a in kl]
        rsi = talib.RSI(np.array(closess), 6)
        lg.info(f"标的:{symbol} 周期{self.interval} Last RSI:{rsi[-1]}")
        last_rsi = rsi[-1]
        if last_rsi >= self.up:
            msg = f"标的:{symbol} Last RSI:{rsi[-1]} => 超买 => 开空"
            lg.info(msg)
            self.send_feishu(msg)

        if last_rsi <= self.down:
            msg = f"标的:{symbol} Last RSI:{rsi[-1]} => 超卖 => 开多"
            lg.info(msg)
            self.send_feishu(msg)

    def init_system(self):
        lg.info('系统自检... ...')
        if self.n <= 1:
            raise Exception('n is miss,must x>=1,default is 6')
        if not self.feishu:
            lg.warning('feishu is miss')
        if self.slp <= 0:
            raise Exception('slp is error')
        lg.info('系统自检完成')
        lg.info(f"目标货币:{self.symbols}")
        lg.info(f"K线周期:{self.interval}")
        lg.info(f"RSI参数:{self.n}")
        lg.info(f"循环周期: {self.slp}s")

    # 启动把手
    def run(self):

        self.init_system()
        # self._core("SUIUSDT")
        while True:
            for s in self.symbols:
                self._core(s)
            time.sleep(self.slp)


def main():
    conf = load_toml_config()

    args = {
        'slp': conf['RSI']['slp'],
        'symbols': conf['RSI']['symbols'],
        'interval': conf['RSI']['interval'],
        'up': conf['RSI']['up'],
        'down': conf['RSI']['down'],
        'n': conf['RSI']['n'],
        'feishu': conf['RSI']['feishu']
    }
    lg.info(json.dumps(args, indent=4))
    st = Strategy(**args)
    st.run()


if __name__ == '__main__':
    main()
