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
from backtrader import ResamplerDaily, ResamplerWeekly, ResamplerMonthly
from backtrader import ReplayerDaily, ReplayerWeekly, ReplayerMonthly
from backtrader.utils import flushfile


class SMAStrategy(bt.Strategy):
    params = (
        ('period', 10), # 移动平均线的周期
        ('onlydaily', False),   # 是否仅在日线上应用指标
    )

    def __init__(self):
        self.sma_small_tf = btind.SMA(self.data, period=self.p.period)  # 创建移动平均线指标
        bt.indicators.MACD(self.data0)  # 创建 MACD 指标

        if not self.p.onlydaily:    # 如果不仅在日线上应用指标
            self.sma_large_tf = btind.SMA(self.data1, period=self.p.period) # 创建移动平均线指标
            bt.indicators.MACD(self.data1)  # 创建 MACD 指标

    def prenext(self):
        self.next()

    def nextstart(self):
        print('--------------------------------------------------')
        print('nextstart called with len', len(self))
        print('--------------------------------------------------')

        super(SMAStrategy, self).nextstart()

    def next(self):
        print('Strategy:', len(self))

        txt = list()
        txt.append('Data0')
        txt.append('%04d' % len(self.data0))
        dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
        txt.append('{:f}'.format(self.data.datetime[0]))
        txt.append('%s' % self.data.datetime.datetime(0).strftime(dtfmt))
        # txt.append('{:f}'.format(self.data.open[0]))
        # txt.append('{:f}'.format(self.data.high[0]))
        # txt.append('{:f}'.format(self.data.low[0]))
        txt.append('{:f}'.format(self.data.close[0]))
        # txt.append('{:6d}'.format(int(self.data.volume[0])))
        # txt.append('{:d}'.format(int(self.data.openinterest[0])))
        # txt.append('{:f}'.format(self.sma_small[0]))
        print(', '.join(txt))

        if len(self.datas) > 1 and len(self.data1):
            txt = list()
            txt.append('Data1')
            txt.append('%04d' % len(self.data1))
            dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
            txt.append('{:f}'.format(self.data1.datetime[0]))
            txt.append('%s' % self.data1.datetime.datetime(0).strftime(dtfmt))
            # txt.append('{}'.format(self.data1.open[0]))
            # txt.append('{}'.format(self.data1.high[0]))
            # txt.append('{}'.format(self.data1.low[0]))
            txt.append('{}'.format(self.data1.close[0]))
            # txt.append('{}'.format(self.data1.volume[0]))
            # txt.append('{}'.format(self.data1.openinterest[0]))
            # txt.append('{}'.format(float('NaN')))
            print(', '.join(txt))


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro()  # 创建一个 Cerebro 引擎

    # Add a strategy
    if not args.indicators: # 如果不需要添加指标
        cerebro.addstrategy(bt.Strategy)    # 添加策略
    else:
        cerebro.addstrategy(    # 添加策略
            SMAStrategy,

            # args for the strategy
            period=args.period, # 移动平均线的周期
            onlydaily=args.onlydaily,   # 是否仅在日线上应用指标
        )

    # Load the Data
    datapath = args.dataname or '../../datas/2006-day-001.txt'
    data = btfeeds.BacktraderCSVData(   # 创建数据源
        dataname=datapath)

    tframes = dict( # 时间周期字典
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)

    # Handy dictionary for the argument timeframe conversion
    # Resample the data
    if args.noresample: # 如果不需要重采样
        datapath = args.dataname2 or '../../datas/2006-week-001.txt'
        data2 = btfeeds.BacktraderCSVData(  # 创建数据源
            dataname=datapath)
    else:
        if args.oldrs:  # 如果使用旧的重采样
            if args.replay: # 如果重放
                data2 = bt.DataReplayer(    # 创建数据重放器
                    dataname=data,
                    timeframe=tframes[args.timeframe],
                    compression=args.compression)
            else:
                data2 = bt.DataResampler(   # 创建数据重采样器
                    dataname=data,
                    timeframe=tframes[args.timeframe],
                    compression=args.compression)

        else:   # 使用新的重采样
            data2 = bt.DataClone(dataname=data) # 创建数据克隆器
            if args.replay:
                if args.timeframe == 'daily':   # 如果时间周期是日线
                    data2.addfilter(ReplayerDaily)  # 添加重放器，日线
                elif args.timeframe == 'weekly':    # 如果时间周期是周线
                    data2.addfilter(ReplayerWeekly) # 添加重放器，周线
                elif args.timeframe == 'monthly':   # 如果时间周期是月线
                    data2.addfilter(ReplayerMonthly)    # 添加重放器，月线
            else:
                if args.timeframe == 'daily':   # 如果时间周期是日线
                    data2.addfilter(ResamplerDaily)   # 添加重采样器，日线
                elif args.timeframe == 'weekly':    # 如果时间周期是周线
                    data2.addfilter(ResamplerWeekly)    # 添加重采样器，周线
                elif args.timeframe == 'monthly':   # 如果时间周期是月线
                    data2.addfilter(ResamplerMonthly)   # 添加重采样器，月线

    # First add the original data - smaller timeframe
    cerebro.adddata(data)   # 添加数据

    # And then the large timeframe
    cerebro.adddata(data2)  # 添加数据

    # Run over everything
    cerebro.run(runonce=not args.runnext,   # 运行策略
                preload=not args.nopreload,   # 预加载数据
                oldsync=args.oldsync,   # 使用旧的数据同步方法
                stdstats=False) # 禁用标准统计

    # Plot the result
    if args.plot:
        cerebro.plot(style='bar')   # 绘制图表，样式为 bar


def parse_args():
    parser = argparse.ArgumentParser(   # 创建一个参数解析器
        description='Pandas test script')

    parser.add_argument('--dataname', default='', required=False,   # 数据文件路径
                        help='File Data to Load')

    parser.add_argument('--dataname2', default='', required=False,  # 数据文件路径
                        help='Larger timeframe file to load')

    parser.add_argument('--runnext', action='store_true',   # 是否运行下一个
                        help='Use next by next instead of runonce')

    parser.add_argument('--nopreload', action='store_true',   # 是否预加载数据
                        help='Do not preload the data')

    parser.add_argument('--oldsync', action='store_true',   # 是否使用旧的数据同步方法
                        help='Use old data synchronization method')

    parser.add_argument('--oldrs', action='store_true',  # 是否使用旧的重采样
                        help='Use old resampler')

    parser.add_argument('--replay', action='store_true',    # 是否重放
                        help='Replay instead of resample')

    parser.add_argument('--noresample', action='store_true',    # 是否重采样
                        help='Do not resample, rather load larger timeframe')

    parser.add_argument('--timeframe', default='weekly', required=False,    # 时间周期
                        choices=['daily', 'weekly', 'monthly'],
                        help='Timeframe to resample to')

    parser.add_argument('--compression', default=1, required=False, type=int,   # 压缩比例
                        help='Compress n bars into 1')

    parser.add_argument('--indicators', action='store_true',    # 是否添加指标
                        help='Wether to apply Strategy with indicators')

    parser.add_argument('--onlydaily', action='store_true',   # 是否仅在日线上应用指标
                        help='Indicator only to be applied to daily timeframe')

    parser.add_argument('--period', default=10, required=False, type=int,   # 移动平均线的周期
                        help='Period to apply to indicator')

    parser.add_argument('--plot', required=False, action='store_true',  # 是否绘图
                        help='Plot the chart')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
