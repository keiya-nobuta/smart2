#
# Copyright (C) 2016 FUJITSU LIMITED
#

from smart import *
import os


def create(ctrl, command=None, argv=None):
    if command:
        from smart.interfaces.tgui.interface import TguiInterface
        return TguiInterface(ctrl)
    else:
        from smart.interfaces.tgui.interactive import TguiInteractiveInterface
        return TguiInteractiveInterface(ctrl)

