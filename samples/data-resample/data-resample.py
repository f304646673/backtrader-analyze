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


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)    # 创建 Cerebro 引擎

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)    # 添加策略

    # Load the Data
    datapath = args.dataname or '../../datas/2006-day-001.txt'
    data = btfeeds.BacktraderCSVData(   # 创建数据源
        dataname=datapath)

    # Handy dictionary for the argument timeframe conversion
    tframes = dict(   # 时间框架字典
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)

    # Resample the data
    if args.oldrs: # 如果使用旧的数据重采样
        # Old resampler, fully deprecated
        data = bt.DataResampler(    # 创建数据重采样器
            dataname=data,  # 数据源
            timeframe=tframes[args.timeframe],  # 时间框架
            compression=args.compression)   # 压缩

        # Add the resample data instead of the original
        cerebro.adddata(data)   # 添加数据源
    else:
        # New resampler
        cerebro.resampledata(   # 数据重采样
            data,   # 数据源
            timeframe=tframes[args.timeframe],  # 时间框架
            compression=args.compression)   # 压缩

    # Run over everything
    cerebro.run()   # 运行

    # Plot the result
    cerebro.plot(style='bar')   # 绘图


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resample down to minutes')

    parser.add_argument('--dataname', default='', required=False,   # 数据文件路径
                        help='File Data to Load')

    parser.add_argument('--oldrs', required=False, action='store_true', # 是否使用旧的数据重采样
                        help='Use deprecated DataResampler')

    parser.add_argument('--timeframe', default='weekly', required=False,    # 时间周期，默认为周线
                        choices=['daily', 'weekly', 'monthly'],
                        help='Timeframe to resample to')

    parser.add_argument('--compression', default=1, required=False, type=int,   # 压缩，默认为 1
                        help='Compress n bars into 1')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
