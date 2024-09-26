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

# References:
#  - https://www.reddit.com/r/algotrading/comments/5jez2b/can_anyone_replicate_this_strategy/
#  - http://dark-bid.com/BTFD-only-strategy-that-matters.html

import argparse
import datetime

import backtrader as bt


class ValueUnlever(bt.observers.Value):
    '''Extension of regular Value observer to add leveraged view'''
    lines = ('value_lever', 'asset')    # 添加 value_lever 和 asset 两个线
    params = (('assetstart', 100000.0), ('lever', True),)   # 添加 assetstart 和 lever 两个参数

    def next(self):
        super(ValueUnlever, self).next()    # 调用父类的 next 方法
        if self.p.lever:    
            self.lines.value_lever[0] = self._owner.broker._valuelever  # 计算杠杆价值

        if len(self) == 1:
            self.lines.asset[0] = self.p.assetstart # 设置资产初始值
        else:
            change = self.data[0] / self.data[-1]   # 计算资产变化
            self.lines.asset[0] = change * self.lines.asset[-1] # 计算资产


class St(bt.Strategy):
    params = (
        ('fall', -0.01),    # 下跌幅度
        ('hold', 2),    # 持有时间
        ('approach', 'highlow'),    # 逼近方式
        ('target', 1.0),    # 目标
        ('prorder', False),   # 是否打印订单
        ('prtrade', False),  # 是否打印交易
        ('prdata', False),  # 是否打印数据
    )

    def __init__(self):
        if self.p.approach == 'closeclose':   # 如果逼近方式为 closeclose
            self.pctdown = self.data.close / self.data.close(-1) - 1.0  # 计算下跌幅度，即收盘价与前一天收盘价的比值减 1
        elif self.p.approach == 'openclose':    # 如果逼近方式为 openclose
            self.pctdown = self.data.close / self.data.open - 1.0   # 计算下跌幅度，即收盘价与开盘价的比值减 1
        elif self.p.approach == 'highclose':    # 如果逼近方式为 highclose
            self.pctdown = self.data.close / self.data.high - 1.0   # 计算下跌幅度，即收盘价与最高价的比值减 1
        elif self.p.approach == 'highlow':  # 如果逼近方式为 highlow
            self.pctdown = self.data.low / self.data.high - 1.0 # 计算下跌幅度，即最低价与最高价的比值减 1

    def next(self):
        if self.position:   # 如果有持仓
            if len(self) == self.barexit:   # 如果持有时间达到 hold
                self.close()    # 平仓
                if self.p.prdata:
                    print(','.join(str(x) for x in  
                                   ['DATA', 'CLOSE',
                                    self.data.datetime.date().isoformat(),
                                    self.data.close[0],
                                    float('NaN')]))
        else:
            if self.pctdown <= self.p.fall: # 如果下跌幅度小于 fall
                self.order_target_percent(target=self.p.target)   # 买入目标百分比
                self.barexit = len(self) + self.p.hold  # 记录持有时间

                if self.p.prdata:
                    print(','.join(str(x) for x in
                                   ['DATA', 'OPEN',
                                    self.data.datetime.date().isoformat(),
                                    self.data.close[0],
                                    self.pctdown[0]]))

    def start(self):
        if self.p.prtrade:
            print(','.join(
                ['TRADE', 'Status', 'Date', 'Value', 'PnL', 'Commission']))
        if self.p.prorder:
            print(','.join(
                ['ORDER', 'Type', 'Date', 'Price', 'Size', 'Commission']))
        if self.p.prdata:
            print(','.join(['DATA', 'Action', 'Date', 'Price', 'PctDown']))

    def notify_order(self, order):
        if order.status in [order.Margin, order.Rejected, order.Canceled]:  # 如果订单状态为保证金、拒绝或取消
            print('ORDER FAILED with status:', order.getstatusname())
        elif order.status == order.Completed:   # 如果订单状态为完成
            if self.p.prorder:
                print(','.join(map(str, [
                    'ORDER', 'BUY' * order.isbuy() or 'SELL',
                    self.data.num2date(order.executed.dt).date().isoformat(),
                    order.executed.price,
                    order.executed.size,
                    order.executed.comm,
                ]
                )))

    def notify_trade(self, trade):
        if not self.p.prtrade:
            return

        if trade.isclosed:  # 如果交易已关闭
            print(','.join(map(str, [
                'TRADE', 'CLOSE',
                self.data.num2date(trade.dtclose).date().isoformat(),   # 交易关闭的日期
                trade.value,    # 交易价值
                trade.pnl,  # 交易盈亏
                trade.commission,   # 交易佣金
            ]
            )))
        elif trade.justopened:  # 如果交易刚刚打开
            print(','.join(map(str, [
                'TRADE', 'OPEN',
                self.data.num2date(trade.dtopen).date().isoformat(),    # 交易打开的日期
                trade.value,    # 交易价值
                trade.pnl,  # 交易盈亏
                trade.commission,   # 交易佣金
            ]
            )))


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        kwargs[d] = datetime.datetime.strptime(a, dtfmt + tmfmt * ('T' in a))

    if not args.offline:    # 如果不使用离线文件
        YahooData = bt.feeds.YahooFinanceData   # 使用 YahooFinanceData
    else:
        YahooData = bt.feeds.YahooFinanceCSVData    # 使用 YahooFinanceCSVData

    # Data feed - no plot - observer will do the job
    data = YahooData(dataname=args.data, plot=False, **kwargs)  # 创建数据源
    cerebro.adddata(data)   # 将数据添加到 Cerebro 引擎

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')')) # 创建 Broker，参数从命令行中获取

    # Add a commission
    cerebro.broker.setcommission(**eval('dict(' + args.comminfo + ')')) # 设置手续费

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))  # 添加策略

    # Add specific observer
    cerebro.addobserver(ValueUnlever, **eval('dict(' + args.valobserver + ')'))   # 添加 ValueUnlever 观察者

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))   # 运行策略

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))  # 绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(' - '.join([
            'BTFD',
            'http://dark-bid.com/BTFD-only-strategy-that-matters.html',
            ('https://www.reddit.com/r/algotrading/comments/5jez2b/'
             'can_anyone_replicate_this_strategy/')]))
        )

    parser.add_argument('--offline', required=False, action='store_true',   # 是否使用离线文件
                        help='Use offline file with ticker name')

    parser.add_argument('--data', required=False, default='^GSPC',  # 数据文件
                        metavar='TICKER', help='Yahoo ticker to download')

    parser.add_argument('--fromdate', required=False, default='1990-01-01',   # 起始日期
                        metavar='YYYY-MM-DD[THH:MM:SS]',
                        help='Starting date[time]')

    parser.add_argument('--todate', required=False, default='2016-10-01',   # 结束日期
                        metavar='YYYY-MM-DD[THH:MM:SS]',
                        help='Ending date[time]')

    parser.add_argument('--cerebro', required=False, default='stdstats=False',  # Cerebro 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False,     # Broker 参数
                        default='cash=100000.0, coc=True',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--valobserver', required=False,    # 观察者参数
                        default='assetstart=100000.0',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False,  # 策略参数
                        default='approach="highlow"',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--comminfo', required=False, default='leverage=2.0',   # 手续费参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',   # 绘图参数
                        nargs='?', const='volume=False',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
