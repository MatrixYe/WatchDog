# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         m_td
# Author:       yepeng
# Date:         2024/10/29 23:18
# Description: 检测TD异动
# -------------------------------------------------------------------------------

import json
import time

import pandas as pd
import requests as r

from utils.logger import MyLogger
from utils.util import load_toml_config

lg = MyLogger.new()


# noinspection PyMethodMayBeStatic
class Strategy:
    def __init__(self, **kwargs):
        self.symbols: [] = kwargs.get('symbols')
        self.interval: str = kwargs.get('interval')
        self.feishu: str = kwargs.get('feishu')
        self.slp: int = kwargs.get('slp')
        self.side: str = kwargs.get('side')

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
        url = f'https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
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

    # 计算TD9技术指标
    def cal_td_sequential(self, data: list):
        columns = ['open_time', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(data, columns=columns)
        df['down'] = 0
        df['up'] = 0

        for i in range(4, len(df)):
            if df['close'][i] < df['close'][i - 4]:
                df.loc[i, 'down'] = df.loc[i - 1, 'down'] + 1 if df.loc[i - 1, 'down'] >= 0 else 1
            else:
                df.loc[i, 'down'] = 0
            if df['close'][i] > df['close'][i - 4]:
                df.loc[i, 'up'] = df.loc[i - 1, 'up'] + 1 if df.loc[i - 1, 'up'] >= 0 else 1
            else:
                df.loc[i, 'up'] = 0

        return df[['close', 'down', 'up']]

    # 核心方法
    def handle_symbol(self, symbol: str):
        kl = self.get_kline(symbol, self.interval, 30)
        if not kl:
            return
        df_td = self.cal_td_sequential(kl)
        last_down = df_td['down'].iloc[-1]
        last_up = df_td['up'].iloc[-1]
        price = df_td['close'].iloc[-1]
        if last_up > 0:
            lg.info(f"TD9指标: symbol:{symbol} interval:{self.interval} price:{price} up:{last_up} ")
        if last_down > 0:
            lg.info(f"TD9指标: symbol:{symbol} interval:{self.interval} price:{price} down:{last_down} ")

        if last_up in [9, 13] and (self.side == 'all' or self.side == 'up'):
            msg = f"【TD异动】symbol:{symbol} interval:{self.interval} price:{price} TD up={last_up} => Sell"
            lg.info(msg)
            self.send_feishu(msg)

        if last_down in [9, 13] and (self.side == 'all' or self.side == 'down'):
            msg = f"【TD异动】symbol:{symbol} interval:{self.interval} price:{price},TD down={last_down} => Buy"
            lg.info(msg)
            self.send_feishu(msg)

    # 启动把手
    def run(self):
        # self.send_feishu("【系统消息】TD9指标监控启动")
        [lg.info(f"启动TD9监控 Dex:币安 Symbol:{a}") for a in self.symbols]
        lg.info(f"启动参数：interval={self.interval}")
        lg.info(f"启动参数：slp={self.slp}")
        lg.info(f"启动参数：side={self.side}")
        while True:
            for symbol in self.symbols:
                self.handle_symbol(symbol)
                time.sleep(3)
            time.sleep(self.slp)

    def debug(self):
        [lg.info(f"启动TD9监控 Dex:币安 Symbol:{a}") for a in self.symbols]
        lg.info(f"启动参数：interval={self.interval}")
        lg.info(f"启动参数：slp={self.slp}")
        lg.info(f"启动参数：side={self.side}")
        # self.handle_symbol('SOLUSDT')


def main():
    conf = load_toml_config()

    config = {
        'symbols': conf['TD9']['symbols'],
        'interval': conf['TD9']['interval'],
        'feishu': conf['TD9']['feishu'],
        'slp': conf['TD9']['slp'],
        'side': conf['TD9']['side'],
    }

    lg.info(json.dumps(config, indent=4))
    strat = Strategy(**config)
    strat.run()


if __name__ == '__main__':
    main()
