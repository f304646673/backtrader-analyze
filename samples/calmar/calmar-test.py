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


class St(bt.SignalStrategy):
    params = (
    )

    def __init__(self):
        ma1, ma2, = bt.ind.SMA(period=15), bt.ind.SMA(period=50)    # 创建两个移动平均线指标，周期分别为 15 和 50天
        self.signal_add(bt.signal.SIGNAL_LONG, bt.ind.CrossOver(ma1, ma2))  # 创建交叉信号，当 ma1 上穿 ma2 时产生买入信号

    def next2(self):
        pass


def runstrat(args=None):
    args = parse_args(args) # 解析参数

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'  # 日期时间格式
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):    # 获取开始日期和结束日期
        if a:   # 如果日期不为空
            strpfmt = dtfmt + tmfmt * ('T' in a)    # 日期时间格式
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)  # 将日期时间字符串转换为 datetime 对象

    # Data feed
    data0 = bt.feeds.YahooFinanceCSVData(dataname=args.data0, **kwargs) # 创建数据源
    cerebro.adddata(data0)  # 添加数据源

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')')) # 创建 Broker

    cerebro.addanalyzer(bt.analyzers.Calmar)    # 添加分析器
    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))   # 创建 Sizer

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))   # 添加策略

    # Execute
    st0 = cerebro.run(**eval('dict(' + args.cerebro + ')'))[0]  # 运行策略
    i = 1
    for k, v in st0.analyzers.calmar.get_analysis().items():    # 输出分析结果
        print(i, ': '.join((str(k), str(v))))
        i += 1

    if args.plot:  # Plot if requested to   如果请求绘图
        cerebro.plot(**eval('dict(' + args.plot + ')')) # 绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,  # 参数默认值帮
        description=(
            'Sample Skeleton'
        )
    )

    parser.add_argument('--data0', default='../../datas/orcl-1995-2014.txt',    # 数据文件
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',   # 开始日期
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

    parser.add_argument('--plot', required=False, default='',   # 绘图参数
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
