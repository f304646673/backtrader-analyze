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
    cerebro = bt.Cerebro(stdstats=False)    # 创建 Cerebro 引擎

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)    # 添加策略

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 获取开始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 获取结束日期

    data = btfeeds.BacktraderCSVData(   # 创建数据源
        dataname=args.data,   # 数据文件
        fromdate=fromdate,  # 开始日期
        todate=todate)  # 结束日期

    if args.calendar:
        if args.fprice is not None: # 如果 fprice 不为空
            args.fprice = float(args.fprice)    # 将 fprice 转换为浮点数

        data.addfilter(   # 添加过滤器
            btfilters.CalendarDays,   # 过滤器类型，日历天
            fill_price=args.fprice,  # 价格填充
            fill_vol=args.fvol) # 成交量填充

    # Add the resample data instead of the original
    cerebro.adddata(data)   # 添加数据

    # Add a simple moving average if requirested
    if args.sma:    # 如果需要添加简单移动平均线
        cerebro.addindicator(btind.SMA, period=args.period)   # 添加简单移动平均线

    # Add a writer with CSV
    if args.writer: # 如果需要添加写入器
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)    # 添加写入器

    # Run over everything
    cerebro.run()   # 运行策略

    # Plot if requested
    if args.plot:   # 如果需要绘制图表
        cerebro.plot(style='bar', numfigs=args.numfigs, volume=False)   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,   # 参数默认值帮助格式
        description='Calendar Days Filter Sample')

    parser.add_argument('--data', '-d',     # 数据文件
                        default='../../datas/2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f', # 起始日期
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--calendar', '-cal', required=False,   # 是否添加日历天过滤器
                        action='store_true',
                        help='Add a CalendarDays filter')

    parser.add_argument('--fprice', required=False, default=None,   # 价格填充
                        help='Use as fill for price (None for previous close)')

    parser.add_argument('--fvol', required=False, default=0.0,      # 成交量填充
                        type=float,
                        help='Use as fill volume for missing bar (def: 0.0)')

    parser.add_argument('--sma', required=False,    # 是否添加简单移动平均线
                        action='store_true',
                        help='Add a Simple Moving Average')

    parser.add_argument('--period', default=15, type=int,   # 移动平均线的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--writer', '-w', action='store_true',  # 是否添加写入器
                        help='Add a writer to cerebro')

    parser.add_argument('--wrcsv', '-wc', action='store_true',  # 是否输出到 CSV
                        help='Enable CSV Output in the writer')

    parser.add_argument('--plot', '-p', action='store_true',    # 是否绘图
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,   # 绘图的数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
