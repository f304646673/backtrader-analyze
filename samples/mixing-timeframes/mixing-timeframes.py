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
import backtrader.utils.flushfile


class St(bt.Strategy):
    params = dict(multi=True)

    def __init__(self):
        self.pp = pp = btind.PivotPoint(self.data1) # 创建 PivotPoint 指标
        pp.plotinfo.plot = False  # deactivate plotting # 关闭绘图

        if self.p.multi:    # 如果 multi 为 True
            pp1 = pp()  # couple the entire indicators # 将整个指标耦合在一起
            self.sellsignal = self.data0.close < pp1.s1 # 创建卖出信号
        else:
            self.sellsignal = self.data0.close < pp.s1()    # 创建卖出信号

    def next(self):
        txt = ','.join(
            ['%04d' % len(self),
             '%04d' % len(self.data0),
             '%04d' % len(self.data1),
             self.data.datetime.date(0).isoformat(),
             '%.2f' % self.data0.close[0],
             '%.2f' % self.pp.s1[0],
             '%.2f' % self.sellsignal[0]])

        print(txt)


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎
    data = btfeeds.BacktraderCSVData(dataname=args.data)    # 创建数据源
    cerebro.adddata(data)   # 添加数据源
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)   # 采样数据

    cerebro.addstrategy(St, multi=args.multi)   # 添加策略

    cerebro.run(stdstats=False, runonce=False)  # 运行策略
    if args.plot:
        cerebro.plot(style='bar')   # 绘制图表，样式为 bar


def parse_args():
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,   # 数据文件路径
                        default='../../datas/2005-2006-day-001.txt',
                        help='Data to be read in')

    parser.add_argument('--multi', required=False, action='store_true',  # 是否 multi
                        help='Couple all lines of the indicator')

    parser.add_argument('--plot', required=False, action='store_true',  # 是否绘图
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
