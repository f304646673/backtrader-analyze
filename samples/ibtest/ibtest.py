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
from backtrader.utils import flushfile  # win32 quick stdout flushing


class TestStrategy(bt.Strategy):
    params = dict(
        smaperiod=5,   # 移动平均线的周期
        trade=False,    # 是否交易
        stake=10,   # 每次交易的数量
        exectype=bt.Order.Market,   # 下单类型
        stopafter=0,    # 在多少个 LIVE 数据行之后停止
        valid=None, # 订单有效时间
        cancel=0,   # 在多少个操作行之后取消订单
        donotsell=False,    # 买入后是否卖出
        stoptrail=False,    # 是否使用 StopTrail 订单
        stoptraillimit=False,   # 是否使用 StopTrailLimit 订单
        trailamount=None,   # StopTrail 订单的 trailamount
        trailpercent=None,  # StopTrail 订单的 trailpercent
        limitoffset=None,   # StopTrailLimit 订单的 limitoffset
        oca=False,  # 是否使用 OCA 订单
        bracket=False,  # 是否使用 Bracket 订单
    )

    def __init__(self):
        # To control operation entries
        self.orderid = list()
        self.order = None

        self.counttostop = 0    # 计数器
        self.datastatus = 0 # 数据状态

        # Create SMA on 2nd data
        self.sma = bt.indicators.MovAv.SMA(self.data, period=self.p.smaperiod)  # 创建移动平均线指标

        print('--------------------------------------------------')
        print('Strategy Created')
        print('--------------------------------------------------')

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE: # 如果数据状态为 LIVE
            self.counttostop = self.p.stopafter  # 计数器为 stopafter
            self.datastatus = 1 # 数据状态为 1

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF:', msg)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Cancelled, order.Rejected]:  # 如果订单状态为完成、取消或拒绝
            self.order = None

        print('-' * 50, 'ORDER BEGIN', datetime.datetime.now())
        print(order)
        print('-' * 50, 'ORDER END')

    def notify_trade(self, trade):
        print('-' * 50, 'TRADE BEGIN', datetime.datetime.now())
        print(trade)
        print('-' * 50, 'TRADE END')

    def prenext(self):
        self.next(frompre=True)

    def next(self, frompre=False):
        txt = list()
        txt.append('Data0')
        txt.append('%04d' % len(self.data0))
        dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
        txt.append('{}'.format(self.data.datetime[0]))
        txt.append('%s' % self.data.datetime.datetime(0).strftime(dtfmt))
        txt.append('{}'.format(self.data.open[0]))
        txt.append('{}'.format(self.data.high[0]))
        txt.append('{}'.format(self.data.low[0]))
        txt.append('{}'.format(self.data.close[0]))
        txt.append('{}'.format(self.data.volume[0]))
        txt.append('{}'.format(self.data.openinterest[0]))
        txt.append('{}'.format(self.sma[0]))
        print(', '.join(txt))

        if len(self.datas) > 1 and len(self.data1):
            txt = list()
            txt.append('Data1')
            txt.append('%04d' % len(self.data1))
            dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
            txt.append('{}'.format(self.data1.datetime[0]))
            txt.append('%s' % self.data1.datetime.datetime(0).strftime(dtfmt))
            txt.append('{}'.format(self.data1.open[0]))
            txt.append('{}'.format(self.data1.high[0]))
            txt.append('{}'.format(self.data1.low[0]))
            txt.append('{}'.format(self.data1.close[0]))
            txt.append('{}'.format(self.data1.volume[0]))
            txt.append('{}'.format(self.data1.openinterest[0]))
            txt.append('{}'.format(float('NaN')))
            print(', '.join(txt))

        if self.counttostop:  # stop after x live lines # 如果计数器不为 0
            self.counttostop -= 1   # 计数器减 1
            if not self.counttostop:    # 如果计数器为 0
                self.env.runstop()  # 停止运行
                return

        if not self.p.trade:    # 如果不交易
            return

        if self.datastatus and not self.position and len(self.orderid) < 1:   # 如果数据状态为 1、没有持仓且订单数小于 1
            exectype = self.p.exectype if not self.p.oca else bt.Order.Limit    # 如果不使用 OCA 订单，exectype 为 self.p.exectype，否则为 bt.Order.Limit
            close = self.data0.close[0] # 获取收盘价
            price = round(close * 0.90, 2)  # 价格为收盘价的 90%
            self.order = self.buy(size=self.p.stake,    # 买入
                                  exectype=exectype,    # 下单类型
                                  price=price,  # 价格
                                  valid=self.p.valid,   # 有效时间
                                  transmit=not self.p.bracket)  # 是否传输

            self.orderid.append(self.order) # 将订单添加到订单列表

            if self.p.bracket:  # 如果使用 Bracket 订单
                # low side
                self.sell(size=self.p.stake,    # 卖出
                          exectype=bt.Order.Stop,   # 下单类型
                          price=round(price * 0.90, 2),   # 价格为 90%
                          valid=self.p.valid,   # 有效时间
                          transmit=False,   # 不传输
                          parent=self.order)    # 父订单

                # high side
                self.sell(size=self.p.stake,    # 卖出
                          exectype=bt.Order.Limit,  # 下单类型
                          price=round(close * 1.10, 2), # 价格为收盘价的 110%
                          valid=self.p.valid,   # 有效时间
                          transmit=True,    # 传输
                          parent=self.order)    # 父订单

            elif self.p.oca:
                self.buy(size=self.p.stake,   # 买入
                         exectype=bt.Order.Limit,   # 下单类型
                         price=round(self.data0.close[0] * 0.80, 2),    # 价格为收盘价的 80%
                         oco=self.order)    # OCO 订单

            elif self.p.stoptrail:
                self.sell(size=self.p.stake,    # 卖出
                          exectype=bt.Order.StopTrail,  # 下单类型
                          # price=round(self.data0.close[0] * 0.90, 2),
                          valid=self.p.valid,   # 有效时间
                          trailamount=self.p.trailamount,   
                          trailpercent=self.p.trailpercent) # StopTrail 订单

            elif self.p.stoptraillimit:
                p = round(self.data0.close[0] - self.p.trailamount, 2)  # 价格为收盘价减 trailamount
                # p = self.data0.close[0]
                self.sell(size=self.p.stake,    # 卖出
                          exectype=bt.Order.StopTrailLimit,   # 下单类型
                          price=p,  # 价格
                          plimit=p + self.p.limitoffset,    # 限价
                          valid=self.p.valid,   # 有效时间
                          trailamount=self.p.trailamount,
                          trailpercent=self.p.trailpercent) # StopTrailLimit 订单

        elif self.position.size > 0 and not self.p.donotsell:   # 如果持仓数量大于 0 且不禁止卖出
            if self.order is None:  # 如果订单为空
                self.order = self.sell(size=self.p.stake // 2,  # 卖出, 卖出数量为 stake 的一半
                                       exectype=bt.Order.Market,    # 下单类型
                                       price=self.data0.close[0])   # 价格为收盘价

        elif self.order is not None and self.p.cancel:  # 如果订单不为空且 cancel 为 True, 取消订单
            if self.datastatus > self.p.cancel: # 如果数据状态大于 cancel
                self.cancel(self.order) # 取消订单

        if self.datastatus: # 如果数据状态为 1
            self.datastatus += 1    # 数据状态加 1

    def start(self):
        if self.data0.contractdetails is not None:  # 如果 contractdetails 不为空
            print('Timezone from ContractDetails: {}'.format(   # 输出时区
                  self.data0.contractdetails.m_timeZoneId)) # 从 contractdetails 获取时区

        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
                  'OpenInterest', 'SMA']
        print(', '.join(header))

        self.done = False


def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()  # 创建一个 Cerebro 引擎

    storekwargs = dict(
        host=args.host, port=args.port, # 主机和端口
        clientId=args.clientId, timeoffset=not args.no_timeoffset,  # 时区偏移
        reconnect=args.reconnect, timeout=args.timeout, # 重连次数和超时时间
        notifyall=args.notifyall, _debug=args.debug # 是否通知所有消息和是否调试
    )

    if args.usestore:   # 如果使用 store
        ibstore = bt.stores.IBStore(**storekwargs)  # 创建 IBStore 数据源

    if args.broker: # 如果使用 broker
        if args.usestore:   # 如果使用 store
            broker = ibstore.getbroker()    # 获取 broker
        else:
            broker = bt.brokers.IBBroker(**storekwargs)   # 创建 IBBroker

        cerebro.setbroker(broker)   # 设置 broker

    timeframe = bt.TimeFrame.TFrame(args.timeframe)  # 时间周期, 默认为 1 分钟
    # Manage data1 parameters
    tf1 = args.timeframe1   # 时间周期
    tf1 = bt.TimeFrame.TFrame(tf1) if tf1 is not None else timeframe    # 时间周期, 默认为 1 分钟
    cp1 = args.compression1 # 压缩
    cp1 = cp1 if cp1 is not None else args.compression  # 压缩

    if args.resample or args.replay:    # 如果 resample 或 replay
        datatf = datatf1 = bt.TimeFrame.Ticks   # 时间周期
        datacomp = datacomp1 = 1    # 压缩
    else:
        datatf = timeframe  # 时间周期
        datacomp = args.compression   # 压缩
        datatf1 = tf1   # 时间周期
        datacomp1 = cp1 # 压缩

    fromdate = None
    if args.fromdate:   # 如果开始日期不为空
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in args.fromdate))
        fromdate = datetime.datetime.strptime(args.fromdate, dtformat)  # 将字符串转换为日期时间对象

    IBDataFactory = ibstore.getdata if args.usestore else bt.feeds.IBData   # 获取数据源

    datakwargs = dict(
        timeframe=datatf, compression=datacomp, # 时间周期和压缩
        historical=args.historical, fromdate=fromdate,  # 是否历史数据和开始日期
        rtbar=args.rtbar,   # 是否实时数据
        qcheck=args.qcheck, # 超时时间
        what=args.what, # 价格类型
        backfill_start=not args.no_backfill_start,  # 是否回填
        backfill=not args.no_backfill,  # 是否回填
        latethrough=args.latethrough,   # 是否允许迟到
        tz=args.timezone    # 时区
    )

    if not args.usestore and not args.broker:   # neither store nor broker  如果既不使用 store 也不使用 broker
        datakwargs.update(storekwargs)  # pass the store args over the data     将 store 参数传递给数据源

    data0 = IBDataFactory(dataname=args.data0, **datakwargs)    # 创建数据源

    data1 = None
    if args.data1 is not None:  # 如果 data1 不为空
        if args.data1 != args.data0:    # 如果 data1 不等于 data0
            datakwargs['timeframe'] = datatf1   # 时间周期
            datakwargs['compression'] = datacomp1   # 压缩
            data1 = IBDataFactory(dataname=args.data1, **datakwargs)    # 创建数据源
        else:
            data1 = data0

    rekwargs = dict(
        timeframe=timeframe, compression=args.compression,  # 时间周期和压缩
        bar2edge=not args.no_bar2edge,  # 是否到达边缘
        adjbartime=not args.no_adjbartime,  # 是否调整时间
        rightedge=not args.no_rightedge,    # 是否到达右边缘
        takelate=not args.no_takelate,  # 是否接受迟到
    )

    if args.replay: # 如果 replay
        cerebro.replaydata(data0, **rekwargs)   # 回放数据

        if data1 is not None:
            rekwargs['timeframe'] = tf1  # 时间周期
            rekwargs['compression'] = cp1   # 压缩
            cerebro.replaydata(data1, **rekwargs)   # 回放数据

    elif args.resample: # 如果 resample
        cerebro.resampledata(data0, **rekwargs)  # 重采样数据

        if data1 is not None:
            rekwargs['timeframe'] = tf1 # 时间周期
            rekwargs['compression'] = cp1   # 压缩
            cerebro.resampledata(data1, **rekwargs) # 重采样数据

    else:
        cerebro.adddata(data0)  # 将数据添加到 Cerebro 引擎
        if data1 is not None:
            cerebro.adddata(data1)  # 将数据添加到 Cerebro 引擎

    if args.valid is None:
        valid = None
    else:
        valid = datetime.timedelta(seconds=args.valid)  # 有效时间
    # Add the strategy
    cerebro.addstrategy(TestStrategy,   # 添加策略
                        smaperiod=args.smaperiod,   # 移动平均线的周期
                        trade=args.trade,   # 是否交易
                        exectype=bt.Order.ExecType(args.exectype),  # 下单类型
                        stake=args.stake,   # 每次交易的数量
                        stopafter=args.stopafter,   # 在多少个 LIVE 数据行之后停止
                        valid=valid,    # 有效时间
                        cancel=args.cancel, # 在多少个操作行之后取消订单
                        donotsell=args.donotsell,   # 买入后是否卖出
                        stoptrail=args.stoptrail,   # 是否使用 StopTrail 订单
                        stoptraillimit=args.traillimit, # 是否使用 StopTrailLimit 订单
                        trailamount=args.trailamount,   # StopTrail 订单的 trailamount
                        trailpercent=args.trailpercent, # StopTrail 订单的 trailpercent
                        limitoffset=args.limitoffset,   # StopTrailLimit 订单的 limitoffset
                        oca=args.oca,   # 是否使用 OCA 订单
                        bracket=args.bracket)   # 是否使用 OCA 订单

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars=args.exactbars)   # 运行 Cerebro 引擎

    if args.plot and args.exactbars < 1:  # plot if possible    如果需要绘制图表
        cerebro.plot()  # 绘制图表


def parse_args():
    parser = argparse.ArgumentParser(   # 创建参数解析器
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, # 参数默认值帮助格式
        description='Test Interactive Brokers integration')

    parser.add_argument('--exactbars', default=1, type=int,  # exactbars 等级
                        required=False, action='store',
                        help='exactbars level, use 0/-1/-2 to enable plotting')

    parser.add_argument('--plot',   # 是否绘图
                        required=False, action='store_true',
                        help='Plot if possible')

    parser.add_argument('--stopafter', default=0, type=int, # 在多少个 LIVE 数据行之后停止
                        required=False, action='store',
                        help='Stop after x lines of LIVE data')

    parser.add_argument('--usestore',   # 是否使用 store
                        required=False, action='store_true',
                        help='Use the store pattern')

    parser.add_argument('--notifyall',  # 是否通知所有消息
                        required=False, action='store_true',
                        help='Notify all messages to strategy as store notifs')

    parser.add_argument('--debug',  # 是否调试
                        required=False, action='store_true',
                        help='Display all info received form IB')

    parser.add_argument('--host', default='127.0.0.1',  # 主机
                        required=False, action='store',
                        help='Host for the Interactive Brokers TWS Connection')

    parser.add_argument('--qcheck', default=0.5, type=float,    # 超时时间
                        required=False, action='store',
                        help=('Timeout for periodic '
                              'notification/resampling/replaying check'))

    parser.add_argument('--port', default=7496, type=int,   # 端口
                        required=False, action='store',
                        help='Port for the Interactive Brokers TWS Connection')

    parser.add_argument('--clientId', default=None, type=int,   # Client Id
                        required=False, action='store',
                        help='Client Id to connect to TWS (default: random)')

    parser.add_argument('--no-timeoffset',  # 是否使用时区偏移
                        required=False, action='store_true',
                        help=('Do not Use TWS/System time offset for non '
                              'timestamped prices and to align resampling'))

    parser.add_argument('--reconnect', default=3, type=int,  # 重连次数
                        required=False, action='store',
                        help='Number of recconnection attempts to TWS')

    parser.add_argument('--timeout', default=3.0, type=float,   # 超时时间
                        required=False, action='store',
                        help='Timeout between reconnection attempts to TWS')

    parser.add_argument('--data0', default=None,    # 数据文件
                        required=True, action='store',
                        help='data 0 into the system')

    parser.add_argument('--data1', default=None,    # 数据文件
                        required=False, action='store',
                        help='data 1 into the system')

    parser.add_argument('--timezone', default=None,   # 时区
                        required=False, action='store',
                        help='timezone to get time output into (pytz names)')

    parser.add_argument('--what', default=None,  # 价格类型
                        required=False, action='store',
                        help='specific price type for historical requests')

    parser.add_argument('--no-backfill_start',  # 是否回填
                        required=False, action='store_true',
                        help='Disable backfilling at the start')

    parser.add_argument('--latethrough',    # 是否允许迟到
                        required=False, action='store_true',
                        help=('if resampling replaying, adjusting time '
                              'and disabling time offset, let late samples '
                              'through'))

    parser.add_argument('--no-backfill',    # 是否回填
                        required=False, action='store_true',
                        help='Disable backfilling after a disconnection')

    parser.add_argument('--rtbar', default=False,   # 是否实时数据
                        required=False, action='store_true',
                        help='Use 5 seconds real time bar updates if possible')

    parser.add_argument('--historical',  # 是否历史数据
                        required=False, action='store_true',
                        help='do only historical download')

    parser.add_argument('--fromdate',   # 起始日期
                        required=False, action='store',
                        help=('Starting date for historical download '
                              'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--smaperiod', default=5, type=int,   # 移动平均线的周期
                        required=False, action='store',
                        help='Period to apply to the Simple Moving Average')

    pgroup = parser.add_mutually_exclusive_group(required=False)    # 创建一个互斥组，只能选择其中一个选项

    pgroup.add_argument('--replay',  # 回放
                        required=False, action='store_true',
                        help='replay to chosen timeframe')

    pgroup.add_argument('--resample',   # 重采样
                        required=False, action='store_true',
                        help='resample to chosen timeframe')

    parser.add_argument('--timeframe', default=bt.TimeFrame.Names[0],   # 时间周期
                        choices=bt.TimeFrame.Names,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay')

    parser.add_argument('--compression', default=1, type=int,   # 压缩
                        required=False, action='store',
                        help='Compression for Resample/Replay')

    parser.add_argument('--timeframe1', default=None,   # 时间周期
                        choices=bt.TimeFrame.Names,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay - Data1')

    parser.add_argument('--compression1', default=None, type=int,   # 压缩
                        required=False, action='store',
                        help='Compression for Resample/Replay - Data1')

    parser.add_argument('--no-takelate',    # 是否接受迟到
                        required=False, action='store_true',
                        help=('resample/replay, do not accept late samples '
                              'in new bar if the data source let them through '
                              '(latethrough)'))

    parser.add_argument('--no-bar2edge',    # 是否到达边缘
                        required=False, action='store_true',
                        help='no bar2edge for resample/replay')

    parser.add_argument('--no-adjbartime',
                        required=False, action='store_true',
                        help='no adjbartime for resample/replay')

    parser.add_argument('--no-rightedge',   # 是否到达右边缘
                        required=False, action='store_true',
                        help='no rightedge for resample/replay')

    parser.add_argument('--broker',  # 是否使用 broker
                        required=False, action='store_true',
                        help='Use IB as broker')

    parser.add_argument('--trade',  # 是否交易
                        required=False, action='store_true',
                        help='Do Sample Buy/Sell operations')

    parser.add_argument('--donotsell',  # 买入后是否卖出
                        required=False, action='store_true',
                        help='Do not sell after a buy')

    parser.add_argument('--exectype', default=bt.Order.ExecTypes[0],    # 下单类型
                        choices=bt.Order.ExecTypes,
                        required=False, action='store',
                        help='Execution to Use when opening position')

    parser.add_argument('--stake', default=10, type=int,    # 每次交易的数量
                        required=False, action='store',
                        help='Stake to use in buy operations')

    parser.add_argument('--valid', default=None, type=int,  # 有效时间
                        required=False, action='store',
                        help='Seconds to keep the order alive (0 means DAY)')

    pgroup = parser.add_mutually_exclusive_group(required=False)    # 创建一个互斥组，只能选择其中一个选项
    pgroup.add_argument('--stoptrail',  # 是否使用 StopTrail 订单
                        required=False, action='store_true',
                        help='Issue a stoptraillimit after buy( do not sell')

    pgroup.add_argument('--traillimit', # 是否使用 StopTrailLimit 订单
                        required=False, action='store_true',
                        help='Issue a stoptrail after buying (do not sell')

    pgroup.add_argument('--oca',    # 是否使用 OCA 订单
                        required=False, action='store_true',
                        help='Test oca by putting 2 orders in a group')

    pgroup.add_argument('--bracket',    # 是否使用 Bracket 订单
                        required=False, action='store_true',
                        help='Test bracket orders by issuing high/low sides')

    pgroup = parser.add_mutually_exclusive_group(required=False)    # 创建一个互斥组，只能选择其中一个选项
    pgroup.add_argument('--trailamount', default=None, type=float,
                        required=False, action='store',
                        help='trailamount for StopTrail order')

    pgroup.add_argument('--trailpercent', default=None, type=float, 
                        required=False, action='store',
                        help='trailpercent for StopTrail order')

    parser.add_argument('--limitoffset', default=None, type=float,
                        required=False, action='store',
                        help='limitoffset for StopTrailLimit orders')

    parser.add_argument('--cancel', default=0, type=int,
                        required=False, action='store',
                        help=('Cancel a buy order after n bars in operation,'
                              ' to be combined with orders like Limit'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
