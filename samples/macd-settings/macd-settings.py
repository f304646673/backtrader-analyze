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

BTVERSION = tuple(int(x) for x in bt.__version__.split('.'))


class FixedPerc(bt.Sizer):
    '''This sizer simply returns a fixed size for any operation

    Params:
      - ``perc`` (default: ``0.20``) Perc of cash to allocate for operation
    '''

    params = (
        ('perc', 0.20),  # perc of cash to use for operation    # 操作所用现金的百分比
    )

    def _getsizing(self, comminfo, cash, data, isbuy):  # 获取操作的大小
        cashtouse = self.p.perc * cash  # 计算操作所用现金
        if BTVERSION > (1, 7, 1, 93):   # 如果版本大于
            size = comminfo.getsize(data.close[0], cashtouse)   # 获取操作的大小
        else:
            size = cashtouse // data.close[0]   # 获取操作的大小
        return size


class TheStrategy(bt.Strategy):
    '''
    This strategy is loosely based on some of the examples from the Van
    K. Tharp book: *Trade Your Way To Financial Freedom*. The logic:

      - Enter the market if:
        - The MACD.macd line crosses the MACD.signal line to the upside
        - The Simple Moving Average has a negative direction in the last x
          periods (actual value below value x periods ago)

     - Set a stop price x times the ATR value away from the close

     - If in the market:

       - Check if the current close has gone below the stop price. If yes,
         exit.
       - If not, update the stop price if the new stop price would be higher
         than the current
    '''

    params = (
        # Standard MACD Parameters
        ('macd1', 12),  # MACD 指标的短期均线周期，默认为 12
        ('macd2', 26),  # MACD 指标的长期均线周期，默认为 26
        ('macdsig', 9), # MACD 指标的信号线周期，默认为 9
        ('atrperiod', 14),  # ATR Period (standard)   # ATR 指标的周期，默认为 14
        ('atrdist', 3.0),   # ATR distance for stop price   # ATR 值与收盘价的距离，默认为 3.0
        ('smaperiod', 30),  # SMA Period (pretty standard)  # SMA 指标的周期，默认为 30
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction   # 考虑 SMA 趋势方向的回溯周期，默认为 10
    )

    def notify_order(self, order):
        if order.status == order.Completed: # 如果订单已完成
            pass

        if not order.alive():   # 如果订单不活跃
            self.order = None  # indicate no order is pending

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data,   # 创建 MACD 指标
                                       period_me1=self.p.macd1,  # 短期均线周期
                                       period_me2=self.p.macd2, # 长期均线周期
                                       period_signal=self.p.macdsig)    # 信号线周期

        # Cross of macd.macd and macd.signal
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)   # 创建交叉信号

        # To set the stop price
        self.atr = bt.indicators.ATR(self.data, period=self.p.atrperiod)    # 创建 ATR 指标

        # Control market trend
        self.sma = bt.indicators.SMA(self.data, period=self.p.smaperiod)    # 创建 SMA 指标
        self.smadir = self.sma - self.sma(-self.p.dirperiod)    # 计算 SMA 趋势方向

    def start(self):
        self.order = None  # sentinel to avoid operrations on pending order

    def next(self):
        if self.order:
            return  # pending order execution

        if not self.position:  # not in the market  如果不持仓
            if self.mcross[0] > 0.0 and self.smadir < 0.0:  # 如果 MACD 交叉信号大于 0 且 SMA 趋势方向小于 0
                self.order = self.buy() # 买入
                pdist = self.atr[0] * self.p.atrdist    # 计算 ATR 值与收盘价的距离
                self.pstop = self.data.close[0] - pdist  # 设置止损价

        else:  # in the market
            pclose = self.data.close[0] # 当前收盘价
            pstop = self.pstop  # 止损价

            if pclose < pstop:  # 如果收盘价小于止损价
                self.close()  # stop met - get out  # 平仓
            else:
                pdist = self.atr[0] * self.p.atrdist    # 计算 ATR 值与收盘价的距离
                # Update only if greater than
                self.pstop = max(pstop, pclose - pdist)  # 更新止损价


DATASETS = {
    'yhoo': '../../datas/yhoo-1996-2014.txt',
    'orcl': '../../datas/orcl-1995-2014.txt',
    'nvda': '../../datas/nvda-1999-2014.txt',
}


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎
    cerebro.broker.set_cash(args.cash)  # 设置初始资金
    comminfo = bt.commissions.CommInfo_Stocks_Perc(commission=args.commperc,    # 设置佣金
                                                   percabs=True)

    cerebro.broker.addcommissioninfo(comminfo)  # 添加佣金信息

    dkwargs = dict()
    if args.fromdate is not None:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 将字符串转换为日期时间对象，起始日期
        dkwargs['fromdate'] = fromdate

    if args.todate is not None:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 将字符串转换为日期时间对象，结束日期
        dkwargs['todate'] = todate

    # if dataset is None, args.data has been given
    dataname = DATASETS.get(args.dataset, args.data)    # 获取数据源名称
    data0 = bt.feeds.YahooFinanceCSVData(dataname=dataname, **dkwargs)  # 创建数据源
    cerebro.adddata(data0)  # 添加数据源

    cerebro.addstrategy(TheStrategy,    # 添加策略
                        macd1=args.macd1, macd2=args.macd2, # MACD 参数
                        macdsig=args.macdsig,   # MACD 信号线参数
                        atrperiod=args.atrperiod,   # ATR 参数
                        atrdist=args.atrdist,   # ATR 距离参数
                        smaperiod=args.smaperiod,   # SMA 参数
                        dirperiod=args.dirperiod)   # SMA 趋势方向参数

    cerebro.addsizer(FixedPerc, perc=args.cashalloc)    # 设置固定百分比的下单量

    # Add TimeReturn Analyzers for self and the benchmark data
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='alltime_roi',   # 添加分析器, 计算所有时间的 ROI
                        timeframe=bt.TimeFrame.NoTimeFrame)

    cerebro.addanalyzer(bt.analyzers.TimeReturn, data=data0, _name='benchmark',   # 添加分析器, 计算基准数据的 ROI
                        timeframe=bt.TimeFrame.NoTimeFrame)

    # Add TimeReturn Analyzers fot the annuyl returns
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years)  # 添加分析器, 计算年度 ROI
    # Add a SharpeRatio
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Years,   # 添加分析器, 计算夏普比率
                        riskfreerate=args.riskfreerate)

    # Add SQN to qualify the trades
    cerebro.addanalyzer(bt.analyzers.SQN)   # 添加分析器, 计算 SQN
    cerebro.addobserver(bt.observers.DrawDown)  # visualize the drawdown evol   # 添加观察者, 可视化回撤

    results = cerebro.run() # 运行策略
    st0 = results[0]    # 获取结果

    for alyzer in st0.analyzers:
        alyzer.print()

    if args.plot:
        pkwargs = dict(style='bar') # 默认样式为 bar
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs) # 绘制图表


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for Tharp example with MACD')

    group1 = parser.add_mutually_exclusive_group(required=True)   # 创建互斥组
    group1.add_argument('--data', required=False, default=None,  # 数据源
                        help='Specific data to be read in')

    group1.add_argument('--dataset', required=False, action='store',    # 数据集
                        default=None, choices=DATASETS.keys(),
                        help='Choose one of the predefined data sets')

    parser.add_argument('--fromdate', required=False,   # 开始日期
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,  # 结束日期
                        default=None,
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store',   # 初始资金
                        type=float, default=50000,
                        help=('Cash to start with'))

    parser.add_argument('--cashalloc', required=False, action='store',  # 下单量
                        type=float, default=0.20,
                        help=('Perc (abs) of cash to allocate for ops'))

    parser.add_argument('--commperc', required=False, action='store',   # 佣金
                        type=float, default=0.0033,
                        help=('Perc (abs) commision in each operation. '
                              '0.001 -> 0.1%%, 0.01 -> 1%%'))

    parser.add_argument('--macd1', required=False, action='store',  # MACD 参数
                        type=int, default=12,
                        help=('MACD Period 1 value'))

    parser.add_argument('--macd2', required=False, action='store',  # MACD 参数
                        type=int, default=26,
                        help=('MACD Period 2 value'))

    parser.add_argument('--macdsig', required=False, action='store',    # MACD 信号线参数
                        type=int, default=9,
                        help=('MACD Signal Period value'))

    parser.add_argument('--atrperiod', required=False, action='store',  # ATR 参数
                        type=int, default=14,
                        help=('ATR Period To Consider'))

    parser.add_argument('--atrdist', required=False, action='store',    # ATR 距离参数
                        type=float, default=3.0,
                        help=('ATR Factor for stop price calculation'))

    parser.add_argument('--smaperiod', required=False, action='store',  # SMA 参数
                        type=int, default=30,
                        help=('Period for the moving average'))

    parser.add_argument('--dirperiod', required=False, action='store',  # SMA 趋势方向参数
                        type=int, default=10,
                        help=('Period for SMA direction calculation'))

    parser.add_argument('--riskfreerate', required=False, action='store',   # 夏普比率的无风险利率
                        type=float, default=0.01,
                        help=('Risk free rate in Perc (abs) of the asset for '
                              'the Sharpe Ratio'))
    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
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
