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


class SMACrossOver(bt.Strategy):
    params = (
        ('stake', 1),
        ('period', 30),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)   # 获取当前日期
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):  # 通知订单
        if order.status in [order.Submitted, order.Accepted]:   # 如果订单已提交/已接受
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed, order.Canceled, order.Margin]:   # 如果订单已完成/已取消/保证金
            if order.isbuy():   # 如果是买入
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

    def notify_trade(self, trade):  # 通知交易
        if trade.isclosed:  # 如果交易已关闭
            self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                     (trade.pnl, trade.pnlcomm))

    def __init__(self):
        sma = btind.SMA(self.data, period=self.p.period)    # 创建简单移动平均线指标
        # > 0 crossing up / < 0 crossing down
        self.buysell_sig = btind.CrossOver(self.data, sma)  # 创建交叉信号

    def next(self):
        if self.buysell_sig > 0:    # 如果交叉信号大于 0
            self.log('BUY CREATE, %.2f' % self.data.close[0])   # 输出买入信息
            self.buy(size=self.p.stake)  # keep order ref to avoid 2nd orders 保持订单引用以避免第二个订单

        elif self.position and self.buysell_sig < 0:    # 如果有持仓且交叉信号小于 0
            self.log('SELL CREATE, %.2f' % self.data.close[0])  # 输出卖出信息
            self.sell(size=self.p.stake)    # keep order ref to avoid 2nd orders 保持订单引用以避免第二个订单


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()  # 创建一个 Cerebro 引擎

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将字符串转换为日期时间对象，起始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 将字符串转换为日期时间对象，结束日期

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(   # 创建一个数据源
        dataname=args.data, # 数据文件路径
        fromdate=fromdate,  # 起始日期
        todate=todate)  # 结束日期

    # Add the 1st data to cerebro
    cerebro.adddata(data)   # 将数据添加到 Cerebro 引擎

    # Add a strategy
    cerebro.addstrategy(SMACrossOver, period=args.period, stake=args.stake)   # 添加策略

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcash(args.cash)   # 设置初始资金

    commtypes = dict(
        none=None,
        perc=bt.CommInfoBase.COMM_PERC, # 佣金百分比
        fixed=bt.CommInfoBase.COMM_FIXED) # 固定佣金

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcommission(commission=args.comm,  # 设置佣金
                                 mult=args.mult,    # 设置合约乘数
                                 margin=args.margin,   # 设置保证金
                                 percabs=not args.percrel,   # 百分比绝对值
                                 commtype=commtypes[args.commtype],   # 佣金类型
                                 stocklike=args.stocklike)  # 股票类型

    # And run it
    cerebro.run()   # 运行策略

    # Plot if requested
    if args.plot:   # 如果需要绘制图表
        cerebro.plot(numfigs=args.numfigs, volume=False)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Commission schemes',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,)    # 参数默认值帮助格式

    parser.add_argument('--data', '-d',     # 数据文件路径
                        default='../../datas/2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f', # 起始日期
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--stake', default=1, type=int,   # 每次交易的数量
                        help='Stake to apply in each operation')

    parser.add_argument('--period', default=30, type=int,   # 简单移动平均线的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--cash', default=10000.0, type=float,  # 初始资金
                        help='Starting Cash')

    parser.add_argument('--comm', default=2.0, type=float,  # 佣金
                        help=('Commission factor for operation, either a'
                              'percentage or a per stake unit absolute value'))

    parser.add_argument('--mult', default=10, type=int, # 合约乘数
                        help='Multiplier for operations calculation')

    parser.add_argument('--margin', default=2000.0, type=float,  # 保证金
                        help='Margin for futures-like operations')

    parser.add_argument('--commtype', required=False, default='none',   # 佣金类型
                        choices=['none', 'perc', 'fixed'],
                        help=('Commission - choose none for the old'
                              ' CommissionInfo behavior'))

    parser.add_argument('--stocklike', required=False, action='store_true',  # 股票类型
                        help=('If the operation is for stock-like assets or'
                              'future-like assets'))

    parser.add_argument('--percrel', required=False, action='store_true',   # 百分比相对值
                        help=('If perc is expressed in relative xx% rather'
                              'than absolute value 0.xx'))

    parser.add_argument('--plot', '-p', action='store_true',    # 是否绘图
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,   # 绘图的数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
