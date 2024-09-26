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


class PandasDataOptix(btfeeds.PandasData):

    lines = ('optix_close', 'optix_pess', 'optix_opt',) # 定义数据源的字段
    params = (('optix_close', -1),  # 定义数据源的字段的默认值
              ('optix_pess', -1),
              ('optix_opt', -1))

    if False:
        # No longer needed with version 1.9.62.122
        datafields = btfeeds.PandasData.datafields + (  # 定义数据源的字段
            ['optix_close', 'optix_pess', 'optix_opt'])


class StrategyOptix(bt.Strategy):

    def next(self):
        print('%03d %f %f, %f' % (
            len(self),
            self.data.optix_close[0],
            self.data.lines.optix_pess[0],
            self.data.optix_opt[0],))


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)    # 创建 Cerebro 引擎

    # Add a strategy
    cerebro.addstrategy(StrategyOptix)  # 添加策略

    # Get a pandas dataframe
    datapath = ('../../datas/2006-day-001-optix.txt')   # 数据文件路径

    # Simulate the header row isn't there if noheaders requested
    skiprows = 1 if args.noheaders else 0   # 如果请求了 noheaders，则模拟没有标题行
    header = None if args.noheaders else 0  # 如果请求了 noheaders，则 header 为 None

    dataframe = pandas.read_csv(datapath,   # 读取数据文件
                                skiprows=skiprows,  # 跳过的行数
                                header=header,  # 标题行
                                parse_dates=True,   # 解析日期
                                index_col=0)    # 索引列

    if not args.noprint:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = PandasDataOptix(dataname=dataframe)  # 创建数据源

    cerebro.adddata(data)   # 将数据添加到 Cerebro 引擎

    # Run over everything
    cerebro.run()   # 运行策略

    # Plot the result
    if not args.noplot:
        cerebro.plot(style='bar')   # 绘制图表, bar 样式


def parse_args():
    parser = argparse.ArgumentParser(   # 创建参数解析器
        description='Pandas test script')

    parser.add_argument('--noheaders', action='store_true', default=False,  # 是否有标题行
                        required=False,
                        help='Do not use header rows')

    parser.add_argument('--noprint', action='store_true', default=False,    # 是否打印数据
                        help='Print the dataframe')

    parser.add_argument('--noplot', action='store_true', default=False, # 是否绘图
                        help='Do not plot the chart')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
