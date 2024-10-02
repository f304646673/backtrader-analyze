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
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
import backtrader.filters as btfilters


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False) # 创建 Cerebro 引擎

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)    # 添加策略

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 开始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')        # 结束日期

    data = btfeeds.YahooFinanceData(    # 创建 YahooFinanceData 数据源
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    # Add the resample data instead of the original
    cerebro.adddata(data)   # 添加数据源

    # Add a simple moving average if requirested
    cerebro.addindicator(btind.SMA, period=args.period)   # 添加 SMA 指标

    # Add a writer with CSV
    if args.writer:
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)    # 添加 writer

    # Run over everything
    cerebro.run()

    # Plot if requested
    if args.plot:
        cerebro.plot(style='bar', numfigs=args.numfigs, volume=False)   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Calendar Days Filter Sample')

    parser.add_argument('--data', '-d', # 数据源
                        default='YHOO',
                        help='Ticker to download from Yahoo')

    parser.add_argument('--fromdate', '-f',  # 开始日期
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--period', default=15, type=int,   # SMA 的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--writer', '-w', action='store_true',  # 添加 writer
                        help='Add a writer to cerebro')

    parser.add_argument('--wrcsv', '-wc', action='store_true',  # CSV 输出
                        help='Enable CSV Output in the writer')

    parser.add_argument('--plot', '-p', action='store_true',    # 绘制图表
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1, type=int, # 绘制图表的数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
