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


class TheStrategy(bt.SignalStrategy):
    params = dict(rsi_per=14, rsi_upper=65.0, rsi_lower=35.0, rsi_out=50.0,
                  warmup=35)

    def notify_order(self, order):
        super(TheStrategy, self).notify_order(order)    # 调用父类的 notify_order 方法
        if order.status == order.Completed: # 如果订单已完成
            print('%s: Size: %d @ Price %f' %
                  ('buy' if order.isbuy() else 'sell',
                   order.executed.size, order.executed.price))

            d = order.data
            print('Close[-1]: %f - Open[0]: %f' % (d.close[-1], d.open[0]))

    def __init__(self):
        # Original code needs artificial warmup phase - hidden sma to replic
        if self.p.warmup:   # 如果有热身期
            bt.indicators.SMA(period=self.p.warmup, plot=False) # 创建移动平均线指标

        rsi = bt.indicators.RSI(period=self.p.rsi_per,  # 创建 RSI 指标
                                upperband=self.p.rsi_upper,     # 上轨
                                lowerband=self.p.rsi_lower)    # 下轨

        crossup = bt.ind.CrossUp(rsi, self.p.rsi_lower)   # 创建交叉信号
        self.signal_add(bt.SIGNAL_LONG, crossup)    # 添加多头信号
        self.signal_add(bt.SIGNAL_LONGEXIT, -(rsi > self.p.rsi_out))    # 添加多头退出信号

        crossdown = bt.ind.CrossDown(rsi, self.p.rsi_upper)  # 创建交叉信号
        self.signal_add(bt.SIGNAL_SHORT, -crossdown)    # 添加空头信号
        self.signal_add(bt.SIGNAL_SHORTEXIT, rsi < self.p.rsi_out)  # 添加空头退出信号


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎
    cerebro.broker.set_cash(args.cash)  # 设置初始资金
    cerebro.broker.set_coc(args.coc)    # 设置是否在下单时立即执行
    data0 = bt.feeds.YahooFinanceData(  # 创建数据源
        dataname=args.data, # 数据源名称
        fromdate=datetime.datetime.strptime(args.fromdate, '%Y-%m-%d'), # 开始日期
        todate=datetime.datetime.strptime(args.todate, '%Y-%m-%d'), # 结束日期
        round=False)    # 是否四舍五入

    cerebro.adddata(data0)  # 添加数据源

    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)   # 创建 Sizer
    cerebro.addstrategy(TheStrategy, **(eval('dict(' + args.strat + ')')))  # 添加策略
    cerebro.addobserver(bt.observers.Value)   # 添加观察者, 记录价值
    cerebro.addobserver(bt.observers.Trades)    # 添加观察者, 记录交易
    cerebro.addobserver(bt.observers.BuySell, barplot=True)   # 添加观察者, 记录买卖

    cerebro.run(stdstats=False) # 运行策略
    if args.plot:   # 如果请求绘图
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample after post at keithselover.wordpress.com')

    parser.add_argument('--data', required=False, default='XOM',    # 数据源
                        help='Yahoo Ticker')

    parser.add_argument('--fromdate', required=False, default='2012-09-01',   # 开始日期
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False, default='2016-01-01',   # 结束日期
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store', type=float,   # 初始资金
                        default=100000, help=('Cash to start with'))

    parser.add_argument('--stake', required=False, action='store', type=int,    # 下单量
                        default=100, help=('Cash to start with'))

    parser.add_argument('--coc', required=False, action='store_true',   # 是否在下单时立即执行
                        help=('Buy on close of same bar as order is issued'))

    parser.add_argument('--strat', required=False, action='store', default='',  # 策略参数
                        help=('Arguments for the strategy'))

    parser.add_argument('--plot', '-p', nargs='?', required=False,  # 是否绘图
                        metavar='kwargs', const='{}',
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
