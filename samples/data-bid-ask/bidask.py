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


class BidAskCSV(btfeeds.GenericCSVData):
    linesoverride = True  # discard usual OHLC structure  丢弃通常的 OHLC 结构
    # datetime must be present and last
    lines = ('bid', 'ask', 'datetime')  # 三条线，分别是 bid、ask 和 datetime
    # datetime (always 1st) and then the desired order for
    params = (
        # (datetime, 0), # inherited from parent class
        ('bid', 1),  # default field pos 1  bid 字段位置 1
        ('ask', 2),  # default field pos 2  ask 字段位置 2
    )


class St(bt.Strategy):
    params = (('sma', False), ('period', 3))

    def __init__(self):
        if self.p.sma:
            self.sma = btind.SMA(self.data, period=self.p.period)   # 创建移动平均线指标

    def next(self):
        dtstr = self.data.datetime.datetime().isoformat()   # 获取当前的日期时间
        txt = '%4d: %s - Bid %.4f - %.4f Ask' % (
            (len(self), dtstr, self.data.bid[0], self.data.ask[0]))

        if self.p.sma:  # 如果有移动平均线
            txt += ' - SMA: %.4f' % self.sma[0]
        print(txt)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Bid/Ask Line Hierarchy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, # 参数默认值帮助格式
    )

    parser.add_argument('--data', '-d', action='store', # 数据文件
                        required=False, default='../../datas/bidask.csv',
                        help='data to add to the system')

    parser.add_argument('--dtformat', '-dt',    # 日期时间格式
                        required=False, default='%m/%d/%Y %H:%M:%S',
                        help='Format of datetime in input')

    parser.add_argument('--sma', '-s', action='store_true', # 是否添加移动平均线
                        required=False,
                        help='Add an SMA to the mix')

    parser.add_argument('--period', '-p', action='store',   # 移动平均线的周期
                        required=False, default=5, type=int,
                        help='Period for the sma')

    return parser.parse_args()


def runstrategy():
    args = parse_args()

    cerebro = bt.Cerebro()  # Create a cerebro  创建一个 Cerebro 引擎

    data = BidAskCSV(dataname=args.data, dtformat=args.dtformat)    # Create a data feed  创建一个数据源
    cerebro.adddata(data)  # Add the 1st data to cerebro    将数据源添加到 Cerebro 引擎
    # Add the strategy to cerebro
    cerebro.addstrategy(St, sma=args.sma, period=args.period)   # Add the strategy to cerebro  将策略添加到 Cerebro 引擎
    cerebro.run()   # Run the strategy  运行策略


if __name__ == '__main__':
    runstrategy()
