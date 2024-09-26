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
import datetime

import backtrader as bt


class St(bt.Strategy):
    params = dict(
        periods=[10, 30],   # 移动平均线的周期
        matype=bt.ind.SMA,  # 移动平均线指标    
    )

    def __init__(self):
        self.cheating = self.cerebro.p.cheat_on_open # 是否在开盘时作弊
        mas = [self.p.matype(period=x) for x in self.p.periods] # 创建两个移动平均线指标
        self.signal = bt.ind.CrossOver(*mas)    # 创建交叉信号
        self.order = None

    def notify_order(self, order):
        if order.status != order.Completed: # 如果订单未完成
            return

        self.order = None
        print('{} {} Executed at price {}'.format(
            bt.num2date(order.executed.dt).date(),
            'Buy' * order.isbuy() or 'Sell', order.executed.price)
        )

    def operate(self, fromopen):
        if self.order is not None:
            return
        if self.position:   # 如果有持仓
            if self.signal < 0: # 如果信号小于 0
                self.order = self.close()   # 平仓
        elif self.signal > 0:   # 如果信号大于 0
            print('{} Send Buy, fromopen {}, close {}'.format(
                self.data.datetime.date(),
                fromopen, self.data.close[0])
            )
            self.order = self.buy() # 买入

    def next(self):
        print('{} next, open {} close {}'.format(
            self.data.datetime.date(),
            self.data.open[0], self.data.close[0])
        )

        if self.cheating:   # 如果作弊
            return
        self.operate(fromopen=False)    # 操作

    def next_open(self):
        if not self.cheating:   # 如果不作弊
            return
        self.operate(fromopen=True) # 操作


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):    # 获取开始日期和结束日期
        if a:   # 如果存在
            strpfmt = dtfmt + tmfmt * ('T' in a)    # 日期时间格式
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)  # 将字符串转换为日期时间对象

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)   # 创建数据源
    cerebro.adddata(data0)  # 将数据添加到 Cerebro 引擎

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')')) # 创建 Broker

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))   # 创建 Sizer

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))  # 创建策略

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))   # 运行策略

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')')) # 绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, # 参数默认值帮助格式
        description=(
            'Cheat-On-Open Sample'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt', # 数据文件路径
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',   # 起始日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='', # 结束日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',    # Cerebro 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='', # Broker 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',  # Sizer 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',  # 策略参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',   # 是否绘图
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
