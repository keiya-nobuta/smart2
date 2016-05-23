#
# Copyright (C) 2016 FUJITSU LIMITED
#
from smart.interfaces.tgui.progress import TguiProgress
from smart.interface import Interface
from smart.fetcher import Fetcher
from smart.const import DEBUG
from smart import *
import sys


class TguiInterface(Interface):

    def __init__(self, ctrl):
        Interface.__init__(self, ctrl)
        self._progress = TguiProgress()
        self._activestatus = False

    def run(self, command=None, argv=None):
        result = Interface.run(self, command, argv)
        self.setCatchExceptions(False)
        return result

    def getProgress(self, obj, hassub=False):
        self._progress.setHasSub(hassub)
        self._progress.setFetcherMode(isinstance(obj, Fetcher))
        return self._progress

    def askContCancel(self, question, default=False):
        if question[-1] not in ".!?":
            question += "."
        return self.askYesNo(question+_(" Continue?"), default)

