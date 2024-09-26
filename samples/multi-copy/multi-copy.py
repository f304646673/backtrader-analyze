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
import random

import backtrader as bt


class TheStrategy(bt.Strategy):
    '''
    This strategy is capable of:
        当移动平均线向上交叉时做多。
      - Going Long with a Moving Average upwards CrossOver
        当 MACD 向上交叉时再次做多。
      - Going Long again with a MACD upwards CrossOver
        当上述多头头寸出现相应的向下交叉时平仓。
      - Closing the aforementioned longs with the corresponding downwards
        crossovers
    '''

    params = (
        ('myname', None),
        ('dtarget', None),
        ('stake', 100), # 每次交易的数量
        ('macd1', 12),  # MACD 指标的短期均线周期
        ('macd2', 26),  # MACD 指标的长期均线周期
        ('macdsig', 9), # MACD 指标的信号线周期
        ('sma1', 10),   # 移动平均线指标的周期
        ('sma2', 30),   # 移动平均线指标的周期
    )

    def notify_order(self, order):
        if not order.alive():   # 如果订单已完成
            if not order.isbuy():  # going flat # 如果订单是卖出
                self.order = 0  

            if order.status == order.Completed: # 如果订单已完成
                tfields = [self.p.myname,
                           len(self),
                           order.data.datetime.date(),
                           order.data._name,
                           'BUY' * order.isbuy() or 'SELL',
                           order.executed.size, order.executed.price]

                print(','.join(str(x) for x in tfields))

    def __init__(self):
        # Choose data to buy from
        self.dtarget = self.getdatabyname(self.p.dtarget)   # 获取数据

        # Create indicators
        sma1 = bt.ind.SMA(self.dtarget, period=self.p.sma1) # 创建移动平均线指标
        sma2 = bt.ind.SMA(self.dtarget, period=self.p.sma2) # 创建移动平均线指标
        self.smasig = bt.ind.CrossOver(sma1, sma2)  # 创建交叉信号

        macd = bt.ind.MACD(self.dtarget,    # 创建 MACD 指标
                           period_me1=self.p.macd1, # 短期均线周期
                           period_me2=self.p.macd2, # 长期均线周期
                           period_signal=self.p.macdsig)    # 信号线周期

        # Cross of macd.macd and macd.signal
        self.macdsig = bt.ind.CrossOver(macd.macd, macd.signal)   # 创建交叉信号

    def start(self):
        self.order = 0  # sentinel to avoid operrations on pending order

        tfields = ['Name', 'Length', 'Datetime', 'Operation/Names',
                   'Position1.Size', 'Position2.Size']
        print(','.join(str(x) for x in tfields))

    def next(self):
        tfields = [self.p.myname,
                   len(self),
                   self.data.datetime.date(),
                   self.getposition(self.data0).size]
        if len(self.datas) > 1:
            tfields.append(self.getposition(self.data1).size)   # 获取持仓数量

        print(','.join(str(x) for x in tfields))

        buysize = self.p.stake // 2  # let each signal buy half # 让每个信号买入一半
        if self.macdsig[0] > 0.0:   # 如果交叉信号大于 0
            self.buy(data=self.dtarget, size=buysize)   # 买入

        if self.smasig[0] > 0.0:    # 如果交叉信号大于 0
            self.buy(data=self.dtarget, size=buysize)   # 买入

        size = self.getposition(self.dtarget).size  # 获取持仓数量

        # if 2x in the market, let each potential close ... close 1/2
        if size == self.p.stake:    # 如果持仓数量等于每次交易的数量
            size //= 2  # 平仓一半

        if self.macdsig[0] < 0.0:   # 如果交叉信号小于 0
            self.close(data=self.dtarget, size=size)    # 平仓

        if self.smasig[0] < 0.0:    # 如果交叉信号小于 0
            self.close(data=self.dtarget, size=size)    # 平仓


class TheStrategy2(TheStrategy):
    '''
    Subclass of TheStrategy to simply change the parameters

    '''
    params = (
        ('stake', 200), # 每次交易的数量
        ('macd1', 15),  # MACD 指标的短期均线周期
        ('macd2', 22),  # MACD 指标的长期均线周期
        ('macdsig', 7), # MACD 指标的信号线周期
        ('sma1', 15),   # 移动平均线指标的周期
        ('sma2', 50),   # 移动平均线指标的周期
    )


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎
    cerebro.broker.set_cash(args.cash)  # 设置初始资金

    dkwargs = dict()
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将日期字符串转换为 datetime 对象, 起始日期
        dkwargs['fromdate'] = fromdate  # 设置起始日期

    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 将日期字符串转换为 datetime 对象, 结束日期
        dkwargs['todate'] = todate  # 设置结束日期

    # if dataset is None, args.data has been given
    data0 = bt.feeds.YahooFinanceCSVData(dataname=args.data0, **dkwargs)    # 创建数据源
    cerebro.adddata(data0, name='MyData0')  # 添加数据源

    st0kwargs = dict()
    if args.st0 is not None:
        tmpdict = eval('dict(' + args.st0 + ')')  # args were passed
        st0kwargs.update(tmpdict)

    cerebro.addstrategy(TheStrategy,    # 添加策略
                        myname='St1', dtarget='MyData0', **st0kwargs)

    if args.copydata:
        data1 = data0.copyas('MyData1')
        cerebro.adddata(data1)  # 添加数据源
        dtarget = 'MyData1'

    else:  # use same target
        dtarget = 'MyData0'

    st1kwargs = dict()
    if args.st1 is not None:
        tmpdict = eval('dict(' + args.st1 + ')')  # args were passed
        st1kwargs.update(tmpdict)

    cerebro.addstrategy(TheStrategy2,   # 添加策略
                        myname='St2', dtarget=dtarget, **st1kwargs)

    results = cerebro.run() # 运行策略

    if args.plot:
        pkwargs = dict(style='bar')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs)


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Tharp example with MACD')

    # pgroup = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--data0', required=False,  # 数据文件路径
                        default='../../datas/yhoo-1996-2014.txt',
                        help='Specific data0 to be read in')

    parser.add_argument('--fromdate', required=False,   # 起始日期
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,  # 结束日期
                        default='2006-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store',   # 初始资金
                        type=float, default=50000,
                        help=('Cash to start with'))

    parser.add_argument('--copydata', required=False, action='store_true',  # 是否复制数据
                        help=('Copy Data for 2nd strategy'))

    parser.add_argument('--st0', required=False, action='store',    # 策略参数
                        default=None,
                        help=('Params for 1st strategy: as a list of comma '
                              'separated name=value pairs like: '
                              'stake=100,macd1=12,macd2=26,macdsig=9,'
                              'sma1=10,sma2=30'))

    parser.add_argument('--st1', required=False, action='store',    # 策略参数
                        default=None,
                        help=('Params for 1st strategy: as a list of comma '
                              'separated name=value pairs like: '
                              'stake=200,macd1=15,macd2=22,macdsig=7,'
                              'sma1=15,sma2=50'))

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
