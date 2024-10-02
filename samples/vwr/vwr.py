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

TFRAMES = dict(
    days=bt.TimeFrame.Days,
    weeks=bt.TimeFrame.Weeks,
    months=bt.TimeFrame.Months,
    years=bt.TimeFrame.Years)


def runstrat(pargs=None):
    args = parse_args(pargs)

    # Create a cerebro
    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    if args.cash is not None:
        cerebro.broker.set_cash(args.cash)  # 设置初始资金

    dkwargs = dict()
    # Get the dates from the args
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 开始日期
        dkwargs['fromdate'] = fromdate
    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 结束日期
        dkwargs['todate'] = todate

    # Create the 1st data
    data = bt.feeds.BacktraderCSVData(dataname=args.data, **dkwargs)    # 创建数据源
    cerebro.adddata(data)  # Add the data to cerebro    # 添加数据源

    cerebro.addstrategy(bt.strategies.SMA_CrossOver)  # Add the strategy    # 添加策略

    lrkwargs = dict()
    if args.tframe is not None:
        lrkwargs['timeframe'] = TFRAMES[args.tframe]    # 设置时间帧

    if args.tann is not None:
        lrkwargs['tann'] = args.tann    # 设置年化因子

    cerebro.addanalyzer(bt.analyzers.Returns, **lrkwargs)  # Returns    # 添加分析器

    vwrkwargs = dict()
    if args.tframe is not None:
        vwrkwargs['timeframe'] = TFRAMES[args.tframe]   # 设置时间帧

    if args.tann is not None:
        vwrkwargs['tann'] = args.tann   # 设置年化因子

    if args.sigma_max is not None:
        vwrkwargs['sigma_max'] = args.sigma_max  # 设置 sigma_max

    if args.tau is not None:
        vwrkwargs['tau'] = args.tau # 设置 tau

    cerebro.addanalyzer(bt.analyzers.SQN)  # VWR Analyzer   # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A)  # VWR Analyzer  # 添加分析器
    cerebro.addanalyzer(bt.analyzers.VWR, **vwrkwargs)  # VWR Analyzer  # 添加分析器
    # Sample time return analyzers
    cerebro.addanalyzer(bt.analyzers.TimeReturn,    # 添加分析器
                        timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.TimeReturn,    # 添加分析器
                        timeframe=bt.TimeFrame.Years)

    # Add a writer to get output
    cerebro.addwriter(bt.WriterFile, csv=args.writercsv, rounding=4)    # 添加 writer

    cerebro.run()  # And run it   # 运行策略

    # Plot if requested
    if args.plot:
        pkwargs = dict(style='bar') # 绘制图表
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='VWR')

    parser.add_argument('--data', '-d', # 数据源
                        default='../../datas/2005-2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--cash', default=None, type=float, required=False,  # 初始资金
                        help='Starting Cash')

    parser.add_argument('--fromdate', '-f', # 开始日期
                        default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default=None,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--writercsv', '-wcsv', action='store_true',    # 输出到 CSV
                        help='Tell the writer to produce a csv stream')

    parser.add_argument('--tframe', '--timeframe', default=None,    # 时间帧
                        required=False, choices=TFRAMES.keys(),
                        help='TimeFrame for the Returns/Sharpe calculations')

    parser.add_argument('--sigma-max', required=False, action='store',  # VWR Sigma Max
                        type=float, default=None,
                        help='VWR Sigma Max')

    parser.add_argument('--tau', required=False, action='store',    # VWR tau factor
                        type=float, default=None,
                        help='VWR tau factor')

    parser.add_argument('--tann', required=False, action='store',   # Annualization factor
                        type=float, default=None,
                        help=('Annualization factor'))

    parser.add_argument('--stddev-sample', required=False, action='store_true', # Consider Bessels correction
                        help='Consider Bessels correction for stddeviation')

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
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
