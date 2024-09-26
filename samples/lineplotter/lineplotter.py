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
    params = (
        ('ondata', False),  # 是否在数据上绘制指标，默认为 False
    )

    def __init__(self):
        if not self.p.ondata:
            a = self.data.high - self.data.low  # 最高点和最低点的差
        else:
            a = 1.05 * (self.data.high + self.data.low) / 2.0   # 最高点和最低点的平均值

        b = bt.LinePlotterIndicator(a, name='hilo') # 创建指标, 用于绘制线图
        b.plotinfo.subplot = not self.p.ondata  # 是否在子图上绘制指标


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    dkwargs = dict()
    # Get the dates from the args
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 获取开始日期
        dkwargs['fromdate'] = fromdate
    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 获取结束日期
        dkwargs['todate'] = todate

    data = bt.feeds.BacktraderCSVData(dataname=args.data, **dkwargs)    # 创建数据源
    cerebro.adddata(data)   # 添加数据源

    cerebro.addstrategy(St, ondata=args.ondata)   # 添加策略
    cerebro.run(stdstats=False) # 运行策略

    # Plot if requested
    if args.plot:   # 如果需要绘图
        pkwargs = dict(style='bar') # 默认样式为 bar
        if args.plot is not True:  # evals to True but is not True  如果 plot 不是 True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed  将 plot 参数转换为字典
            pkwargs.update(npkwargs)    # 更新参数

        cerebro.plot(**pkwargs) # 绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Fake Indicator')

    parser.add_argument('--data', '-d', # 数据文件路径
                        default='../../datas/2005-2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f', # 起始日期
                        default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--ondata', '-o', action='store_true',  # 是否在数据上绘制指标
                        help='Plot fake indicator on the data')

    parser.add_argument('--plot', '-p', nargs='?', required=False,  # 绘图参数
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
