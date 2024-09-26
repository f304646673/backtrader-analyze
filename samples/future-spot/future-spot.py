#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import random
import backtrader as bt


# The filter which changes the close price
def close_changer(data, *args, **kwargs):   # 定义一个函数，用于改变数据源的 close 字段
    data.close[0] += 50.0 * random.randint(-1, 1)   # 随机改变 close 字段的值
    return False  # length of stream is unchanged


# override the standard markers
class BuySellArrows(bt.observers.BuySell):  # 继承自 bt.observers.BuySell 类
    plotlines = dict(buy=dict(marker='$\u21E7$', markersize=12.0),  # 重写 plotlines 属性
                     sell=dict(marker='$\u21E9$', markersize=12.0))


class St(bt.Strategy):
    def __init__(self):
        bt.obs.BuySell(self.data0, barplot=True)  # done here for
        BuySellArrows(self.data1, barplot=True)  # different markers per data   

    def next(self):
        if not self.position:   # 没有持仓
            if random.randint(0, 1):    # 随机买入
                self.buy(data=self.data0)   # 买入
                self.entered = len(self)    # 记录买入时的长度

        else:  # in the market  # 有持仓
            if (len(self) - self.entered) >= 10:    # 持仓 10 天后卖出
                self.sell(data=self.data1)  # 卖出


def runstrat(args=None):
    args = parse_args(args)
    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    dataname = '../../datas/2006-day-001.txt'  # data feed  数据文件路径

    data0 = bt.feeds.BacktraderCSVData(dataname=dataname, name='data0') # 创建数据源
    cerebro.adddata(data0)  # 添加数据源

    data1 = bt.feeds.BacktraderCSVData(dataname=dataname, name='data1') # 创建数据源
    data1.addfilter(close_changer)  # 添加过滤器
    if not args.no_comp:    # 如果不使用补偿
        data1.compensate(data0) # 设置补偿
    data1.plotinfo.plotmaster = data0   # 设置 plotmaster
    if args.sameaxis:   # 如果使用相同的坐标轴
        data1.plotinfo.sameaxis = True  # 设置 sameaxis
    cerebro.adddata(data1)  # 添加数据源

    cerebro.addstrategy(St)  # sample strategy  添加策略

    cerebro.addobserver(bt.obs.Broker)  # removed below with stdstats=False 添加观察者
    cerebro.addobserver(bt.obs.Trades)  # removed below with stdstats=False 添加观察者

    cerebro.broker.set_coc(True)    # 设置 coc, Close on Close
    cerebro.run(stdstats=False)  # execute  运行策略
    cerebro.plot(volume=False)  # and plot  绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=('Compensation example'))

    parser.add_argument('--no-comp', required=False, action='store_true')   # 是否使用补偿
    parser.add_argument('--sameaxis', required=False, action='store_true')  # 是否使用相同的坐标轴
    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
