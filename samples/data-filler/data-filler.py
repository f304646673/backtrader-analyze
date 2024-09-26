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
import math

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.utils.flushfile
import backtrader.filters as btfilters

from relativevolume import RelativeVolume


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 获取开始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 获取结束日期

    # Get the session times to pass them to the indicator
    # datetime.time has no strptime ...
    dtstart = datetime.datetime.strptime(args.tstart, '%H:%M')  # 交易日开始时间
    dtend = datetime.datetime.strptime(args.tend, '%H:%M')  # 交易日结束时间

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(   # 创建数据源
        dataname=args.data,  # 数据文件
        fromdate=fromdate,  # 开始日期
        todate=todate,  # 结束日期
        timeframe=bt.TimeFrame.Minutes, # 时间周期
        compression=1,  # 压缩比例
        sessionstart=dtstart,  # internally just the "time" part will be used   交易日开始时间
        sessionend=dtend,  # internally just the "time" part will be used   交易日结束时间
    )

    if args.filter:
        data.addfilter(btfilters.SessionFilter) # 添加过滤器

    if args.filler:
        data.addfilter(btfilters.SessionFiller, fill_vol=args.fvol) # 添加过滤器， 填充成交量

    # Add the data to cerebro
    cerebro.adddata(data)   # 添加数据

    if args.relvol: # 如果需要添加相对成交量指标
        # Calculate backward period - tend tstart are in same day
        # + 1 to include last moment of the interval dstart <-> dtend
        td = ((dtend - dtstart).seconds // 60) + 1  # 计算时间差，单位为分钟
        cerebro.addindicator(RelativeVolume,    # 添加相对成交量指标
                             period=td, # 时间周期
                             volisnan=math.isnan(args.fvol))    # 是否将 NaN 作为成交量

    # Add an empty strategy
    cerebro.addstrategy(bt.Strategy)    # 添加策略

    # Add a writer with CSV
    if args.writer:
        cerebro.addwriter(bt.WriterFile, csv=args.wrcsv)    # 添加写入器

    # And run it - no trading - disable stdstats
    cerebro.run(stdstats=False) # 运行策略，禁用标准统计

    # Plot if requested
    if args.plot:   # 如果需要绘制图表
        cerebro.plot(numfigs=args.numfigs, volume=True)  # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(
        description='DataFilter/DataFiller Sample')   # 创建一个参数解析器

    parser.add_argument('--data', '-d',    # 数据文件路径
                        default='../../datas/2006-01-02-volume-min-001.txt',
                        help='data to add to the system')

    parser.add_argument('--filter', '-ft', action='store_true',     # 是否过滤
                        help='Filter using session start/end times')

    parser.add_argument('--filler', '-fl', action='store_true',    # 是否填充
                        help='Fill missing bars inside start/end times')

    parser.add_argument('--fvol', required=False, default=0.0,      # 填充成交量
                        type=float,
                        help='Use as fill volume for missing bar (def: 0.0)')

    parser.add_argument('--tstart', '-ts',      # 交易日开始时间
                        # default='09:14:59',
                        # help='Start time for the Session Filter (%H:%M:%S)')
                        default='09:15',
                        help='Start time for the Session Filter (HH:MM)')

    parser.add_argument('--tend', '-te',        # 交易日结束时间
                        # default='17:15:59',
                        # help='End time for the Session Filter (%H:%M:%S)')
                        default='17:15',
                        help='End time for the Session Filter (HH:MM)')

    parser.add_argument('--relvol', '-rv', action='store_true', # 是否添加相对成交量指标
                        help='Add relative volume indicator')

    parser.add_argument('--fromdate', '-f',   # 起始日期
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

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
    runstrategy()
