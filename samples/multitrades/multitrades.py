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
import itertools

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind

import mtradeobserver


class MultiTradeStrategy(bt.Strategy):
    '''This strategy buys/sells upong the close price crossing
    upwards/downwards a Simple Moving Average.

    It can be a long-only strategy by setting the param "onlylong" to True
    '''
    params = dict(
        period=15,
        stake=1,
        printout=False,
        onlylong=False,
        mtrade=False,
    )

    def log(self, txt, dt=None):
        if self.p.printout:
            dt = dt or self.data.datetime[0]    # 获取当前日期
            dt = bt.num2date(dt)    # 将数字转换为日期
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # To control operation entries
        self.order = None

        # Create SMA on 2nd data
        sma = btind.MovAv.SMA(self.data, period=self.p.period)  # 创建移动平均线指标
        # Create a CrossOver Signal from close an moving average
        self.signal = btind.CrossOver(self.data.close, sma) # 创建交叉信号

        # To alternate amongst different tradeids
        if self.p.mtrade:   # 如果激活了多交易 ID
            self.tradeid = itertools.cycle([0, 1, 2])   # 创建一个迭代器
        else:
            self.tradeid = itertools.cycle([0])   # 创建一个迭代器

    def next(self):
        if self.order:
            return  # if an order is active, no new orders are allowed

        if self.signal > 0.0:  # cross upwards  # 如果交叉信号大于 0
            if self.position:   # 如果有持仓
                self.log('CLOSE SHORT , %.2f' % self.data.close[0])
                self.close(tradeid=self.curtradeid)

            self.log('BUY CREATE , %.2f' % self.data.close[0])
            self.curtradeid = next(self.tradeid)    # 获取下一个交易 ID
            self.buy(size=self.p.stake, tradeid=self.curtradeid)    # 买入指定数量

        elif self.signal < 0.0: # cross downwards  # 如果交叉信号小于 0
            if self.position:   # 如果有持仓
                self.log('CLOSE LONG , %.2f' % self.data.close[0])
                self.close(tradeid=self.curtradeid)  # 平仓

            if not self.p.onlylong: # 如果不仅做多
                self.log('SELL CREATE , %.2f' % self.data.close[0])
                self.curtradeid = next(self.tradeid)    # 获取下一个交易 ID
                self.sell(size=self.p.stake, tradeid=self.curtradeid)   # 卖出指定数量

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:   # 如果订单已提交/已接受
            return  # Await further notifications

        if order.status == order.Completed:  # 如果订单已完成
            if order.isbuy():   # 如果是买入
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price
                self.log(buytxt, order.executed.dt)
            else:
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:  # 如果订单已过期/已取消/保证金
            self.log('%s ,' % order.Status[order.status])
            pass  # Simply log

        # Allow new orders
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:  # 如果交易已关闭
            self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                     (trade.pnl, trade.pnlcomm))

        elif trade.justopened:  # 如果交易刚刚打开
            self.log('TRADE OPENED, SIZE %2d' % trade.size)


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()  # 创建一个 Cerebro 引擎

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将字符串转换为日期时间对象, 起始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 将字符串转换为日期时间对象, 结束日期

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(   # 创建一个数据源
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    # Add the 1st data to cerebro
    cerebro.adddata(data)   # 将数据添加到 Cerebro 引擎

    # Add the strategy
    cerebro.addstrategy(MultiTradeStrategy, # 添加策略
                        period=args.period, # 简单移动平均线的周期
                        onlylong=args.onlylong, # 是否仅做多
                        stake=args.stake,   # 每次交易的数量
                        printout=args.printout, # 是否打印交易信息
                        mtrade=args.mtrade)   # 是否激活多交易 ID

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcash(args.cash)   # 设置初始资金

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcommission(commission=args.comm,  # 设置手续费
                                 mult=args.mult,    # 设置合约乘数
                                 margin=args.margin)    # 设置保证金

    # Add the MultiTradeObserver
    cerebro.addobserver(mtradeobserver.MTradeObserver)  # 添加观察者

    # And run it
    cerebro.run()   # 运行策略

    # Plot if requested
    if args.plot:
        cerebro.plot(numfigs=args.numfigs, volume=False, zdown=False)   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(description='MultiTrades')  # 创建一个参数解析器

    parser.add_argument('--data', '-d',     # 数据文件路径
                        default='../../datas/2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f', # 起始日期
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--mtrade', action='store_true',    # 激活多交易 ID
                        help='Activate MultiTrade Ids')

    parser.add_argument('--period', default=15, type=int,   # 移动平均线的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--onlylong', '-ol', action='store_true',   # 仅做多
                        help='Do only long operations')

    parser.add_argument('--printout', action='store_true',  # 打印交易信息
                        help='Print operation log from strategy')

    parser.add_argument('--cash', default=100000, type=int, # 初始资金
                        help='Starting Cash')

    parser.add_argument('--comm', default=2, type=float,    # 佣金
                        help='Commission for operation')

    parser.add_argument('--mult', default=10, type=int,    # 合约乘数
                        help='Multiplier for futures')

    parser.add_argument('--margin', default=2000.0, type=float, # 保证金
                        help='Margin for each future')

    parser.add_argument('--stake', default=1, type=int,   # 每次交易的数量
                        help='Stake to apply in each operation')

    parser.add_argument('--plot', '-p', action='store_true',    # 是否绘图
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,   # 绘图的数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
