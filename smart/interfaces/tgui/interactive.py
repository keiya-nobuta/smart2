#
# Copyright (C) 2016 FUJITSU LIMITED
#
from window import *
from smart import *
from smart.interfaces.tgui.interface import TguiInterface
from smart.transaction import *
from smart.report import Report
import sys, os, copy, textwrap, snack, string, time, re
from snack import *

_TXT_ROOT_TITLE = "Package Installer"
Install_types = [("Install All", "If you choose it, all packages are selected."), \
                ("Busybox base", "Busybox base sample."), \
                ("Customize", "Default, no packages are selected, your can choose packages that you want.")]

INSTALL_ALL = 0
INSTALL_BUSYBOX = 1
INSTALL_CUSTOMIZE = 2

CONFIRM_EXIT = 0
CONFIRM_INSTALL = 1
CONFIRM_LICENSE = 2

class TguiInteractiveInterface(TguiInterface):
    
    def __init__(self, ctrl):
        TguiInterface.__init__(self, ctrl)
                
    def run(self, command=None, argv=None):
        self._ctrl.reloadChannels()
        self.PKGINSTDispMain()

    def confirmChange(self, screen, oldchangeset, newchangeset):
        return self.showChangeSet(screen, newchangeset)

    def PKGINSTDispMain(self):
        STAGE_INSTALL_TYPE = 1
        STAGE_PKG_TYPE     = 2
        STAGE_CUST_LIC     = 3
        STAGE_PACKAGE      = 4
        STAGE_PACKAGE_SPEC = 5
        
        screen = None
        no_gpl3 = False

        cache = self._ctrl.getCache()
        self._changeset = ChangeSet(self._ctrl.getCache())
        packages = self._ctrl.getCache().getPackages()
        if len(packages) < 1:
            print "Error! No packages!"
            sys.exit(0)
        transaction = Transaction(cache, policy=PolicyInstall)
        screen = StartHotkeyScreen(_TXT_ROOT_TITLE)
        if screen == None:
            sys.exit(1)

        install_type = INSTALL_ALL
        stage = STAGE_INSTALL_TYPE
 
        def __init_pkg_type():
            pkgTypeList = []
            
            pkgType_locale = pkgType("locale", False, "If select, you can see/select *-locale/*-localedata packages in the next step.")
            pkgTypeList.append(pkgType_locale)
            pkgType_dev = pkgType("dev", False, "If select, you can see/select *-dev packages in the next step.")
            pkgTypeList.append(pkgType_dev)
            pkgType_doc = pkgType("doc", False, "If select, you can see/select *-doc packages in the next step.")
            pkgTypeList.append(pkgType_doc)
            pkgType_dbg = pkgType("dbg", False, "If select, you can see/select *-dbg packages in the next step.")
            pkgTypeList.append(pkgType_dbg)
            pkgType_staticdev = pkgType("staticdev", False, "If select, you can see/select *-staticdev packages in the next step.")
            pkgTypeList.append(pkgType_staticdev)
            pkgType_ptest = pkgType("ptest", False, "If select, you can see/select *-ptest packages in the next step.")
            pkgTypeList.append(pkgType_ptest)

            
            return pkgTypeList

        pkgTypeList = __init_pkg_type()
        selected_pkgs = []
        selected_pkgs_spec = []
        pkgs_spec = []
        while True:
            #==============================
            # select install type
            #==============================
            if stage == STAGE_INSTALL_TYPE:
                install_type = PKGINSTTypeWindowCtrl(screen, Install_types, install_type)
                stage = STAGE_PACKAGE
                selected_pkgs = []
                selected_pkgs_spec = []
                pkgs_spec = []
            #if install_type != INSTALL_BUSYBOX:
                result = HotkeyExitWindow(screen, confirm_type=CONFIRM_LICENSE)
                if result == "y":
                    no_gpl3 = False
                else:
                    no_gpl3 = True
            #==============================
            # select package
            #==============================
            elif stage == STAGE_PACKAGE:
                (result, selected_pkgs, pkgs_spec) = self.PKGINSTWindowCtrl(screen, install_type, None, no_gpl3, None, selected_pkgs)
                if result == "b":
                    # back
                    stage = STAGE_INSTALL_TYPE
                elif result == "n":
                    stage = STAGE_PKG_TYPE
            #==============================
            # select package type
            #==============================
            elif stage == STAGE_PKG_TYPE:
                (result, pkgTypeList) = PKGTypeSelectWindowCtrl(screen, pkgTypeList)
                if result == "b":
                    # back
                    stage = STAGE_PACKAGE
                elif result == "n":
                    stage = STAGE_PACKAGE_SPEC
            #==============================
            # select special packages(local, dev, dbg, doc) 
            #==============================
            elif stage == STAGE_PACKAGE_SPEC:
                (result, selected_pkgs_spec, pkgs_temp) = self.PKGINSTWindowCtrl(screen, install_type, pkgTypeList, no_gpl3, pkgs_spec, selected_pkgs_spec)
                if result == "b":
                    # back
                    stage = STAGE_PKG_TYPE
                elif result == "k":
                     stage = STAGE_PKG_TYPE
                elif result == "n":
                    for pkg in selected_pkgs:
                        transaction.enqueue(pkg, INSTALL)
                    for pkg in selected_pkgs_spec:
                        transaction.enqueue(pkg, INSTALL)
                    transaction.run()
                    if no_gpl3:
                        oldchangeset = self._changeset
                        newchangeset = transaction.getChangeSet() 
                        result = self.confirmChange(screen, oldchangeset, newchangeset)
                        #continue to install
                        if result == "y":
                            hkey = HotkeyExitWindow(screen, confirm_type=CONFIRM_INSTALL)
                            if hkey == "y":
                                if screen != None:
                                    StopHotkeyScreen(screen)
                                    screen = None
                                self._ctrl.commitTransaction(transaction, confirm=True)
                                break
                            elif hkey == "n":
                                stage = STAGE_PKG_TYPE
                        #don't want to install GPLv3 that depended by others
                        else:
                            stage = STAGE_PKG_TYPE
                    else:
                        if screen != None:
                            StopHotkeyScreen(screen)
                            screen = None

                        self._ctrl.commitTransaction(transaction, confirm=True)
                        break

        if screen != None:
            StopHotkeyScreen(screen)
            screen = None

    def PKGINSTWindowCtrl(self, screen, install_type, pkgTypeList, no_gpl3, packages=None, selected_pkgs=[]):
        STAGE_SELECT = 1
        STAGE_PKG_TYPE = 2
        STAGE_BACK   = 3
        STAGE_INFO   = 4
        STAGE_EXIT   = 5
        STAGE_SEARCH = 6
        STAGE_NEXT = 7

        iTargetSize = 0
        iHostSize = 0

        searched_ret = [] 
        pkgs_spec = []
        position = 0
        search_position = 0
        check = 0
        stage = STAGE_SELECT
        search = None

        if pkgTypeList == None:
            ctrl = self._ctrl
            packages = ctrl.getCache().getPackages()
            if len(packages) > 1:
                sortUpgrades(packages)
                packages.sort()
            display_pkgs = copy.copy(packages)
        else:
            display_pkgs = copy.copy(packages)

        if no_gpl3:
            for pkg in packages:
                for loader in pkg.loaders:
                    info = loader.getInfo(pkg)
                    licence = info.getLicense()
                    if licence:
                        if "GPLv3" in licence:
                            display_pkgs.remove(pkg)
                    break
            packages = copy.copy(display_pkgs)

        if pkgTypeList != None:
            for pkyType in pkgTypeList:
                if pkyType.name == "locale":
                    if not pkyType.status:
                        pkyType_locale = False
                    else:
                        pkyType_locale = True
                elif pkyType.name == "dev":
                    if not pkyType.status:
                        pkyType_dev = False
                    else:
                        pkyType_dev = True
                elif pkyType.name == "doc":
                    if not pkyType.status:
                        pkyType_doc = False
                    else:
                        pkyType_doc = True
                elif pkyType.name == "dbg":
                    if not pkyType.status:
                        pkyType_dbg = False
                    else:
                        pkyType_dbg = True
                elif pkyType.name == "staticdev":
                    if not pkyType.status:
                        pkyType_staticdev = False
                    else:
                        pkyType_staticdev = True
                elif pkyType.name == "ptest":
                    if not pkyType.status:
                        pkyType_ptest = False
                    else:
                        pkyType_ptest = True

            if pkyType_locale or pkyType_dev or pkyType_doc or pkyType_dbg or pkyType_staticdev or pkyType_ptest:
                #Don't show doc and dbg packages
                for pkg in packages:
                    if "-locale-" in pkg.name:
                        if not pkyType_locale:
                            display_pkgs.remove(pkg)
                    elif "-localedata-" in pkg.name:
                        if not pkyType_locale:
                            display_pkgs.remove(pkg)
                    elif pkg.name.endswith('-dev'):
                        if not pkyType_dev:
                            display_pkgs.remove(pkg)
                    elif pkg.name.endswith('-doc'):
                        if not pkyType_doc:
                            display_pkgs.remove(pkg)
                    elif pkg.name.endswith('-dbg'):
                        if not pkyType_dbg:
                            display_pkgs.remove(pkg)
                    elif pkg.name.endswith('-staticdev'):
                        if not pkyType_staticdev:
                            display_pkgs.remove(pkg)
                    elif pkg.name.endswith('-ptest'):
                        if not pkyType_ptest:
                            display_pkgs.remove(pkg)
            else:
                display_pkgs = []

            if install_type == INSTALL_ALL:
                selected_pkgs = copy.copy(display_pkgs)

            if len(display_pkgs) == 0:
                if not no_gpl3:
                    hkey = HotkeyExitWindow(screen, confirm_type=CONFIRM_INSTALL)
                    if hkey == "y":
                        return ("n", selected_pkgs, packages)
                    elif hkey == "n":
                        return ("k", selected_pkgs, packages)
                else:
                    return ("n", selected_pkgs, packages)
        else:
            for pkg in packages:
                    if "-locale-" in pkg.name:
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
                    elif "-localedata-" in pkg.name:
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
                    elif pkg.name.endswith('-dev'):
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
                    elif pkg.name.endswith('-doc'):
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
                    elif pkg.name.endswith('-dbg'):
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
                    elif pkg.name.endswith('-staticdev'):
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
                    elif pkg.name.endswith('-ptest'):
                        display_pkgs.remove(pkg)
                        pkgs_spec.append(pkg)
            if install_type == INSTALL_ALL:
                selected_pkgs = copy.copy(display_pkgs)
            elif install_type == INSTALL_BUSYBOX:
                selected_pkgs = [] 
                first_busybox_position = 0
                for pkg in display_pkgs:
                    if pkg.name.startswith('busybox'): 
                        selected_pkgs.append(pkg)
                        if first_busybox_position == 0:
                            first_busybox_position = position
                    position += 1
                position = first_busybox_position
        
        while True:
            if stage == STAGE_SELECT:
                if search == None:
                    (hkey, position, pkglist) = PKGINSTPackageWindow(screen, \
                                                            display_pkgs, \
                                                            selected_pkgs, \
                                                            position, \
                                                            iTargetSize, \
                                                            iHostSize, \
                                                            search)
                else:
                    (hkey, search_position, pkglist) = PKGINSTPackageWindow(screen, \
                                                             searched_ret, \
                                                             selected_pkgs, \
                                                             search_position, \
                                                             iTargetSize, \
                                                             iHostSize, \
                                                             search)

                if hkey == "n":
                    stage = STAGE_NEXT
                elif hkey == "b":
                    stage = STAGE_BACK
                elif hkey == "i":
                    stage = STAGE_INFO
                elif hkey == "x":
                    stage = STAGE_EXIT
                elif hkey == 'r':
                    stage = STAGE_SEARCH
            elif stage == STAGE_NEXT:
                search = None
                #if in packages select Interface:
                if pkgTypeList == None:
                    return ("n", selected_pkgs, pkgs_spec)
                #if in special type packages(dev,doc,locale) select Interface:
                else:
                    if not no_gpl3:
                        hkey = HotkeyExitWindow(screen, confirm_type=CONFIRM_INSTALL)
                        if hkey == "y":
                            return ("n", selected_pkgs, packages)
                        elif hkey == "n":
                            stage = STAGE_SELECT
                    else:
                        return ("n", selected_pkgs, packages)
            elif stage == STAGE_BACK:
                if not search == None:
                    stage = STAGE_SELECT
                    search = None
                else:
                    return ("b", selected_pkgs, pkgs_spec)
            elif stage == STAGE_INFO:
                ctrl = self._ctrl
                if not search == None:
                    PKGINSTPackageInfoWindow(screen, ctrl, searched_ret[search_position])
                else:
                    PKGINSTPackageInfoWindow(screen, ctrl, display_pkgs[position])
                stage = STAGE_SELECT
            elif stage == STAGE_EXIT:
                hkey = HotkeyExitWindow(screen)
                if hkey == "y":
                    if screen != None:
                        StopHotkeyScreen(screen)
                        screen = None
                    sys.exit(0)
                elif hkey == "n":
                    stage = STAGE_SELECT
            elif stage == STAGE_SEARCH:
                search_position = 0
                search = PKGINSTPackageSearchWindow(screen)
                if not search == None:
                    def __search_pkgs(keyword, pkgs):
                        searched_pgks = []
                        keyword = re.escape(keyword)
                        for pkg in pkgs:
                            if re.compile(keyword, re.IGNORECASE).search(pkg.name):
                                searched_pgks.append(pkg)
                        return searched_pgks
                    searched_ret = __search_pkgs(search, display_pkgs)
                    if len(searched_ret) == 0:
                        buttons = ['OK']
                        (w, h) = GetButtonMainSize(screen)
                        rr = ButtonInfoWindow(screen, "Message", "%s - not found." % search, w, h, buttons)
                        search = None
                stage = STAGE_SELECT

    def showChangeSet(self, screen, changeset):
        gplv3_pkgs = []
        report = Report(changeset)
        report.compute()

        pkgs = report.installing.keys()
        for pkg in pkgs:
            for loader in pkg.loaders:
                info = loader.getInfo(pkg)
                licence = info.getLicense()
                if licence:
                    if "GPLv3" in licence:
                        gplv3_pkgs.append(pkg)
                break
        if len(gplv3_pkgs) > 0:
            hkey = ConfirmGplv3Window(screen, gplv3_pkgs)
            if hkey == "y":
                return "y"
            elif hkey == "n":
                return "n"
        else:
            return "y"
