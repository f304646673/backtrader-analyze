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


class TestSizer(bt.Sizer):
    params = dict(stake=1)

    # 确定每次交易的头寸大小
    def _getsizing(self, comminfo, cash, data, isbuy):
        dt, i = self.strategy.datetime.date(), data._id
        # 如果是买入交易，头寸大小为 self.p.stake，如果是卖出交易，头寸大小为 self.p.stake * 2。
        s = self.p.stake * (1 + (not isbuy))
        print('{} Data {} OType {} Sizing to {}'.format(
            dt, data._name, ('buy' * isbuy) or 'sell', s))

        return s


class St(bt.Strategy):
    params = dict(
        enter=[1, 3, 4],  # data ids are 1 based
        hold=[7, 10, 15],  # data ids are 1 based
        usebracket=True,
        rawbracket=True,
        pentry=0.015,
        plimits=0.03,
        valid=10,
    )

    def notify_order(self, order):
        if order.status == order.Submitted:
            return

        dt, dn = self.datetime.date(), order.data._name
        print('{} {} Order {} Status {}'.format(
            dt, dn, order.ref, order.getstatusname())
        )

        whichord = ['main', 'stop', 'limit', 'close']
        if not order.alive():  # not alive - nullify    # 如果订单不活跃
            dorders = self.o[order.data]    # 获取订单列表
            idx = dorders.index(order)  # 获取订单在订单列表中的索引
            dorders[idx] = None
            print('-- No longer alive {} Ref'.format(whichord[idx]))

            if all(x is None for x in dorders):
                dorders[:] = []  # empty list - New orders allowed

    def __init__(self):
        self.o = dict()  # orders per data (main, stop, limit, manual-close)
        self.holding = dict()  # holding periods per data

    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.date(), d._name  # 获取当前日期和数据名称
            pos = self.getposition(d).size  # 获取持仓数量
            print('{} {} Position {}'.format(dt, dn, pos))

            if not pos and not self.o.get(d, None):  # no market / no orders    # 如果没有持仓且没有订单
                if dt.weekday() == self.p.enter[i]: # if weekday is a desired one    # 如果是指定的交易日
                    if not self.p.usebracket:
                        self.o[d] = [self.buy(data=d)]  # keep the order for further reference  保留订单以供进一步参考
                        print('{} {} Buy {}'.format(dt, dn, self.o[d][0].ref))

                    else:
                        p = d.close[0] * (1.0 - self.p.pentry)  # entry limit price    # 买入限价
                        pstp = p * (1.0 - self.p.plimits)   # stop price    # 止损价格
                        plmt = p * (1.0 + self.p.plimits)   # limit price    # 限价
                        valid = datetime.timedelta(self.p.valid)    # 有效期

                        if self.p.rawbracket:   # 如果使用原始 bracket
                            o1 = self.buy(data=d, exectype=bt.Order.Limit,  # 买入限价单
                                          price=p, valid=valid, transmit=False)

                            o2 = self.sell(data=d, exectype=bt.Order.Stop,  # 卖出止损单
                                           price=pstp, size=o1.size,
                                           transmit=False, parent=o1)

                            o3 = self.sell(data=d, exectype=bt.Order.Limit, # 卖出限价单
                                           price=plmt, size=o1.size,
                                           transmit=True, parent=o1)

                            self.o[d] = [o1, o2, o3]    # 保存订单

                        else:
                            self.o[d] = self.buy_bracket(   # 买入 bracket
                                data=d, price=p, stopprice=pstp,
                                limitprice=plmt, oargs=dict(valid=valid))

                        print('{} {} Main {} Stp {} Lmt {}'.format(
                            dt, dn, *(x.ref for x in self.o[d])))

                    self.holding[d] = 0

            elif pos:  # exiting can also happen after a number of days
                self.holding[d] += 1    # 持仓天数加 1
                if self.holding[d] >= self.p.hold[i]:   # 如果持仓天数超过指定天数
                    o = self.close(data=d)  # close the position    # 平仓
                    self.o[d].append(o)  # manual order to list of orders   # 将手动订单添加到订单列表
                    print('{} {} Manual Close {}'.format(dt, dn, o.ref))
                    if self.p.usebracket:   # 如果使用 bracket
                        self.cancel(self.o[d][1])  # cancel stop side   # 取消止损单
                        print('{} {} Cancel {}'.format(dt, dn, self.o[d][1]))


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):    # 获取开始日期和结束日期
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data0 = bt.feeds.YahooFinanceCSVData(dataname=args.data0, **kwargs)   # 创建数据源
    cerebro.adddata(data0, name='d0')

    data1 = bt.feeds.YahooFinanceCSVData(dataname=args.data1, **kwargs)  # 创建数据源
    data1.plotinfo.plotmaster = data0
    cerebro.adddata(data1, name='d1')

    data2 = bt.feeds.YahooFinanceCSVData(dataname=args.data2, **kwargs) # 创建数据源
    data2.plotinfo.plotmaster = data0   # 设置主数据源
    cerebro.adddata(data2, name='d2')   # 将数据添加到 Cerebro 引擎

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))   # 创建 Broker
    cerebro.broker.setcommission(commission=0.001)  # 设置手续费

    # Sizer
    # cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))
    cerebro.addsizer(TestSizer, **eval('dict(' + args.sizer + ')'))   # 创建 Sizer

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')')) # 创建策略

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))   # 运行策略

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))  # 绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Multiple Values and Brackets'
        )
    )

    parser.add_argument('--data0', default='../../datas/nvda-1999-2014.txt',    # 数据文件路径
                        required=False, help='Data0 to read in')

    parser.add_argument('--data1', default='../../datas/yhoo-1996-2014.txt',    # 数据文件路径
                        required=False, help='Data1 to read in')

    parser.add_argument('--data2', default='../../datas/orcl-1995-2014.txt',    # 数据文件路径
                        required=False, help='Data1 to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='2001-01-01',  # 开始日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2007-01-01',   # 结束日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',    # Cerebro 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='', # 交易所参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',  # Sizer 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',  # 策略参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',   # 是否绘图
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
