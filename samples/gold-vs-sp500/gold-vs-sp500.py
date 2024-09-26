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

# Reference
# https://estrategiastrading.com/oro-bolsa-estadistica-con-python/

import argparse
import datetime

import scipy.stats

import backtrader as bt


class PearsonR(bt.ind.PeriodN):
    _mindatas = 2  # hint to the platform   # 数据源的最小数量

    lines = ('correlation',)    # 定义指标的字段
    params = (('period', 20),)  # 移动平均线的周期

    def next(self):
        c, p = scipy.stats.pearsonr(self.data0.get(size=self.p.period), # 计算两个数据源的皮尔逊相关系数
                                    self.data1.get(size=self.p.period))

        self.lines.correlation[0] = c   # 将计算结果赋值给指标字段


class MACrossOver(bt.Strategy):
    params = (
        ('ma', bt.ind.MovAv.SMA),   # 移动平均线的类型，默认为 SMA
        ('pd1', 20),    # 第一个数据源的周期，默认为 20
        ('pd2', 20),    # 第二个数据源的周期，默认为 20
    )

    def __init__(self):
        ma1 = self.p.ma(self.data0, period=self.p.pd1, subplot=True)    # 创建移动平均线指标
        self.p.ma(self.data1, period=self.p.pd2, plotmaster=ma1)    # 创建移动平均线指标
        PearsonR(self.data0, self.data1)    # 创建皮尔逊相关系数指标


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):    # 获取开始日期和结束日期
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    if not args.offline:    # 如果不是离线模式
        YahooData = bt.feeds.YahooFinanceData   # 使用 YahooFinanceData
    else:
        YahooData = bt.feeds.YahooFinanceCSVData    # 使用 YahooFinanceCSVData

    # Data feeds
    data0 = YahooData(dataname=args.data0, **kwargs)    # 创建数据源
    # cerebro.adddata(data0)
    cerebro.resampledata(data0, timeframe=bt.TimeFrame.Weeks)   # 重采样数据

    data1 = YahooData(dataname=args.data1, **kwargs)    # 创建数据源
    # cerebro.adddata(data1)
    cerebro.resampledata(data1, timeframe=bt.TimeFrame.Weeks)   # 重采样数据
    data1.plotinfo.plotmaster = data0   # 设置主数据源

    # Broker
    kwargs = eval('dict(' + args.broker + ')')  # 从命令行参数中获取 Broker 参数
    cerebro.broker = bt.brokers.BackBroker(**kwargs)    # 创建 Broker

    # Sizer
    kwargs = eval('dict(' + args.sizer + ')')   # 从命令行参数中获取 Sizer 参数
    cerebro.addsizer(bt.sizers.FixedSize, **kwargs)   # 创建 Sizer

    # Strategy
    if True:
        kwargs = eval('dict(' + args.strat + ')')
        cerebro.addstrategy(MACrossOver, **kwargs)  # 创建策略

    cerebro.addobserver(bt.observers.LogReturns2,   # 添加观察者, 记录收益率
                        timeframe=bt.TimeFrame.Weeks,
                        compression=20)

    # Execute
    cerebro.run(**(eval('dict(' + args.cerebro + ')')))   # 运行策略

    if args.plot:  # Plot if requested to   如果请求绘图
        cerebro.plot(**(eval('dict(' + args.plot + ')')))   # 绘制图表


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Gold vs SP500 from '
            'https://estrategiastrading.com/oro-bolsa-estadistica-con-python/')
    )

    parser.add_argument('--data0', required=False, default='SPY',   # 第一个数据源
                        metavar='TICKER', help='Yahoo ticker to download')

    parser.add_argument('--data1', required=False, default='GLD',   # 第二个数据源
                        metavar='TICKER', help='Yahoo ticker to download')

    parser.add_argument('--offline', required=False, action='store_true',   # 是否使用离线文件
                        help='Use the offline files')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='2005-01-01',  # 开始日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2016-01-01',   # 结束日期
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
