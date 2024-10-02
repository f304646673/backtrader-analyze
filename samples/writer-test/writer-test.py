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
from backtrader.analyzers import SQN


class LongShortStrategy(bt.Strategy):
    '''This strategy buys/sells upong the close price crossing
    upwards/downwards a Simple Moving Average.

    It can be a long-only strategy by setting the param "onlylong" to True
    '''
    params = dict(
        period=15,
        stake=1,
        printout=False,
        onlylong=False,
        csvcross=False,
    )

    def start(self):
        pass

    def stop(self):
        pass

    def log(self, txt, dt=None):
        if self.p.printout:
            dt = dt or self.data.datetime[0]    # 获取时间
            dt = bt.num2date(dt)    # 转换时间
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # To control operation entries
        self.orderid = None

        # Create SMA on 2nd data
        sma = btind.MovAv.SMA(self.data, period=self.p.period)  # 创建 SMA 指标
        # Create a CrossOver Signal from close an moving average
        self.signal = btind.CrossOver(self.data.close, sma)  # 创建交叉信号
        self.signal.csv = self.p.csvcross   # 输出交叉信号到 CSV

    def next(self):
        if self.orderid:
            return  # if an order is active, no new orders are allowed

        if self.signal > 0.0:  # cross upwards  # 交叉向上
            if self.position:   # 有持仓
                self.log('CLOSE SHORT , %.2f' % self.data.close[0])
                self.close()

            self.log('BUY CREATE , %.2f' % self.data.close[0])
            self.buy(size=self.p.stake) # 买入

        elif self.signal < 0.0: # cross downwards  # 交叉向下
            if self.position:   # 有持仓
                self.log('CLOSE LONG , %.2f' % self.data.close[0])
                self.close()    # 卖出

            if not self.p.onlylong: # 不是只做多
                self.log('SELL CREATE , %.2f' % self.data.close[0])
                self.sell(size=self.p.stake)    # 卖空

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]: # 订单已提交或已接受
            return  # Await further notifications

        if order.status == order.Completed: # 订单已完成
            if order.isbuy():   # 买入
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price
                self.log(buytxt, order.executed.dt)
            else:   # 卖出
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:   # 订单已过期、已取消、保证金
            self.log('%s ,' % order.Status[order.status])
            pass  # Simply log

        # Allow new orders
        self.orderid = None

    def notify_trade(self, trade):
        if trade.isclosed:  # 交易关闭
            self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                     (trade.pnl, trade.pnlcomm))

        elif trade.justopened:  # 交易开启
            self.log('TRADE OPENED, SIZE %2d' % trade.size)


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro() # 创建 Cerebro 引擎

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 开始日期
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 结束日期

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(   # 创建数据源
        dataname=args.data,
        fromdate=fromdate,
        todate=todate)

    # Add the 1st data to cerebro
    cerebro.adddata(data)   # 添加数据源

    # Add the strategy
    cerebro.addstrategy(LongShortStrategy,  # 添加策略
                        period=args.period, # 周期
                        onlylong=args.onlylong, # 只做多
                        csvcross=args.csvcross, # 输出交叉信号到 CSV
                        stake=args.stake)   # 交易量

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcash(args.cash)   # 设置初始资金

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcommission(commission=args.comm,  # 佣金
                                 mult=args.mult,    # 乘数
                                 margin=args.margin)    # 保证金

    cerebro.addanalyzer(SQN)    # 添加分析器

    cerebro.addwriter(bt.WriterFile, csv=args.writercsv, rounding=2)    # 添加 writer

    # And run it
    cerebro.run()   # 运行策略

    # Plot if requested
    if args.plot:
        cerebro.plot(numfigs=args.numfigs, volume=False, zdown=False)   # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(description='MultiData Strategy')  # 创建参数解析器

    parser.add_argument('--data', '-d', # 数据源
                        default='../../datas/2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f', # 开始日期
                        default='2006-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--period', default=15, type=int,   # SMA 的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--onlylong', '-ol', action='store_true',   # 只做多
                        help='Do only long operations')

    parser.add_argument('--writercsv', '-wcsv', action='store_true',    # 输出到 CSV
                        help='Tell the writer to produce a csv stream')

    parser.add_argument('--csvcross', action='store_true',  # 输出交叉信号到 CSV
                        help='Output the CrossOver signals to CSV')

    parser.add_argument('--cash', default=100000, type=int,   # 初始资金
                        help='Starting Cash')

    parser.add_argument('--comm', default=2, type=float,    # 佣金
                        help='Commission for operation')

    parser.add_argument('--mult', default=10, type=int,   # 乘数
                        help='Multiplier for futures')

    parser.add_argument('--margin', default=2000.0, type=float,   # 保证金
                        help='Margin for each future')

    parser.add_argument('--stake', default=1, type=int,  # 交易量
                        help='Stake to apply in each operation')

    parser.add_argument('--plot', '-p', action='store_true',    # 绘制图表
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,   # 绘制图表的数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
