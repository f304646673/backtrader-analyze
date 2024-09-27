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

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class MultiDataStrategy(bt.Strategy):
    '''
    This strategy operates on 2 datas. The expectation is that the 2 datas are
    correlated and the 2nd data is used to generate signals on the 1st
        买入/卖出操作将在第一个数据源上执行
      - Buy/Sell Operationss will be executed on the 1st data
        信号是使用第二个数据源上的简单移动平均线（SMA）生成的，当收盘价向上/向下交叉时触发信号
      - The signals are generated using a Simple Moving Average on the 2nd data
        when the close price crosses upwwards/downwards

    该策略仅做多
    The strategy is a long-only strategy
    '''
    params = dict(
        period=15,  # 移动平均线的周期
        stake=10,   # 每次交易的数量
        printout=True,  # 是否打印输出
    )

    def log(self, txt, dt=None):
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]: # 如果订单已提交/已接受
            return  # Await further notifications

        if order.status == order.Completed: # 如果订单已完成
            if order.isbuy():   # 如果是买入
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price
                self.log(buytxt, order.executed.dt)
            else:   # 如果是卖出
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]: # 如果订单已过期/已取消/保证金
            self.log('%s ,' % order.Status[order.status])
            pass  # Simply log

        # Allow new orders
        self.orderid = None

    def __init__(self):
        # To control operation entries
        self.orderid = None

        # Create SMA on 2nd data
        sma = btind.MovAv.SMA(self.data1, period=self.p.period)  # 创建一个简单移动平均线（SMA）指标，基于收盘价和指定的周期
        # Create a CrossOver Signal from close an moving average
        self.signal = btind.CrossOver(self.data1.close, sma)    # 创建一个交叉指标，用于检测收盘价与SMA的交叉

    def next(self):
        if self.orderid:
            return  # if an order is active, no new orders are allowed

        if self.p.printout:
            print('Self  len:', len(self))
            print('Data0 len:', len(self.data0))
            print('Data1 len:', len(self.data1))
            print('Data0 len == Data1 len:',
                  len(self.data0) == len(self.data1))

            print('Data0 dt:', self.data0.datetime.datetime())
            print('Data1 dt:', self.data1.datetime.datetime())

        if not self.position:  # not yet in market  # 如果还没有持仓
            if self.signal > 0.0:  # cross upwards  # 如果交叉信号大于 0
                self.log('BUY CREATE , %.2f' % self.data1.close[0])
                self.buy(size=self.p.stake)
                self.buy(data=self.data1, size=self.p.stake)

        else:  # in the market  # 如果已经有持仓
            if self.signal < 0.0:  # crosss downwards   # 如果交叉信号小于
                self.log('SELL CREATE , %.2f' % self.data1.close[0])
                self.sell(size=self.p.stake)
                self.sell(data=self.data1, size=self.p.stake)

    def stop(self):
        print('==================================================')
        print('Starting Value - %.2f' % self.broker.startingcash)
        print('Ending   Value - %.2f' % self.broker.getvalue())
        print('==================================================')


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()  # 创建一个 Cerebro 引擎

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将字符串转换为日期时间对象，起始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    # Create the 1st data
    data0 = btfeeds.YahooFinanceCSVData(    # 创建一个数据源
        dataname=args.data0,
        fromdate=fromdate,
        todate=todate)

    # Add the 1st data to cerebro
    cerebro.adddata(data0)  # 将数据添加到 Cerebro 引擎

    # Create the 2nd data
    data1 = btfeeds.YahooFinanceCSVData(    # 创建一个数据源
        dataname=args.data1,
        fromdate=fromdate,
        todate=todate)

    # Add the 2nd data to cerebro
    cerebro.adddata(data1)  # 将数据添加到 Cerebro 引擎

    # Add the strategy
    cerebro.addstrategy(MultiDataStrategy,  # 添加策略
                        period=args.period,
                        stake=args.stake)

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcash(args.cash)   # 设置初始资金

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcommission(commission=args.commperc)  # 设置佣金

    # And run it
    cerebro.run(runonce=not args.runnext,   # 运行策略
                preload=not args.nopreload, # 预加载数据
                oldsync=args.oldsync)   # 使用旧的数据同步方法

    # Plot if requested
    if args.plot:
        cerebro.plot(numfigs=args.numfigs, volume=False, zdown=False)   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(description='MultiData Strategy')

    parser.add_argument('--data0', '-d0',   # 数据文件路径
                        default='../../datas/orcl-1995-2014.txt',
                        help='1st data into the system')

    parser.add_argument('--data1', '-d1',   # 数据文件路径
                        default='../../datas/yhoo-1996-2014.txt',
                        help='2nd data into the system')

    parser.add_argument('--fromdate', '-f', # 起始日期
                        default='2003-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2005-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--period', default=15, type=int,   # 简单移动平均线的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--cash', default=100000, type=int, # 初始资金
                        help='Starting Cash')

    parser.add_argument('--runnext', action='store_true',   # 使用 next by next      
                        help='Use next by next instead of runonce')

    parser.add_argument('--nopreload', action='store_true',  # 不预加载数据
                        help='Do not preload the data')

    parser.add_argument('--oldsync', action='store_true',   # 使用旧的数据同步方法
                        help='Use old data synchronization method')

    parser.add_argument('--commperc', default=0.005, type=float,    # 佣金百分比
                        help='Percentage commission (0.005 is 0.5%%')

    parser.add_argument('--stake', default=10, type=int,    # 每次交易的数量
                        help='Stake to apply in each operation')

    parser.add_argument('--plot', '-p', action='store_true',    # 是否绘图
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,   # 绘图的数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
