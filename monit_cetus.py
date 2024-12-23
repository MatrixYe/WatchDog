# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         monit_cetus 
# Author:       yepeng
# Date:         2024/12/23 11:57
# Description: 
# -------------------------------------------------------------------------------

# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         m_cetus_apr
# Author:       yepeng
# Date:         2024/10/21 16:38
# Description: 监控cetus上的Pool，挑选出APR最高的项目
# -------------------------------------------------------------------------------
import time

import requests as r
import schedule

from utils.logger import MyLogger
from utils.util import load_toml_config

lg = MyLogger.new()


# 网络请求
def to_request(method: str, url: str, params: dict = None, json: dict = None, data: dict = None):
    lg.debug(f"METHOD: {method} URL: {url} PARAMS: {params} JSON_: {json}")
    resp = r.request(method=method, url=url, params=params, json=json, data=data)
    lg.debug(f"STATUS_CODE: {resp.status_code}")
    return resp


# 小数位格式化
def rd(v: float, d: int = 4):
    return round(v, d)


def send_feishu(msg: str):
    if not feishu or not msg:
        return

    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        text = {
            "msg_type": "text",
            "content": {
                "text": f"{date}\n{msg}"
            }
        }
        r.post(url=feishu, json=text)
    except Exception as e:
        lg.error(e)


def handle_data(data) -> (str | None, float | None):
    if data is None:
        return None, None

    pools = data['pools']
    if not pools:
        return None, None
    target_symbol = ''
    max_total_apr = 0
    for p in pools:
        symbol = p['symbol']
        total_apr = float(p['total_apr'])
        rewarder_apr = p['rewarder_apr']

        if not rewarder_apr:
            # 跳过没有任何挖矿奖励的Pool
            continue
        no_reward = all([a in ['0%', ''] for a in rewarder_apr])

        if no_reward:
            # lg.info(f'{symbol} no mint reward -> pass')
            continue

        total_apr = 100 * rd(total_apr, 4)
        lg.info(f'{symbol} total apr:{total_apr},reward apr:{rewarder_apr}')
        if total_apr > max_total_apr:
            max_total_apr = total_apr
            target_symbol = symbol
    return target_symbol, max_total_apr


def job():
    u = "https://api-sui.cetus.zone/v2/sui/statistics_pools?order_by=-vol"
    resp = to_request('GET', url=u)
    if resp.status_code == 200:
        result = resp.json()
        if result['code'] == 200:
            data = result['data']
            target_symbol, max_total_apr = handle_data(data)
            if not target_symbol or not max_total_apr:
                lg.error(f"获取最大APR失败 {target_symbol} {max_total_apr}")
                return
            # lg.info(f"find target_symbol:{target_symbol} max_total_apr:{max_total_apr}%")
            msg = f"{target_symbol} 24APR: {max_total_apr}% 今日Cetus APR最大项目: "
            lg.info(msg)
            if max_total_apr <= min_apr:
                lg.info(f"APR小于预设最低值，跳过")
                return
            send_feishu(msg=msg)
        else:
            lg.error(f"net error:{resp.status_code}\n{resp.text}")


if __name__ == '__main__':

    conf = load_toml_config()
    feishu = conf["Cetus"]["feishu"]
    t = conf["Cetus"]["t"]
    min_apr = conf["Cetus"]["min_apr"]

    send_feishu("【系统消息】Cetus 最大APR指标监控启动")
    lg.info(f"启动参数:{t=} {feishu=} {min_apr=}")
    schedule.every().day.at(t).do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
