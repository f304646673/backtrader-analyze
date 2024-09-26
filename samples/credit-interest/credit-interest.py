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
import collections
import datetime
import itertools

import backtrader as bt


class SMACrossOver(bt.Signal):
    params = (('p1', 10), ('p2', 30),)

    def __init__(self):
        sma1 = bt.indicators.SMA(period=self.p.p1)  # 创建移动平均线指标，周期为 p1
        sma2 = bt.indicators.SMA(period=self.p.p2)  # 创建移动平均线指标，周期为 p2
        self.lines.signal = bt.indicators.CrossOver(sma1, sma2) # 创建交叉信号


class NoExit(bt.Signal):
    def next(self):
        self.lines.signal[0] = 0.0


class St(bt.SignalStrategy):
    opcounter = itertools.count(1)  # 生成一个无限迭代器

    def notify_order(self, order):  # 通知订单
        if order.status == bt.Order.Completed:  # 如果订单完成
            t = ''
            t += '{:02d}'.format(next(self.opcounter))
            t += ' {}'.format(order.data.datetime.datetime())
            t += ' BUY ' * order.isbuy() or ' SELL'
            t += ' Size: {:+d} / Price: {:.2f}'
            print(t.format(order.executed.size, order.executed.price))

    def notify_trade(self, trade):  # 通知交易
        if trade.isclosed:  # 如果交易已关闭
            print('Trade closed with P&L: Gross {} Net {}'.format(
                trade.pnl, trade.pnlcomm))


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎
    cerebro.broker.set_cash(args.cash)  # 设置初始资金
    cerebro.broker.set_int2pnl(args.no_int2pnl) # 设置是否将利息分配到 pnl

    dkwargs = dict()
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将日期字符串转换为 datetime 对象，起始日期
        dkwargs['fromdate'] = fromdate

    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 将日期字符串转换为 datetime 对象，结束日期
        dkwargs['todate'] = todate

    # if dataset is None, args.data has been given
    data = bt.feeds.BacktraderCSVData(dataname=args.data, **dkwargs)    # 创建数据源
    cerebro.adddata(data)   # 将数据添加到 Cerebro 引擎

    cerebro.signal_strategy(St)   # 添加策略
    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)   # 设置固定数量的下单量

    sigtype = bt.signal.SIGNAL_LONGSHORT    # 信号类型
    if args.long:   # 如果是做多
        sigtype = bt.signal.SIGNAL_LONG
    elif args.short:    # 如果是做空
        sigtype = bt.signal.SIGNAL_SHORT

    cerebro.add_signal(sigtype, 
                       SMACrossOver, p1=args.period1, p2=args.period2) # 添加信号  

    if args.no_exit:    # 如果不退出
        if args.long:   # 如果是做多
            cerebro.add_signal(bt.signal.SIGNAL_LONGEXIT, NoExit)   # 添加信号
        elif args.short:    # 如果是做空
            cerebro.add_signal(bt.signal.SIGNAL_SHORTEXIT, NoExit)  # 添加信号

    comminfo = bt.CommissionInfo(   # 创建佣金信息
        mult=args.mult, # 合约乘数
        margin=args.margin, # 保证金
        stocklike=args.stocklike,   # 是否股票类
        interest=args.interest, # 利息
        interest_long=args.interest_long)   # 做多利息

    cerebro.broker.addcommissioninfo(comminfo)  # 添加佣金信息

    cerebro.run()   # 运行策略
    if args.plot:   # 如果绘图
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)    # 更新参数

        cerebro.plot(**pkwargs) # 绘制图表


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,  # 参数默认值帮助格式
        description='Sample for Slippage')

    parser.add_argument('--data', required=False,   # 数据文件路径
                        default='../../datas/2005-2006-day-001.txt',
                        help='Specific data to be read in')

    parser.add_argument('--fromdate', required=False, default=None,   # 起始日期
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False, default=None,   # 结束日期
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store',   # 初始资金
                        type=float, default=50000,
                        help=('Cash to start with'))

    parser.add_argument('--period1', required=False, action='store',    # 简单移动平均线的周期
                        type=int, default=10,
                        help=('Fast moving average period'))

    parser.add_argument('--period2', required=False, action='store',    # 简单移动平均线的周期
                        type=int, default=30,
                        help=('Slow moving average period'))

    parser.add_argument('--interest', required=False, action='store',   # 利息
                        default=0.0, type=float,
                        help=('Activate credit interest rate'))

    parser.add_argument('--no-int2pnl', required=False, action='store_false',   # 是否将利息分配到 pnl
                        help=('Do not assign interest to pnl'))

    parser.add_argument('--interest_long', required=False, action='store_true',  # 做多利息
                        help=('Credit interest rate for long positions'))

    pgroup = parser.add_mutually_exclusive_group()  # 创建一个互斥组，只能选择其中一个选项
    pgroup.add_argument('--long', required=False, action='store_true',  # 做多
                        help=('Do a long only strategy'))

    pgroup.add_argument('--short', required=False, action='store_true', # 做空
                        help=('Do a long only strategy'))

    parser.add_argument('--no-exit', required=False, action='store_true',   # 不退出
                        help=('The 1st taken position will not be exited'))

    parser.add_argument('--stocklike', required=False, action='store_true', # 股票类
                        help=('Consider the asset to be stocklike'))

    parser.add_argument('--margin', required=False, action='store',  # 保证金
                        default=0.0, type=float,
                        help=('Margin for future like instruments'))

    parser.add_argument('--mult', required=False, action='store',   # 合约乘数
                        default=1.0, type=float,
                        help=('Multiplier for future like instruments'))

    parser.add_argument('--stake', required=False, action='store',  # 每次交易的数量
                        default=10, type=int,
                        help=('Stake to apply'))

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,  # 是否绘图
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
