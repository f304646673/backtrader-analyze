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
from __future__ import (absolute_import, division, print_function,)
#                        unicode_literals)

import argparse
import datetime

import backtrader as bt
import backtrader.feeds as btfeeds


class St(bt.Strategy):
    def next(self):
        print(','.join(str(x) for x in [
            self.data.datetime.datetime(),  # 当前的日期时间
            self.data.open[0], self.data.high[0],   # 当前的开盘价和最高价  
            self.data.high[0], self.data.close[0],  # 当前的最高价和收盘价
            self.data.volume[0]]))  # 当前的成交量


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    data = btfeeds.GenericCSVData(  # 创建数据源
        dataname=args.data, # 数据文件
        dtformat='%d/%m/%y',    # 日期格式
        # tmformat='%H%M%S',  # already the default value   时间格式
        # datetime=0,  # position at default
        time=1,  # position of time 时间字段在数据文件中的位置
        open=5,  # position of open 开盘价字段在数据文件中的位置
        high=5, # position of high 最高价字段在数据文件中的位置
        low=5,  # position of low 最低价字段在数据文件中的位置
        close=5,    # position of close 收盘价字段在数据文件中的位置
        volume=7,   # position of volume 成交量字段在数据文件中的位置
        openinterest=-1,  # -1 for not present  持仓量字段在数据文件中的位置，-1 表示不存在
        timeframe=bt.TimeFrame.Ticks)   # 数据的时间周期

    cerebro.resampledata(data,  # 采样数据
                         timeframe=bt.TimeFrame.Ticks,  # 时间周期
                         compression=args.compression)  # 压缩比例

    cerebro.addstrategy(St) # 添加策略

    cerebro.run()   # 运行策略
    if args.plot:
        cerebro.plot(style='bar')   # 绘制图表，样式为 bar


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, # 参数默认值帮助格式
        description='BidAsk to OHLC')

    parser.add_argument('--data', required=False,   # 数据文件
                        default='../../datas/bidask2.csv',
                        help='Data file to be read in')

    parser.add_argument('--compression', required=False, default=2, type=int,   # 压缩比例
                        help='How much to compress the bars')

    parser.add_argument('--plot', required=False, action='store_true',  # 是否绘图
                        help='Plot the vars')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
