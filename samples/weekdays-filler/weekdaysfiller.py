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

import datetime


class WeekDaysFiller(object):
    '''Bar Filler to add missing calendar days to trading days'''
    # kickstart value for date comparisons
    ONEDAY = datetime.timedelta(days=1)
    lastdt = datetime.date.max - ONEDAY

    def __init__(self, data, fillclose=False):
        self.fillclose = fillclose
        self.voidbar = [float('Nan')] * data.size()  # init a void bar

    def __call__(self, data):
        '''Empty bars (NaN) or with last close price are added for weekdays with no
        data

        Params:
          - data: the data source to filter/process

        Returns:
          - True (always): bars are removed (even if put back on the stack)

        '''
        dt = data.datetime.date()  # current date in int format
        lastdt = self.lastdt + self.ONEDAY  # move last seen data once forward  # 向前移动一天

        while lastdt < dt:  # loop over gap bars
            if lastdt.isoweekday() < 6:  # Mon-Fri  # 判断是否是周一到周五
                # Fill in date and add new bar to the stack
                if self.fillclose:
                    self.voidbar = [self.lastclose] * data.size()   # 用上一个收盘价填充
                dtime = datetime.datetime.combine(lastdt, data.p.sessionend)    # 合并时间
                self.voidbar[-1] = data.date2num(dtime) # set the date in the bar  # 设置日期
                data._add2stack(self.voidbar[:])    # 添加到栈中

            lastdt += self.ONEDAY  # move lastdt forward    # 向前移动一天

        self.lastdt = dt  # keep a record of the last seen date # 记录最后一个日期

        self.lastclose = data.close[0]  # keep a record of the last close price  # 记录最后一个收盘价
        data._save2stack(erase=True)  # dt bar to the stack and out of stream   # 保存到栈中
        return True  # bars are on the stack (new and original) # 返回 True，表示栈中有新的和原始的 bar
