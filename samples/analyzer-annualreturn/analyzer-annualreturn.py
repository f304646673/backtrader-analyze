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
from backtrader.analyzers import (SQN, AnnualReturn, TimeReturn, SharpeRatio,
                                  TradeAnalyzer)


class LongShortStrategy(bt.Strategy):
    '''This strategy buys/sells upong the close price crossing
    upwards/downwards a Simple Moving Average.

    It can be a long-only strategy by setting the param "onlylong" to True
    '''
    
    '''
    这个策略在收盘价向上/向下穿越简单移动平均线时买入/卖出。
    它可以通过将参数“onlylong”设置为 True 来成为仅做多策略。
    
    定义策略的参数：
        period: 移动平均线的周期，默认为 15。
        stake: 每次交易的数量，默认为 1。
        printout: 是否打印输出，默认为 False。
        onlylong: 是否仅做多，默认为 False。
        csvcross: 是否记录交叉点，默认为 False。
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
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # To control operation entries
        self.orderid = None

        # Create SMA on 2nd data
        sma = btind.MovAv.SMA(self.data, period=self.p.period) # 创建一个简单移动平均线（SMA）指标，基于收盘价和指定的周期
        # Create a CrossOver Signal from close an moving average
        self.signal = btind.CrossOver(self.data.close, sma) # 创建一个交叉指标，用于检测收盘价与SMA的交叉
        self.signal.csv = self.p.csvcross

    def next(self):
        if self.orderid:
            return  # if an order is active, no new orders are allowed

        if self.signal > 0.0:  # 如果收盘价向上穿越SMA
            if self.position:    # 如果已经有持仓 
                self.log('CLOSE SHORT , %.2f' % self.data.close[0])
                self.close()    # 平仓

            self.log('BUY CREATE , %.2f' % self.data.close[0])
            self.buy(size=self.p.stake)   # 买入指定数量

        elif self.signal < 0.0: # 如果收盘价向下穿越SMA
            if self.position:   # 如果已经有持仓
                self.log('CLOSE LONG , %.2f' % self.data.close[0])
                self.close()    # 平仓

            if not self.p.onlylong: # 如果允许做空
                self.log('SELL CREATE , %.2f' % self.data.close[0])
                self.sell(size=self.p.stake)    # 卖出指定数量

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]: # 如果订单已提交或已接受
            return  # Await further notifications   等待进一步通知

        if order.status == order.Completed: # 如果订单已完成
            if order.isbuy():   # 如果是买入
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price
                self.log(buytxt, order.executed.dt)
            else:
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]: # 如果订单已过期、已取消或保证金不足
            self.log('%s ,' % order.Status[order.status])
            pass  # Simply log  仅记录

        # Allow new orders
        self.orderid = None

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
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将字符串转换为日期时间对象
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 将字符串转换为日期时间对象

    # Create the 1st data
    data = btfeeds.BacktraderCSVData(   # 创建一个数据源
        dataname=args.data, # 数据文件路径
        fromdate=fromdate,  # 起始日期
        todate=todate)  # 结束日期

    # Add the 1st data to cerebro
    cerebro.adddata(data)   # 将数据添加到 Cerebro 引擎

    # Add the strategy
    cerebro.addstrategy(LongShortStrategy,  # 添加策略
                        period=args.period, # 简单移动平均线的周期 
                        onlylong=args.onlylong, # 是否仅做多
                        csvcross=args.csvcross, # 是否记录交叉点
                        stake=args.stake)   # 每次交易的数量

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcash(args.cash)   # 设置初始资金

    # Add the commission - only stocks like a for each operation
    cerebro.broker.setcommission(commission=args.comm,  # 设置手续费
                                 mult=args.mult,    # 设置合约乘数
                                 margin=args.margin)    # 设置保证金

    tframes = dict( # 时间帧
        days=bt.TimeFrame.Days, # 天
        weeks=bt.TimeFrame.Weeks,   # 周
        months=bt.TimeFrame.Months, # 月
        years=bt.TimeFrame.Years)   # 年

    # Add the Analyzers
    cerebro.addanalyzer(SQN)    # 添加 SQN 分析器
    if args.legacyannual:   # 如果使用传统年度收益率分析器
        cerebro.addanalyzer(AnnualReturn)   # 添加传统年度收益率分析器
        cerebro.addanalyzer(SharpeRatio, legacyannual=True)   # 添加传统夏普比率分析器     
    else:
        cerebro.addanalyzer(TimeReturn, timeframe=tframes[args.tframe])  # 添加时间收益率分析器，设置时间帧
        cerebro.addanalyzer(SharpeRatio, timeframe=tframes[args.tframe])    # 添加夏普比率分析器，设置时间帧

    cerebro.addanalyzer(TradeAnalyzer)  # 添加交易分析器

    cerebro.addwriter(bt.WriterFile, csv=args.writercsv, rounding=4)    # 添加写入器

    # And run it
    cerebro.run()   # 运行 Cerebro 引擎

    # Plot if requested
    if args.plot:   # 如果请求绘图
        cerebro.plot(numfigs=args.numfigs, volume=False, zdown=False)   # 绘图


def parse_args():
    parser = argparse.ArgumentParser(description='TimeReturn')  # 创建一个参数解析器

    parser.add_argument('--data', '-d', # 数据文件路径
                        default='../../datas/2005-2006-day-001.txt',
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f', # 起始日期
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',   # 结束日期
                        default='2006-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--period', default=15, type=int,   # 移动平均线的周期
                        help='Period to apply to the Simple Moving Average')

    parser.add_argument('--onlylong', '-ol', action='store_true',   # 仅做多
                        help='Do only long operations')

    parser.add_argument('--writercsv', '-wcsv', action='store_true',    # 输出到 CSV
                        help='Tell the writer to produce a csv stream')

    parser.add_argument('--csvcross', action='store_true',  # 输出交叉点到 CSV
                        help='Output the CrossOver signals to CSV')

    group = parser.add_mutually_exclusive_group()   # 创建一个互斥组，只能选择其中一个选项
    group.add_argument('--tframe', default='years', required=False,  # 时间帧
                       choices=['days', 'weeks', 'months', 'years'],
                       help='TimeFrame for the returns/Sharpe calculations')

    group.add_argument('--legacyannual', action='store_true',   # 使用传统年度收益率分析器
                       help='Use legacy annual return analyzer')

    parser.add_argument('--cash', default=100000, type=int,  # 初始资金
                        help='Starting Cash')

    parser.add_argument('--comm', default=2, type=float,    # 手续费
                        help='Commission for operation')

    parser.add_argument('--mult', default=10, type=int,  # 合约乘数
                        help='Multiplier for futures')

    parser.add_argument('--margin', default=2000.0, type=float,   # 保证金
                        help='Margin for each future')

    parser.add_argument('--stake', default=1, type=int,
                        help='Stake to apply in each operation')    # 每次交易的数量

    parser.add_argument('--plot', '-p', action='store_true',    # 是否绘图
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,   # 绘图时的图形数量
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
