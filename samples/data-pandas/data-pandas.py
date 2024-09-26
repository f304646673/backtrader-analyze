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

import pandas


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)    # 创建 Cerebro 引擎, stdstats=False 表示不显示统计信息

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)    # 添加策略

    # Get a pandas dataframe
    datapath = ('../../datas/2006-day-001.txt')   # 数据文件路径

    # Simulate the header row isn't there if noheaders requested
    skiprows = 1 if args.noheaders else 0   # 如果请求不使用头行，则跳过第一行
    header = None if args.noheaders else 0  # 如果请求不使用头行，则头行为 None

    dataframe = pandas.read_csv(    # 读取数据文件
        datapath,   # 数据文件路径
        skiprows=skiprows,  # 跳过的行数
        header=header,  # 头行
        # parse_dates=[0],
        parse_dates=True,   # 解析日期
        index_col=0,    # 索引列
    )

    if not args.noprint:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,  # 数据源
                               # datetime='Date',
                               nocase=True, # 不区分大小写
                               )

    cerebro.adddata(data)   # 添加数据

    # Run over everything
    cerebro.run()   # 运行策略

    # Plot the result
    cerebro.plot(style='bar')   # 绘制图表，样式为 bar


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pandas test script')

    parser.add_argument('--noheaders', action='store_true', default=False,  # 是否有标题行
                        required=False,
                        help='Do not use header rows')

    parser.add_argument('--noprint', action='store_true', default=False,    # 是否打印数据
                        help='Print the dataframe')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
