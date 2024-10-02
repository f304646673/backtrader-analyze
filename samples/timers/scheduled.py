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
        when=bt.timer.SESSION_START,
        timer=True,
        cheat=False,
        offset=datetime.timedelta(),
        repeat=datetime.timedelta(),
        weekdays=[],
    )

    def __init__(self):
        bt.ind.SMA()    # 添加指标
        if self.p.timer:
            self.add_timer(
                when=self.p.when,   # 定时器触发时间
                offset=self.p.offset,   # 偏移时间
                repeat=self.p.repeat,   # 重复时间
                weekdays=self.p.weekdays,   # 星期几
            )
        if self.p.cheat:
            self.add_timer(
                when=self.p.when,   # 定时器触发时间
                offset=self.p.offset,   # 偏移时间
                repeat=self.p.repeat,   # 重复时间
                cheat=True, # 作弊
            )

        self.order = None

    def prenext(self):
        self.next()

    def next(self):
        _, isowk, isowkday = self.datetime.date().isocalendar()   # 获取日期的年份、周数、星期几
        txt = '{}, {}, Week {}, Day {}, O {}, H {}, L {}, C {}'.format(
            len(self), self.datetime.datetime(),
            isowk, isowkday,
            self.data.open[0], self.data.high[0],
            self.data.low[0], self.data.close[0])

        print(txt)

    def notify_timer(self, timer, when, *args, **kwargs):
        print('strategy notify_timer with tid {}, when {} cheat {}'.
              format(timer.p.tid, when, timer.p.cheat))

        if self.order is None and timer.p.cheat:
            print('-- {} Create buy order'.format(self.data.datetime.date()))
            self.order = self.buy()

    def notify_order(self, order):
        if order.status == order.Completed:  # 如果订单状态为完成
            print('-- {} Buy Exec @ {}'.format(
                self.data.datetime.date(), order.executed.price))


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()  # 创建 Cerebro 引擎

    # Data feed kwargs
    kwargs = dict(
        timeframe=bt.TimeFrame.Days,
        compression=1,
        sessionstart=datetime.time(9, 0),
        sessionend=datetime.time(17, 30),
    )

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)   # 创建数据源
    cerebro.adddata(data0)  # Add the data to cerebro    # 添加数据源

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')')) # 创建 Broker

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))   # 创建 Sizer

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))  # 创建策略

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))   # 运行策略

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')')) # 绘制图表


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Sample Skeleton'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt',
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',   # 起始日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='', # 结束日期
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',    # cerebro 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='', # broker 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',  # sizer 参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',  # 策略参数
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',   # 绘图参数
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
