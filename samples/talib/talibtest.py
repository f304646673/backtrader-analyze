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


class TALibStrategy(bt.Strategy):
    params = (('ind', 'sma'), ('doji', True),)

    INDS = ['sma', 'ema', 'stoc', 'rsi', 'macd', 'bollinger', 'aroon',
            'ultimate', 'trix', 'kama', 'adxr', 'dema', 'ppo', 'tema',
            'roc', 'williamsr']

    def __init__(self):
        if self.p.doji:  # 是否使用 Doji 蜡烛图模式
            bt.talib.CDLDOJI(self.data.open, self.data.high,    # Doji 蜡烛图
                             self.data.low, self.data.close)

        if self.p.ind == 'sma': # SMA 指标
            bt.talib.SMA(self.data.close, timeperiod=25, plotname='TA_SMA') # 使用 bt.talib.SMA 计算简单移动平均线（SMA），时间周期为 25，绘图名称为 'TA_SMA'
            bt.indicators.SMA(self.data, period=25)   # 使用 bt.indicators.SMA 计算简单移动平均线（SMA），时间周期为 25
        elif self.p.ind == 'ema':   # EMA 指标
            bt.talib.EMA(timeperiod=25, plotname='TA_SMA')  # 使用 bt.talib.EMA 计算指数移动平均线（EMA），时间周期为 25，绘图名称为 'TA_SMA'
            bt.indicators.EMA(period=25)    # 使用 bt.indicators.EMA 计算指数移动平均线（EMA），时间周期为 25
        elif self.p.ind == 'stoc':  # Stochastic 指标
            bt.talib.STOCH(self.data.high, self.data.low, self.data.close,  # 使用 bt.talib.STOCH 计算随机指标（Stochastic），时间周期为 14，快速时间周期为 3，慢速时间周期为 3，绘图名称为 'TA_STOCH'
                           fastk_period=14, slowk_period=3, slowd_period=3,
                           plotname='TA_STOCH')

            bt.indicators.Stochastic(self.data)   # 使用 bt.indicators.Stochastic 计算随机指标（Stochastic）

        elif self.p.ind == 'macd':  # MACD 指标
            bt.talib.MACD(self.data, plotname='TA_MACD')    # 使用 bt.talib.MACD 计算 MACD 指标，绘图名称为 'TA_MACD'
            bt.indicators.MACD(self.data)   # 使用 bt.indicators.MACD 计算 MACD 指标
            bt.indicators.MACDHisto(self.data)  # 使用 bt.indicators.MACDHisto 计算 MACD 直方图
        elif self.p.ind == 'bollinger': # Bollinger 指标
            bt.talib.BBANDS(self.data, timeperiod=25,   # 使用 bt.talib.BBANDS 计算布林带（Bollinger Bands），时间周期为 25，绘图名称为 'TA_BBANDS'
                            plotname='TA_BBANDS')
            bt.indicators.BollingerBands(self.data, period=25)  # 使用 bt.indicators.BollingerBands 计算布林带（Bollinger Bands），时间周期为 25

        elif self.p.ind == 'rsi':   # RSI 指标
            bt.talib.RSI(self.data, plotname='TA_RSI')  # 使用 bt.talib.RSI 计算相对强弱指标（RSI），绘图名称为 'TA_RSI'
            bt.indicators.RSI(self.data)    # 使用 bt.indicators.RSI 计算相对强弱指标（RSI）

        elif self.p.ind == 'aroon': # Aroon 指标
            bt.talib.AROON(self.data.high, self.data.low, plotname='TA_AROON')  # 使用 bt.talib.AROON 计算 Aroon 指标，绘图名称为 'TA_AROON'
            bt.indicators.AroonIndicator(self.data)   # 使用 bt.indicators.AroonIndicator 计算 Aroon 指标

        elif self.p.ind == 'ultimate':  # Ultimate Oscillator 指标
            bt.talib.ULTOSC(self.data.high, self.data.low, self.data.close, # 使用 bt.talib.ULTOSC 计算终极波动指标（Ultimate Oscillator），绘图名称为 'TA_ULTOSC'
                            plotname='TA_ULTOSC')
            bt.indicators.UltimateOscillator(self.data)   # 使用 bt.indicators.UltimateOscillator 计算终极波动指标（Ultimate Oscillator）

        elif self.p.ind == 'trix':  # TRIX 指标
            bt.talib.TRIX(self.data, timeperiod=25,  plotname='TA_TRIX')    # 使用 bt.talib.TRIX 计算三重平滑指标（TRIX），时间周期为 25，绘图名称为 'TA_TRIX'
            bt.indicators.Trix(self.data, period=25)    # 使用 bt.indicators.Trix 计算三重平滑指标（TRIX），时间周期为 25

        elif self.p.ind == 'adxr':  # ADXR 指标
            bt.talib.ADXR(self.data.high, self.data.low, self.data.close,   # 使用 bt.talib.ADXR 计算平均趋向指数（ADX），绘图名称为 'TA_ADXR'
                          plotname='TA_ADXR')
            bt.indicators.ADXR(self.data)   # 使用 bt.indicators.ADXR 计算平均趋向指数（ADX）

        elif self.p.ind == 'kama':  # KAMA 指标
            bt.talib.KAMA(self.data, timeperiod=25, plotname='TA_KAMA') # 使用 bt.talib.KAMA 计算适应性移动平均线（KAMA），时间周期为 25，绘图名称为 'TA_KAMA'
            bt.indicators.KAMA(self.data, period=25)    # 使用 bt.indicators.KAMA 计算适应性移动平均线（KAMA），时间周期为 25

        elif self.p.ind == 'dema':  # DEMA 指标
            bt.talib.DEMA(self.data, timeperiod=25, plotname='TA_DEMA') # 使用 bt.talib.DEMA 计算双指数移动平均线（DEMA），时间周期为 25，绘图名称为 'TA_DEMA'
            bt.indicators.DEMA(self.data, period=25)    # 使用 bt.indicators.DEMA 计算双指数移动平均线（DEMA），时间周期为 25

        elif self.p.ind == 'ppo':   # PPO 指标
            bt.talib.PPO(self.data, plotname='TA_PPO')  # 使用 bt.talib.PPO 计算价格振荡百分比指标（PPO），绘图名称为 'TA_PPO'
            bt.indicators.PPO(self.data, _movav=bt.indicators.SMA)  # 使用 bt.indicators.PPO 计算价格振荡百分比指标（PPO）

        elif self.p.ind == 'tema':  # TEMA 指标
            bt.talib.TEMA(self.data, timeperiod=25, plotname='TA_TEMA')   # 使用 bt.talib.TEMA 计算三重指数移动平均线（TEMA），时间周期为 25，绘图名称为 'TA_TEMA'
            bt.indicators.TEMA(self.data, period=25)    # 使用 bt.indicators.TEMA 计算三重指数移动平均线（TEMA），时间周期为 25

        elif self.p.ind == 'roc':   # ROC 指标
            bt.talib.ROC(self.data, timeperiod=12, plotname='TA_ROC')   # 使用 bt.talib.ROC 计算变动率指标（ROC），时间周期为 12，绘图名称为 'TA_ROC'
            bt.talib.ROCP(self.data, timeperiod=12, plotname='TA_ROCP') # 使用 bt.talib.ROCP 计算变动率指标（ROC），时间周期为 12，绘图名称为 'TA_ROCP'
            bt.talib.ROCR(self.data, timeperiod=12, plotname='TA_ROCR') # 使用 bt.talib.ROCR 计算变动率指标（ROC），时间周期为 12，绘图名称为 'TA_ROCR'
            bt.talib.ROCR100(self.data, timeperiod=12, plotname='TA_ROCR100')   # 使用 bt.talib.ROCR100 计算变动率指标（ROC），时间周期为 12，绘图名称为 'TA_ROCR100'
            bt.indicators.ROC(self.data, period=12)   # 使用 bt.indicators.ROC 计算变动率指标（ROC），时间周期为 12
            bt.indicators.Momentum(self.data, period=12)    # 使用 bt.indicators.Momentum 计算动量指标（Momentum），时间周期为 12
            bt.indicators.MomentumOscillator(self.data, period=12)  # 使用 bt.indicators.MomentumOscillator 计算动量指标（Momentum），时间周期为 12

        elif self.p.ind == 'williamsr': # Williams %R 指标
            bt.talib.WILLR(self.data.high, self.data.low, self.data.close,  # 使用 bt.talib.WILLR 计算威廉指标（Williams %R），时间周期为 14，绘图名称为 'TA_WILLR'
                           plotname='TA_WILLR')
            bt.indicators.WilliamsR(self.data)  # 使用 bt.indicators.WilliamsR 计算威廉指标（Williams %R）


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    dkwargs = dict()
    if args.fromdate:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')    # 开始日期
        dkwargs['fromdate'] = fromdate

    if args.todate:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')    # 结束日期
        dkwargs['todate'] = todate

    data0 = bt.feeds.YahooFinanceCSVData(dataname=args.data0, **dkwargs)    # 创建数据源
    cerebro.adddata(data0)  # Add the data to cerebro    # 添加数据源

    cerebro.addstrategy(TALibStrategy, ind=args.ind, doji=not args.no_doji)   # Add the strategy    # 添加策略

    cerebro.run(runcone=not args.use_next, stdstats=False)  # Run the strategy    # 运行策略
    if args.plot:
        pkwargs = dict(style='candle')
        if args.plot is not True:  # evals to True but is not True
            npkwargs = eval('dict(' + args.plot + ')')  # args were passed
            pkwargs.update(npkwargs)

        cerebro.plot(**pkwargs) # Plot the read data applying any kwargs passed    # 绘制图表


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for sizer')

    parser.add_argument('--data0', required=False,  # 添加参数
                        default='../../datas/yhoo-1996-2015.txt',
                        help='Data to be read in')

    parser.add_argument('--fromdate', required=False,   # 添加参数
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=False,  # 添加参数
                        default='2006-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--ind', required=False, action='store',    # 添加参数
                        default=TALibStrategy.INDS[0],
                        choices=TALibStrategy.INDS,
                        help=('Which indicator pair to show together'))

    parser.add_argument('--no-doji', required=False, action='store_true',   # 添加参数
                        help=('Remove Doji CandleStick pattern checker'))

    parser.add_argument('--use-next', required=False, action='store_true',  # 添加参数
                        help=('Use next (step by step) '
                              'instead of once (batch)'))

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,  # 添加参数
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example (escape the quotes if needed):\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()  # 解析参数


if __name__ == '__main__':
    runstrat()
