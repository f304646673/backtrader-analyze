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
import sys

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile


class TestInd(bt.Indicator):
    lines = ('a', 'b')

    def __init__(self):
        self.lines.a = b = self.data.close - self.data.high # 计算 a 线
        self.lines.b = btind.SMA(b, period=20)  # 计算 b 线


class St(bt.Strategy):
    params = (
        ('datalines', False),   # 是否打印数据行，默认为 False
        ('lendetails', False),  # 是否打印详细信息，默认为 False
    )

    def __init__(self):
        btind.SMA() # 创建移动平均线指标
        btind.Stochastic()  # 创建随机指标
        btind.RSI() # 创建 RSI 指标
        btind.MACD()    # 创建 MACD 指标
        btind.CCI() # 创建 CCI 指标
        TestInd().plotinfo.plot = False # 创建自定义指标

    def next(self):
        if self.p.datalines:    # 如果打印数据行
            txt = ','.join(
                ['%04d' % len(self),
                 '%04d' % len(self.data0),
                 self.data.datetime.date(0).isoformat()]
            )

            print(txt)

    def loglendetails(self, msg):
        if self.p.lendetails:
            print(msg)

    def stop(self):
        super(St, self).stop()  # 调用父类的 stop 方法

        tlen = 0
        self.loglendetails('-- Evaluating Datas')
        for i, data in enumerate(self.datas):   # 遍历数据
            tdata = 0
            for line in data.lines: # 遍历数据的每一行
                tdata += len(line.array)    # 计算每一行的长度
                tline = len(line.array) # 计算每一行的长度

            tlen += tdata   # 计算总长度
            logtxt = '---- Data {} Total Cells {} - Cells per Line {}'
            self.loglendetails(logtxt.format(i, tdata, tline))  # 打印数据信息

        self.loglendetails('-- Evaluating Indicators')  # 打印指标信息
        for i, ind in enumerate(self.getindicators()):  # 遍历指标
            tlen += self.rindicator(ind, i, 0)  # 计算指标的长度

        self.loglendetails('-- Evaluating Observers')
        for i, obs in enumerate(self.getobservers()):   # 遍历观察者
            tobs = 0
            for line in obs.lines:  # 遍历观察者的每一行
                tobs += len(line.array) # 计算每一行的长度
                tline = len(line.array) # 计算每一行的长度

            tlen += tdata   # 计算总长度
            logtxt = '---- Observer {} Total Cells {} - Cells per Line {}'
            self.loglendetails(logtxt.format(i, tobs, tline))

        print('Total memory cells used: {}'.format(tlen))

    def rindicator(self, ind, i, deep):
        tind = 0
        for line in ind.lines:  # 遍历指标的每一行
            tind += len(line.array) # 计算每一行的长度
            tline = len(line.array) # 计算每一行的长度

        thisind = tind  # 记录当前指标的长度

        tsub = 0    # 子指标的长度
        for j, sind in enumerate(ind.getindicators()):  # 遍历子指标
            tsub += self.rindicator(sind, j, deep + 1)  # 计算子指标的长度

        iname = ind.__class__.__name__.split('.')[-1]   # 获取指标的名称

        logtxt = '---- Indicator {}.{} {} Total Cells {} - Cells per line {}'
        self.loglendetails(logtxt.format(deep, i, iname, tind, tline))
        logtxt = '---- SubIndicators Total Cells {}'
        self.loglendetails(logtxt.format(deep, i, iname, tsub)) # 打印子指标的长度

        return tind + tsub


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎
    data = btfeeds.YahooFinanceCSVData(dataname=args.data)  # 创建数据源
    cerebro.adddata(data)   # 添加数据源
    cerebro.addstrategy(    # 添加策略
        St, datalines=args.datalines, lendetails=args.lendetails)

    cerebro.run(runonce=False, exactbars=args.save)   # 运行策略
    if args.plot:
        cerebro.plot(style='bar')   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Check Memory Savings')

    parser.add_argument('--data', required=False,   # 数据文件
                        default='../../datas/yhoo-1996-2015.txt',
                        help='Data to be read in')

    parser.add_argument('--save', required=False, type=int, default=0,  # 保存级别
                        help=('Memory saving level [1, 0, -1, -2]'))

    parser.add_argument('--datalines', required=False, action='store_true', # 是否打印数据行
                        help=('Print data lines'))

    parser.add_argument('--lendetails', required=False, action='store_true',    # 是否打印详细信息
                        help=('Print individual items memory usage'))

    parser.add_argument('--plot', required=False, action='store_true',  # 是否绘图
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
