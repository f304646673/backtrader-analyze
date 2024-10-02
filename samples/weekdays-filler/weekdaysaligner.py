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
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile

# from wkdaysfiller import WeekDaysFiller
from weekdaysfiller import WeekDaysFiller


class St(bt.Strategy):
    params = (('sma', 0),)

    def __init__(self):
        if self.p.sma:
            btind.SMA(self.data0, period=self.p.sma)    # 添加 SMA 指标
            btind.SMA(self.data1, period=self.p.sma)    # 添加 SMA 指标

    def next(self):
        dtequal = (self.data0.datetime.datetime() ==    # 判断两个时间是否相等
                   self.data1.datetime.datetime())

        txt = ''
        txt += '%04d, %5s' % (len(self), str(dtequal))
        txt += ', data0, %s' % self.data0.datetime.datetime().isoformat()
        txt += ', %s, data1' % self.data1.datetime.datetime().isoformat()
        print(txt)


def runstrat():
    args = parse_args()

    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 开始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 结束日期

    cerebro = bt.Cerebro(stdstats=False)    # 创建 Cerebro 引擎

    DataFeed = btfeeds.YahooFinanceCSVData  # 创建数据源
    if args.online:   # 判断是否在线获取数据
        DataFeed = btfeeds.YahooFinanceData # 创建数据源

    data0 = DataFeed(dataname=args.data0, fromdate=fromdate, todate=todate)   # 创建数据源

    if args.data1:
        data1 = DataFeed(dataname=args.data1, fromdate=fromdate, todate=todate)   # 创建数据源
    else:
        data1 = data0.clone()   # 克隆数据源

    if args.filler or args.filler0:
        data0.addfilter(WeekDaysFiller, fillclose=args.fillclose)   # 添加过滤器

    if args.filler or args.filler1:
        data1.addfilter(WeekDaysFiller, fillclose=args.fillclose)   # 添加过滤器

    cerebro.adddata(data0)  # 添加数据源
    cerebro.adddata(data1)  # 添加数据源

    cerebro.addstrategy(St, sma=args.sma)   # 添加策略
    cerebro.run(runonce=True, preload=True)  # 运行

    if args.plot:
        cerebro.plot(style='bar')   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for aligning with trade ')

    parser.add_argument('--online', required=False, action='store_true',    # 在线获取数据
                        help='Fetch data online from Yahoo')

    parser.add_argument('--data0', required=True, help='Data 0 to be read in')  # 数据源 0
    parser.add_argument('--data1', required=False, help='Data 1 to be read in') # 数据源 1

    parser.add_argument('--sma', required=False, default=0, type=int,   # SMA 的周期
                        help='Add a sma to the datas')

    parser.add_argument('--fillclose', required=False, action='store_true',   # 用收盘价填充
                        help='Fill with Close price instead of NaN')

    parser.add_argument('--filler', required=False, action='store_true',    # 添加过滤器
                        help='Add Filler to Datas 0 and 1')

    parser.add_argument('--filler0', required=False, action='store_true',   # 添加过滤器
                        help='Add Filler to Data 0')

    parser.add_argument('--filler1', required=False, action='store_true',   # 添加过滤器
                        help='Add Filler to Data 1')

    parser.add_argument('--fromdate', '-f', default='2012-01-01',   # 开始日期
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t', default='2012-12-31',  # 结束日期
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--plot', required=False, action='store_true',  # 绘制图表
                        help='Do plot')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
