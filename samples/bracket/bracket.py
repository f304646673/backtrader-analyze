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


class St(bt.Strategy):
    params = dict(
        ma=bt.ind.SMA,  # 移动平均线指标
        p1=5,   # 短周期
        p2=15,  # 长周期
        limit=0.005,    # 限价单的价格偏移
        limdays=3,  # 限价单的有效期
        limdays2=1000,  # 止损单和止盈单的有效期
        hold=10,    # 持有时间
        usebracket=False,  # use order_target_size  使用 order_target_size
        switchp1p2=False,  # switch prices of order1 and order2 切换 order1 和 order2 的价格
    )

    def notify_order(self, order):
        print('{}: Order ref: {} / Type {} / Status {}'.format(
            self.data.datetime.date(0),
            order.ref, 'Buy' * order.isbuy() or 'Sell',
            order.getstatusname()))

        if order.status == order.Completed: # 如果订单完成
            self.holdstart = len(self)  # 记录持有开始的时间

        if not order.alive() and order.ref in self.orefs:   # 如果订单不活跃且订单的 ref 在 self.orefs 中
            self.orefs.remove(order.ref)    # 从 self.orefs 中移除订单的 ref

    def __init__(self):
        ma1, ma2 = self.p.ma(period=self.p.p1), self.p.ma(period=self.p.p2) # 创建两个移动平均线指标
        self.cross = bt.ind.CrossOver(ma1, ma2)   # 创建交叉指标

        self.orefs = list()   # 订单列表

        if self.p.usebracket:
            print('-' * 5, 'Using buy_bracket')

    def next(self):
        if self.orefs:  # 如果有订单
            return  # pending orders do nothing 挂单不做任何操作

        if not self.position: # 如果没有持仓
            if self.cross > 0.0:  # crossing up 交叉上穿

                close = self.data.close[0]  # 当前的收盘价
                p1 = close * (1.0 - self.p.limit)   # 限价单的价格
                p2 = p1 - 0.02 * close  # 止损单的价格
                p3 = p1 + 0.02 * close  # 止盈单的价格

                valid1 = datetime.timedelta(self.p.limdays) # 限价单的有效期
                valid2 = valid3 = datetime.timedelta(self.p.limdays2)   # 止损单和止盈单的有效期

                if self.p.switchp1p2:   # 切换 order1 和 order2 的价格
                    p1, p2 = p2, p1 # 切换 order1 和 order2 的价格
                    valid1, valid2 = valid2, valid1 # 切换 order1 和 order2 的有效期

                if not self.p.usebracket:   # 如果不使用 order_target_size
                    o1 = self.buy(exectype=bt.Order.Limit,  # 买入限价单
                                  price=p1, # 价格
                                  valid=valid1, # 有效期
                                  transmit=False)   # 不立即传输

                    print('{}: Oref {} / Buy at {}'.format(
                        self.datetime.date(), o1.ref, p1))

                    o2 = self.sell(exectype=bt.Order.Stop,  # 卖出止损单
                                   price=p2,    # 价格
                                   valid=valid2,    # 有效期
                                   parent=o1,   # 父订单
                                   transmit=False)  # 不立即传输

                    print('{}: Oref {} / Sell Stop at {}'.format(
                        self.datetime.date(), o2.ref, p2))

                    o3 = self.sell(exectype=bt.Order.Limit, # 卖出止盈单
                                   price=p3,    # 价格
                                   valid=valid3,    # 有效期
                                   parent=o1,   # 父订单
                                   transmit=True)   # 立即传输

                    print('{}: Oref {} / Sell Limit at {}'.format(
                        self.datetime.date(), o3.ref, p3))

                    self.orefs = [o1.ref, o2.ref, o3.ref]   # 记录订单的 ref

                else:
                    os = self.buy_bracket(
                        price=p1, valid=valid1,  # 买入限价单
                        stopprice=p2, stopargs=dict(valid=valid2),  # 卖出止损单
                        limitprice=p3, limitargs=dict(valid=valid3),)   # 卖出止盈单

                    self.orefs = [o.ref for o in os]    # 记录订单的 ref

        else:  # in the market
            if (len(self) - self.holdstart) >= self.p.hold: # 持有时间超过指定时间
                pass  # do nothing in this case


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):    # 获取 fromdate 和 todate
        if a:   # 如果存在
            strpfmt = dtfmt + tmfmt * ('T' in a)    # 日期时间格式
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)  # 将字符串转换为日期时间对象

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)   # 创建数据源
    cerebro.adddata(data0)  # 将数据添加到 Cerebro 引擎

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')')) # 创建 Broker，参数从命令行中获取

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))   # 创建 Sizer，参数从命令行中获取

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))   # 创建策略，参数从命令行中获取

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))   # 运行策略

    if args.plot:  # Plot if requested to   如果请求绘图
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, # 参数默认值帮助格式
        description=(
            'Sample Skeleton'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt', # 数据文件路径
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',   # 起始日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='', # 结束日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',    # Cerebro 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='', # Broker 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',  # Sizer 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',  # 策略参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',   # 绘图参数
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
