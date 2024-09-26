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

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class SMAStrategy(bt.Strategy):
    params = (
        ('period', 10), # 移动平均线的周期，默认为 10
        ('onlydaily', False),   # 是否仅在日线上应用指标，默认为 False
    )

    def __init__(self):
        self.sma = btind.SMA(self.data, period=self.p.period)   # 创建移动平均线指标

    def start(self):
        self.counter = 0    # 计数器

    def prenext(self):
        self.counter += 1   # 计数器加 1
        print('prenext len %d - counter %d' % (len(self), self.counter))

    def next(self):
        self.counter += 1   # 计数器加 1
        print('---next len %d - counter %d' % (len(self), self.counter))


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)    # 创建 Cerebro 引擎

    cerebro.addstrategy(    # 添加策略
        SMAStrategy,
        # args for the strategy
        period=args.period,
    )

    # Load the Data
    datapath = args.dataname or '../../datas//2006-day-001.txt'   # 数据文件路径
    data = btfeeds.BacktraderCSVData(   # 创建数据源
        dataname=datapath)

    tframes = dict(   # 时间框架字典
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)

    # Handy dictionary for the argument timeframe conversion
    # Resample the data
    if args.oldrp:  # 如果使用旧的数据重放
        data = bt.DataReplayer(   # 创建数据重放器
            dataname=data,  # 数据源
            timeframe=tframes[args.timeframe],  # 时间周期
            compression=args.compression)   # 压缩
    else:
        data.replay(    # 重放
            timeframe=tframes[args.timeframe],  # 时间周期
            compression=args.compression)   # 压缩

    # First add the original data - smaller timeframe
    cerebro.adddata(data)   # 添加数据源

    # Run over everything
    cerebro.run(preload=False)  # 运行策略

    # Plot the result
    cerebro.plot(style='bar')   # 绘制图表，样式为 bar


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pandas test script')

    parser.add_argument('--dataname', default='', required=False,   # 数据文件路径
                        help='File Data to Load')

    parser.add_argument('--oldrp', required=False, action='store_true',  # 是否使用旧的数据重放
                        help='Use deprecated DataReplayer')

    parser.add_argument('--timeframe', default='weekly', required=False,    # 时间周期，默认为周线
                        choices=['daily', 'weekly', 'monthly'],
                        help='Timeframe to resample to')

    parser.add_argument('--compression', default=1, required=False, type=int,   # 压缩，默认为 1
                        help='Compress n bars into 1')

    parser.add_argument('--period', default=10, required=False, type=int,   # 移动平均线的周期，默认为 10
                        help='Period to apply to indicator')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
