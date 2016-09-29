#encoding=utf-8 
#
# Copyright (C) 2016 FUJITSU LIMITED
#
import sys, os, copy, textwrap, snack, string, time, re
from snack import * 

ACTION_INSTALL    = 0
ACTION_REMOVE     = 1
ACTION_UPGRADE    = 2
ACTION_GET_SOURCE = 3
ACTION_GET_SPDX   = 4


Confirm_type_list = [("Exit","\n Do you really terminate it?\n\n"), \
                     ("Confirm install","\n Do you want to begin installation?\n\n"), \
                     ("License","\n Do you want to display GPLv3 packages?\n\n"), \
                     ("Confirm remove","\n Do you want to begin removing?\n\n"), \
                     ("Confirm upgrade","\n Do you want to begin upgrading?\n\n"), \
                     ("Confirm get source","\n Do you want to begin getting source?\n\n"), \
                     ("Confirm get SPDX","\n Do you want to begin getting SPDX files?\n\n") \
                    ]

class pkgType:
    name = None
    status = None
    description = None

    def __init__(self, type, status, desc):
        self.name = type
        self.status = False
        self.description = desc

#------------------------------------------------------------
# def GetWindowSize()
#
#   Get Window size.
#
# Input:
#   insScreen : screen instance
# Output:
#   int       : window height
#   int       : window width
#------------------------------------------------------------
def GetWindowSize(insScreen):
    return (insScreen.width, insScreen.height)

#------------------------------------------------------------
# def GetHotkeyMainSize()
#
#   Get best full screen main object size for HotKey mode
#
# Input:
#   insScreen : screen instance
# Output:
#   int       : width
#   int       : height
#------------------------------------------------------------
def GetHotKeyMainSize(insScreen):
    (width, height) = GetWindowSize(insScreen)

    width -= 8

    # It is not centered well only by doing -9 when the Height is an Odd.
    # In addition, it is necessary to do 1.
    height -= (9 - (height % 2))

    return (width, height)
#------------------------------------------------------------
# def _StatusToggle(insLi, sHkey, iIdx, selected_packages, packages, install_type)
#
#   package select window, "selection" function.
#
# Input:
#    insLi              : instance of Listbox
#    sHkey              : hotkey selected
#    iIdx               : index selected
#    selected_packages  : selected_package
#    packages           : display packages
#    install_type       :INSTALL or REMOVE or UPDATE
# Output:
#    packages : showed packages
#------------------------------------------------------------

def _StatusToggle(insLi, sHkey, iIdx, selected_packages, packages, install_type):
    pkg = packages[iIdx]
    #print "select package : %s " % pkg.name
    if sHkey == " " or sHkey == "ENTER":
        if install_type == ACTION_INSTALL and (not pkg.installed):
            if pkg in selected_packages:
                selected_packages.remove(pkg)
                newsign = " "
            else:
                selected_packages.append(pkg)
                newsign = "*"
        elif install_type == ACTION_REMOVE:
            if pkg in selected_packages:
                selected_packages.remove(pkg)
                newsign = " "
            else:
                selected_packages.append(pkg)
                newsign = "-"
        elif install_type == ACTION_UPGRADE:
            if pkg in selected_packages:
                selected_packages.remove(pkg)
                newsign = " "
            else:
                selected_packages.append(pkg)
                newsign = "U"
        elif install_type == ACTION_GET_SOURCE or install_type == ACTION_GET_SPDX :
            if pkg in selected_packages:
                selected_packages.remove(pkg)
                newsign = " "
            else:
                selected_packages.append(pkg)
                newsign = "S"
        else:
            return insLi
    item = "[%s] %s" % (newsign, pkg.name)
    insLi.replace(item, iIdx)
    return insLi
#------------------------------------------------------------
# def _SelectAll(insLi, sHkey,numPackage,selected_packages, packages, install_type))
#
#   package select window, "select all" function.
#
# Input:
#    insLi             : instance of Listbox
#    sHkey             : hotkey selected
#    numPackage        : number of showed packages
#    selected_packages : selected_package
#    packages          : showed packages
#    install_type      : INSTALL or REMOVE or UPDATE
# Output:
#    insLi :changed instance of Listbox
#------------------------------------------------------------
def _SelectAll(insLi, sHkey, numPackage, selected_packages, packages, \
                                                       install_type):
    haveSelected=False      
    for pkg in packages:
        if (not pkg in selected_packages) and ((install_type==ACTION_INSTALL and (not pkg.installed))or \
                                                                    not install_type==ACTION_INSTALL):
            haveSelected=True
            break

#replace sign in list

    if install_type == ACTION_INSTALL:
        if haveSelected :
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if (not pkg in selected_packages) and (not pkg.installed):
                    selected_packages.append(pkg)
                    item = "[%s] %s" % ("*", pkg.name)
                    insLi.replace(item,iIdx)
        else:
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if (pkg in selected_packages) and (not pkg.installed):
                    selected_packages.remove(pkg)
                    item = "[%s] %s" % (" ", pkg.name)
                    insLi.replace(item,iIdx)

    elif install_type == ACTION_REMOVE:
        if haveSelected :
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if not pkg in selected_packages:
                    selected_packages.append(pkg)
                    item = "[%s] %s" % ("-", pkg.name)
                    insLi.replace(item,iIdx)
        else:
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if pkg in selected_packages:
                    selected_packages.remove(pkg)
                    item = "[%s] %s" % (" ", pkg.name)
                    insLi.replace(item,iIdx)

    elif install_type == ACTION_UPGRADE:
        if haveSelected :
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if not pkg in selected_packages:
                    selected_packages.append(pkg)
                    item = "[%s] %s" % ("U", pkg.name)
                    insLi.replace(item,iIdx)
        else:
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if pkg in selected_packages:
                    selected_packages.remove(pkg)
                    item = "[%s] %s" % (" ", pkg.name)
                    insLi.replace(item,iIdx)

    elif install_type == ACTION_GET_SOURCE or install_type == ACTION_GET_SPDX:
        if haveSelected :
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if not pkg in selected_packages:
                    selected_packages.append(pkg)
                    item = "[%s] %s" % ("S", pkg.name)
                    insLi.replace(item,iIdx)
        else:
            for iIdx in range(0,numPackage):
                pkg=packages[iIdx]
                if pkg in selected_packages:
                    selected_packages.remove(pkg)
                    item = "[%s] %s" % (" ", pkg.name)
                    insLi.replace(item,iIdx)

    return insLi

#_SelectAll


#------------------------------------------------------------
# def StartHotkeyScreen()
#
#   Setup snack's screen and hotkey dict for Hotkey mode.
#
# Input:
#   sText : root text
# Output:
#   ins   : screen instance
#------------------------------------------------------------
def StartHotkeyScreen(sText):

    # Set screen mode
    os.environ['NEWT_MONO'] = "1"
    env_term = os.getenv("TERM").upper()
    if env_term == "VT100":
        print "\x1b[?25l"  # cursor off

    # Setup hotkey dictionary
    for x in string.ascii_letters:
        snack.hotkeys[x] = ord(x)
        snack.hotkeys[ord(x)] = x
    snack.hotkeys["ENTER"] = 0x0d
    snack.hotkeys[0x0d] = "ENTER"
    snack.hotkeys["PD"] = 0x800c
    snack.hotkeys[0x800c] = "PD"

    # Start snack's screen
    screen = snack.SnackScreen()
    screen.drawRootText(0, 0, sText)
    screen.pushHelpLine(" ")
      
    # Window size check
    (width, height) = GetWindowSize(screen)
    if width < 80 or height < 24:
        StopHotkeyScreen(screen)
        screen = None
        print "Your screen is too small! It must be at least 24 lines by 80 columns!"

    return screen

#------------------------------------------------------------
# def HotkeyExitWindow(insScreen, confirm_install=False)
#
#   Display "Exit" window and exit for Hotkey mode.
#
# Input:
#   insScreen : screen instance
#   confirm_install=False : just exit without install
#   confirm_install=False : just exit and begin to install
# Output:
#   int       : "y" or "n"
#------------------------------------------------------------
def HotkeyExitWindow(insScreen, confirm_type=0):

    # Display Exit Window
    myhotkeys = {"Y" : "y", \
                 "y" : "y", \
                 "N" : "n", \
                 "n" : "n"}
    
    result = HotkeyInfoWindow(insScreen, Confirm_type_list[confirm_type][0], \
                 Confirm_type_list[confirm_type][1], \
                 40, 4, myhotkeys, "Y:yes  N:no")

    return result

#------------------------------------------------------------
# def StopHotkeyScreen()
#
#   Finish snack's screen
#
# Input:
#   insScreen : screen instance
# Output:
#   None
#------------------------------------------------------------
def StopHotkeyScreen(insScreen):

    # Finish Snack's screen
    insScreen.finish()

    # Resume screen mode
    env_term = os.getenv("TERM").upper()
    if env_term == "VT100":
        print "\x1b[?25h"  # cursor on

#------------------------------------------------------------
# def HotkeyInfoWindow()
#
#   Display information window for Hotkey mode.
#
# Input:
#   insScreen             : screen instance
#   sTitle                : title string
#   sText                 : main text
#   iWidth                : width of main text
#   iHeight               : height of main text
#   dctHotkeys{str : srr} : Hotkey dictionary
#                           [hotkey string, rtncode]
#   sHtext                : Hotkey information text
# Output:
#   str : rtncode in Hotkey dictionary
#------------------------------------------------------------
def HotkeyInfoWindow(insScreen, sTitle, sText, iWidth, iHeight, \
                     dctHotkeys, sHtext):

    # Get line number
    length = len(sText)
    index = 0
    count = 0
    scroll = 0
    while index < length:
        if sText[index] == "\n":
            count += 1
            if count > iHeight:
                scroll = 1
                break
        index += 1

    # Create Text instance
    t1 = snack.Textbox(iWidth - scroll * 2, iHeight, sText, scroll)
    t2 = snack.Textbox(iWidth, 1, "-" * iWidth)
    t3 = snack.Textbox(iWidth, 1, sHtext)

    # Create Grid instance
    g = snack.GridForm(insScreen, sTitle, 1, 3)
    g.add(t1, 0, 0)
    g.add(t2, 0, 1, (-1, 0, -1, 0))
    g.add(t3, 0, 2, (0, 0, 0, -1))
    for x in dctHotkeys.keys():
        g.addHotKey(x)
    # Display window
    while True:
        result = g.run()
        if dctHotkeys.has_key(result):
            break

    # Return
    insScreen.popWindow()
    return dctHotkeys[result]

#------------------------------------------------------------
# def PKGINSTTypeInfoWindow()
#
#   Display install type information window.
#
# Input:
#   insScreen    : screen instance
#   sSubject     : install type subject
#   sDescription : description about the install type
# Output:
#   None
#------------------------------------------------------------
def PKGINSTTypeInfoWindow(insScreen, sSubject, sDescription):

    # Create Main Text
    (main_width, main_height) = GetHotKeyMainSize(insScreen)

    wrapper = textwrap.TextWrapper(width = main_width - 2)

    wrapper.initial_indent    = ""
    wrapper.subsequent_indent = ""
    main_text = wrapper.fill("[ %s ]" % sSubject) + "\n"

    wrapper.initial_indent    = "  "
    wrapper.subsequent_indent = "  "
    main_text += (wrapper.fill(sDescription) + "\n\n")

    # Display information window
    HotkeyInfoWindow(insScreen, "Install type information", main_text, \
                     main_width, main_height, {"b" : "b", "B" : "b"}, "B:Back")

#------------------------------------------------------------
# def PKGINSTTypeWindowCtrl()
#
#    Select install type
#
# Input:
#    insScreen         : screen instance
#    insPKGINSTXmlinfo : xml information
#    insPKGINSTPkginfo : package information
#    iType             : select type (first -1)
#
# Output:
#    int  : select type
#------------------------------------------------------------
def PKGINSTTypeWindowCtrl(insScreen, lstSubject, iType):

    type = iType

    while True:
        (hkey, type) = PKGINSTTypeWindow(insScreen, lstSubject, type)

        if hkey == "ENTER" or hkey == " ":
            # select/unselect
            return type

        elif hkey == "i":
            # info
            description = lstSubject[type][1]
            subject = lstSubject[type][0]
            PKGINSTTypeInfoWindow(insScreen, subject, description)

        elif hkey == "x":
            # exit
            exit_hkey = HotkeyExitWindow(insScreen)
            if exit_hkey == "y":
                if insScreen != None:
                    StopHotkeyScreen(insScreen)
                    insScreen = None
                sys.exit(0)

#------------------------------------------------------------
# def PKGINSTTypeWindow()
#
#   Display install type select window.
#
# Input:
#   insScreen  : screen instance
#   lstSubject : install type subject list
#      [ str ]
#        str : subject of each install type
#   iPosition  : current entry position
# Output:
#   str   : pressed hotkey "ENTER", " ", "i", or "x"
#   int   : position
#------------------------------------------------------------
def PKGINSTTypeWindow(insScreen, lstSubject, iPosition):

    # Create CheckboxTree instance
    (main_width, main_height) = GetHotKeyMainSize(insScreen)

    if len(lstSubject) > main_height:
        scroll = 1
    else:
        scroll = 0

    li = snack.Listbox(main_height, scroll = scroll, width = main_width)

    idx = 0
    for idx in range(len(lstSubject)):
        str = "%s" % lstSubject[idx][0]
        li.append(str, idx)

    num_subject = len(lstSubject)
    if num_subject > iPosition:
        li.setCurrent(iPosition)
    else:
        li.setCurrent(num_subject - 1)
    # Create Text instance
    t1 = snack.Textbox(main_width, 1, "-" * main_width)
    text = "SPACE/ENTER:select  I:Info  X:eXit"
    t2 = snack.Textbox(main_width, 1, text)

    # Create Grid instance
    g = snack.GridForm(insScreen, "Select install type", 1, 3)
    g.add(li, 0, 0)
    g.add(t1, 0, 1, (-1, 0, -1, 0))
    g.add(t2, 0, 2, (0, 0, 0, -1))

    myhotkeys = {"ENTER" : "ENTER", \
                 " "     : " ", \
                 "i"     : "i", \
                 "I"     : "i", \
                 "x"     : "x", \
                 "X"     : "x"}
    for x in myhotkeys.keys():
        g.addHotKey(x)

    # Display window
    while True:
        result = g.run()
        if myhotkeys.has_key(result):
            idx = li.current()
            break

    insScreen.popWindow()
    return (myhotkeys[result], idx)
#------------------------------------------------------------
# def PKGINSTActionWindowCtrl()
#
#    Select install type
#
# Input:
#    insScreen         : screen instance
#    insPKGINSTXmlinfo : xml information
#    insPKGINSTPkginfo : package information
#    iType             : select type (first -1)
#
# Output:
#    int  : select type
#------------------------------------------------------------
def PKGINSTActionWindowCtrl(insScreen, lstSubject, iType):

    type = iType

    while True:
        (hkey, type) = PKGINSTActionWindow(insScreen, lstSubject, type)

        if hkey == "ENTER" or hkey == " ":
            # select/unselect
            return type

        elif hkey == "i":
            # info
            description = lstSubject[type][1]
            subject = lstSubject[type][0]
            PKGINSTTypeInfoWindow(insScreen, subject, description)

        elif hkey == "x":
            # exit
            exit_hkey = HotkeyExitWindow(insScreen)
            if exit_hkey == "y":
                if insScreen != None:
                    StopHotkeyScreen(insScreen)
                    insScreen = None
                sys.exit(0)


#------------------------------------------------------------
# def PKGINSTActionWindow()
#
#   Display action select window.
#
# Input:
#   insScreen  : screen instance
#   lstSubject : install type subject list
#      [ str ]
#        str : subject of each install type
#   iPosition  : current entry position
# Output:
#   str   : pressed hotkey "ENTER", " ", "i", or "x"
#   int   : position
#------------------------------------------------------------
def PKGINSTActionWindow(insScreen, lstSubject, iPosition):

    # Create CheckboxTree instance
    (main_width, main_height) = GetHotKeyMainSize(insScreen)

    if len(lstSubject) > main_height:
        scroll = 1
    else:
        scroll = 0

    li = snack.Listbox(main_height, scroll = scroll, width = main_width)

    idx = 0
    for idx in range(len(lstSubject)):
        str = "%s" % lstSubject[idx][0]
        li.append(str, idx)

    num_subject = len(lstSubject)
    if num_subject > iPosition:
        li.setCurrent(iPosition)
    else:
        li.setCurrent(num_subject - 1)
    # Create Text instance
    t1 = snack.Textbox(main_width, 1, "-" * main_width)
    text = "SPACE/ENTER:select  I:Info  X:eXit"
    t2 = snack.Textbox(main_width, 1, text)

    # Create Grid instance
    g = snack.GridForm(insScreen, "Select your operation", 1, 3)
    g.add(li, 0, 0)
    g.add(t1, 0, 1, (-1, 0, -1, 0))
    g.add(t2, 0, 2, (0, 0, 0, -1))

    myhotkeys = {"ENTER" : "ENTER", \
                 " "     : " ", \
                 "i"     : "i", \
                 "I"     : "i", \
                 "x"     : "x", \
                 "X"     : "x"}
    for x in myhotkeys.keys():
        g.addHotKey(x)

    # Display window
    while True:
        result = g.run()
        if myhotkeys.has_key(result):
            idx = li.current()
            break

    insScreen.popWindow()
    return (myhotkeys[result], idx)


#------------------------------------------------------------
# def PKGINSTPackageInfoWindow()
#
#   Display install package information window.
#
# Input:
#   insScreen            : screen instance
#   pkg               : selected package info list
#     [str, str, str, long, str, str, [str]]
#       str  : name
#       str  : version
#       str  : release
#       long : size
#       str  : licence
#       str  : summary
#       str  : description
# Output:
#   None
#------------------------------------------------------------
def PKGINSTPackageInfoWindow(insScreen, ctrl, pkg):
    # Create Main Text
    (main_width, main_height) = GetHotKeyMainSize(insScreen)
    name     = pkg.name
    ver      = pkg.version
    rel      = "r0"

    for loader in pkg.loaders:
        info = loader.getInfo(pkg)
        summary = info.getSummary()
        if summary:
            summ = summary
#           desc = info.getDescription()
            desc = info.getSource()
            licence = info.getLicense()
            break
    
    for loader in pkg.loaders:
        info = loader.getInfo(pkg)
        if pkg.installed:
            if not loader.getInstalled():
                continue
            size = info.getInstalledSize()
        else:
            size = 0L
            for url in info.getURLs():
                size += info.getSize(url) or 0
        break

    cache = ctrl.getCache()
    filelist = cache.getProvides(pkg.name)
    requires = pkg.requires

    wrapper = textwrap.TextWrapper(width = main_width - 2)

    main_text = []

    main_text.append("Name    : %s\n" % name)
    main_text.append("Version : %s\n" % ver)
    main_text.append("Release : %s\n" % rel)
    main_text.append("Size    : %ld bytes\n" % size)
    main_text.append("Licence : %s\n\n" % licence)

    main_text.append("Summary:\n")
    wrapper.initial_indent    = "  "
    wrapper.subsequent_indent = "  "
    main_text.append(wrapper.fill(summ) + "\n\n")

    main_text.append("Description:\n")
    main_text.append(wrapper.fill(desc) + "\n\n")

    main_text.append("Provides:\n")
    wrapper.initial_indent    = "  "
    wrapper.subsequent_indent = "    "
    if filelist:
        for file in filelist:
            main_text.append(wrapper.fill(file.name) + "\n")
        main_text.append("\n")
########
    main_text.append("Requires:\n")
    wrapper.initial_indent    = "  "
    wrapper.subsequent_indent = "    "
    for pkg_req in requires:
        main_text.append(wrapper.fill(pkg_req.name) + "\n")
    main_text.append("\n")
########

    main_join_text = "".join(main_text)
    del main_text

    # Display information window
    HotkeyInfoWindow(insScreen, "Package information", main_join_text, \
                     main_width, main_height, {"b" : "b", "B" : "b"}, "B:Back")

#------------------------------------------------------------
# def ButtonInfoWindow()
#
#   Display information window for Button mode.
#
# Input:
#   insScreen : screen instance
#   sTitle    : title string
#   sText     : main text
#   iWidth    : width of main text
#   iHeight   : height of main text
#   lstButtons: Button list [button name1, button name2, ...]
# Output:
#   str       : initial character in pressed button name
#------------------------------------------------------------
def ButtonInfoWindow(insScreen, sTitle, sText, iWidth, iHeight, lstButtons):

    # Get line number
    length = len(sText)
    index = 0
    count = 0
    scroll = 0
    while index < length:
        if sText[index] == "\n":
            count += 1
            if count > iHeight:
                scroll = 1
                break
        index += 1

    # Create Text instance
    t1 = snack.Textbox(iWidth - scroll * 2, iHeight, sText, scroll)

    # Create Button instance
    bb = snack.ButtonBar(insScreen, lstButtons)

    # Create Grid instance
    g = snack.GridForm(insScreen, sTitle, 1, 2)
    g.add(t1, 0, 0)
    g.add(bb, 0, 1, (0, 1, 0, -1))

    # Display window
    while True:
        result = bb.buttonPressed(g.run())

        rcode = None
        for x in lstButtons:
            if result == x.lower():
                rcode = x[0].lower()
                break
        if rcode != None:
            break

    insScreen.popWindow()
    return rcode

#------------------------------------------------------------
# def GetButtonMainSize()
#
#   Get best full screen main object size for Button mode
#
# Input:
#   insScreen : screen instance
# Output:
#   int       : width
#   int       : height
#------------------------------------------------------------
def GetButtonMainSize(insScreen):
    (width, height) = GetWindowSize(insScreen)

    width -= 8

    # It is not centered well only by doing -12 when the Height is an Odd.
    # In addition, it is necessary to do 1.
    height -= (12 - (height % 2))

    return (width, height)

def _make_grid_search(insScreen, search_id):

    l = snack.Label("Search Value:")
    l1 = snack.Label(" ")
    e = snack.Entry(30, search_id)
    b = snack.ButtonBar(insScreen,(("Search","search"),("Search off","cancel")))

    g = snack.GridForm(insScreen, "Enter Search String", 3, 6)
    g.add(l, 0, 1)
    g.add(l1,0, 2)
    g.add(e, 0, 3)
    g.add(l1,0, 4)
    g.add(b, 0, 5)

    return e, b, g

def _make_grid_input_path(insScreen, title, label, strText):

    l = snack.Label(label)
    l1 = snack.Label(" ")
    e = snack.Entry(50, strText)
    b = snack.ButtonBar(insScreen,(("   OK   ", "ok"), (" Cancel ", "cancel")))

    g = snack.GridForm(insScreen, title, 3, 6)
    g.add(l, 0, 1)
    g.add(l1,0, 2)
    g.add(e, 0, 3)
    g.add(l1,0, 4)
    g.add(b, 0, 5)

    return e, b, g
#------------------------------------------------------------
# def PKGINSTPathInputWindow()
#
#   Display a window which you can input a path.
#
# Input:
#       title : Title of the window
#       label : A text aim to guide the users operation
# Output:
#   path   : path you have inputed
#------------------------------------------------------------
def PKGINSTPathInputWindow(insScreen, check_dir_exist, title, label,text_prev=""):

    rtn_sts = None

    while rtn_sts == None:
        (e, b, g) = _make_grid_input_path(insScreen, title, label , text_prev)
        r = g.runOnce()
        insScreen.popWindow()
        str = e.value()

        if b.buttonPressed(r) == "ok":
            #  judge if or not the input is correct
            if check_dir_exist :
                if os.path.isdir(str) :
                    rtn_sts=str
                else:
                    buttons = ['  OK  ']
                    (w, h) = GetButtonMainSize(insScreen)
                    rr = ButtonInfoWindow(insScreen, "  Error !  ", "Not a correct path! Input again, please !", \
                                          w, h, buttons)
            else:
                real_path=os.path.realpath(str)
                folder=os.path.split(real_path)
                folder='/'.join(folder[:-1])
                if os.path.isdir(folder):
                    rtn_sts=real_path
                else:
                    buttons = ['  OK  ']
                    (w, h) = GetButtonMainSize(insScreen)
                    rr = ButtonInfoWindow(insScreen, \
                                          "  Error !  ", \
                                          "The path but the last folder must exist. Please check it ! ", \
                                          w, h, buttons)
        else:
            break
        text_prev = str
    return rtn_sts

def PKGINSTPackageSearchWindow(insScreen):

    search_id = ""
    rtn_sts = None

    while rtn_sts == None:

        (e, b, g) = _make_grid_search(insScreen, search_id)
        r = g.runOnce()
        insScreen.popWindow()

        sts = e.value()

        if b.buttonPressed(r) == "search":
            regexp = re.compile(r'^[-\+\*/\:;,.\?_&$#\"\'!()0-9A-Za-z]+$')
            rs = regexp.search(sts)
            if rs != None:
                rtn_sts = sts
            else:
                buttons = ['OK']
                (w, h) = GetButtonMainSize(insScreen)
                rr = ButtonInfoWindow(insScreen, "Error!", "Search Value Invalid!", \
                                  w, h, buttons)
        else:
            break
        search_id = sts

    return rtn_sts

#------------------------------------------------------------
# def PKGTypeSelectWindow()
#
#   Display locale doc and dbg pacakges select window.
#
# Input:
#   pkgTypeList   : package type list 
#     ["locale", "doc", "dbg"]
#      "locale" = True/False : install/not install *-locale/*-localedata package
#      "doc"    = True/False : install/not install doc package 
#      "dbg"    True/False : install/not install dbg package
#      "static"    True/False : install/not install *-staticdev package
#      "ptest"    True/False : install/not install *-ptest package
# Output:
#   pkgTypeList   : select result
#------------------------------------------------------------
def PKGTypeSelectWindow(insScreen, pkgTypeList, position = 0):

    iPosition = position
    # Create CheckboxTree instance
    (main_width, main_height) = GetHotKeyMainSize(insScreen)
    main_height -= 2

    #print " packages = %s" % len(packages)
    if len(pkgTypeList) > main_height:
        scroll = 1
    else:
        scroll = 0

    hotkey_base_text = "SPACE/ENTER:select/unselect  N:Next  B:Back  I:Info  X:eXit"
    wrapper = textwrap.TextWrapper(width = main_width)
    hotkey_text = wrapper.fill(hotkey_base_text)
    if hotkey_text != hotkey_base_text:
        main_height -= 1
        hotkey_line = 2
    else:
        hotkey_line = 1

    li = snack.Listbox(main_height, scroll = scroll, width = main_width)
    idx = 0
    for x in pkgTypeList:
        if x.status:
            status = "*"
        else:
            status = " "
        str = "%s [%s]" % (x.name, status)

        li.append(str, idx)
        idx += 1
    # Set position
    num_type = len(pkgTypeList)
    if num_type > 1:
        if num_type <= iPosition:
            iPosition = num_typr - 1
        if  num_type > (iPosition + main_height / 2):
            before_position = (iPosition + main_height / 2)
        else:
            before_position = num_type - 1
    li.setCurrent(before_position)
    li.setCurrent(iPosition)

    t1 = snack.Textbox(main_width, 1, "-" * main_width)
    t2 = snack.Textbox(main_width, hotkey_line, hotkey_text)

    # Create Grid instance
    title = "Customize special type packages"

    g = snack.GridForm(insScreen, title, 1, 5)
   
    g.add(t1, 0, 2) 
    g.add(t2, 0, 4, (0, 0, 0, -1))
    g.add(li, 0, 0)

############# append test key 'S' ####
    myhotkeys = {"ENTER" : "ENTER", \
                 " "     : " ", \
                 "n"     : "n", \
                 "N"     : "n", \
                 "b"     : "b", \
                 "B"     : "b", \
                 "i"     : "i", \
                 "I"     : "i", \
                 "x"     : "x", \
                 "X"     : "x"}

    for x in myhotkeys.keys():
        g.addHotKey(x)
#####################################
    while True:
        result = g.run()
        idx = li.current()
        if myhotkeys.has_key(result):
            if myhotkeys[result] == "ENTER" or \
               myhotkeys[result] == " ":
                curr_type = pkgTypeList[idx]
                if not curr_type.status:
                    curr_type.status = True
                    newsign = "*"
                else:
                    curr_type.status = False
                    newsign = " "
                item = "%s [%s]" % (curr_type.name, newsign)
                li.replace(item, idx)    
                idx += 1

                if idx >= num_type:
                    idx = num_type - 1
                li.setCurrent(idx)
            else:
                break
    insScreen.popWindow()
    return (myhotkeys[result], idx, pkgTypeList)


def PKGTypeSelectWindowCtrl(insScreen, pkgTypeList):
    idx = 0
    while True:
        (hkey, idx, pkgTypeList) = PKGTypeSelectWindow(insScreen, pkgTypeList, idx)
        if hkey == "i":
            # info
            description = pkgTypeList[idx].description
            subject = pkgTypeList[idx].name
            PKGINSTTypeInfoWindow(insScreen, subject, description)

        elif hkey == "x":
            # exit
            exit_hkey = HotkeyExitWindow(insScreen)
            if exit_hkey == "y":
                if insScreen != None:
                    StopHotkeyScreen(insScreen)
                    insScreen = None
                    sys.exit(0)

        elif hkey == "n":
            return ("n", pkgTypeList)
        elif hkey == "b":
            return ("b", pkgTypeList)

#------------------------------------------------------------
# def PKGINSTPackageWindow()
#
#   Display package select window.
#
# Input:
#   insScreen   : screen instance
#   lstPackage  : package info list
#     [str, str, i]
#      str      : package name
#      str      : package summary
#      i        : select status
#   dispPackage ; disp package info list
#   iPosition   : current entry position
#   lTargetSize : target size
#   lHostSize   : host size
#   search      : search string
#   install_type: INSTALL or REMOVE or UPDATE
# Output:
#   str   : pressed hotkey "r", "f", "c", "n", "b", "d", "s", "i", or "x"
#   int   : position
#   lst   : package info list (updated)
#------------------------------------------------------------
def PKGINSTPackageWindow(insScreen, packages, selected_packages, iPosition, lTargetSize, lHostSize, search, \
                                                                                               install_type):
    installed_pkgs = 0


    # Create CheckboxTree instance
    (main_width, main_height) = GetHotKeyMainSize(insScreen)
    main_height -= 2

    #print " packages = %s" % len(packages)
    if len(packages) > main_height:
        scroll = 1
    else:
        scroll = 0

    hotkey_base_text = "SPACE/ENTER:select/unselect  A:select/unselect All  R:seaRch N:Next  B:Back  I:Info  X:eXit"
    wrapper = textwrap.TextWrapper(width = main_width)
    hotkey_text = wrapper.fill(hotkey_base_text)
    if hotkey_text != hotkey_base_text:
        main_height -= 1
        hotkey_line = 2
    else:
        hotkey_line = 1

    li = snack.Listbox(main_height, scroll = scroll, width = main_width)

    idx = 0
    for x in packages:
        if install_type==ACTION_INSTALL and x.installed :
            status = "I"
            installed_pkgs += 1
        elif x in selected_packages:
            status = "*"
        else:
            status = " "
        str = "[%s] %s " % (status, x.name)

        li.append(str, idx)
        idx += 1
    # Set position
    num_package = len(packages)
    before_position = 0
    if num_package > 1:
        if num_package <= iPosition:
            iPosition = num_package - 1
        if  num_package > (iPosition + main_height / 2):
            before_position = (iPosition + main_height / 2)
        else:
            before_position = num_package - 1
    li.setCurrent(before_position)
    li.setCurrent(iPosition)

    # Create Text instance
    t1 = snack.Textbox(main_width, 1, "-" * main_width)
    text = "All Packages [%ld]    Installed Packages    [%ld] Selected Packages [%ld]" % \
          (num_package, installed_pkgs, len(selected_packages))
    t2 = snack.Textbox(main_width, 1, text)
    t3 = snack.Textbox(main_width, 1, "-" * main_width)
    t4 = snack.Textbox(main_width, hotkey_line, hotkey_text)

    # Create Grid instance
    if search == None:
        title = "Select package"
    else:
        title = "Select package - (%s)" % search

    g = snack.GridForm(insScreen, title, 1, 5)
    g.add(li, 0, 0)
    g.add(t1, 0, 1, (-1, 0, -1, 0))
    g.add(t2, 0, 2)
    g.add(t3, 0, 3, (-1, 0, -1, 0))
    g.add(t4, 0, 4, (0, 0, 0, -1))

############# append test key 'S' ####
    myhotkeys = {"ENTER" : "ENTER", \
                 " "     : " ", \
                 "n"     : "n", \
                 "N"     : "n", \
                 "b"     : "b", \
                 "B"     : "b", \
                 "r"     : "r", \
                 "R"     : "r", \
                 "i"     : "i", \
                 "I"     : "i", \
                 "x"     : "x", \
                 "X"     : "x", \
                 "a"     : "a", \
                 "A"     : "a"}        

    for x in myhotkeys.keys():
        g.addHotKey(x)
#####################################
    while True:
        result = g.run()
        idx = li.current()
        if myhotkeys.has_key(result):
            if myhotkeys[result] == "ENTER" or \
               myhotkeys[result] == " ":
                li = _StatusToggle(li, myhotkeys[result], idx, selected_packages, \
                                                          packages, install_type)
                idx += 1
                if idx >= num_package:
                    idx = num_package - 1
                li.setCurrent(idx)
            elif myhotkeys[result]=="a":        ###
                li = _SelectAll(li, myhotkeys[result],num_package, selected_packages, \
                                                         packages, install_type)
                li.setCurrent(idx)
            else:
                break
    insScreen.popWindow()
    return (myhotkeys[result], idx, selected_packages)

#------------------------------------------------------------
# def PKGINSTDebuginfoWindow()
#
#   Display package select window.
#
# Input:
#   insScreen   : screen instance
#   lstDebugPkg : package info list
#     [str, str, i]
#      str      : package name
#      str      : package summary
#      i        : select status
#   iPosition   : current entry position
#   lTargetSize : target size
#   lHostSize   : host size
# Output:
#   str   : pressed hotkey "c", "n", "b", "i", or "x"
#   int   : position
#   lst   : package info list (updated)
#------------------------------------------------------------
def PKGINSTDebuginfoWindow(insScreen, lstDebugPkg, selected_packages, iPosition, \
                         lTargetSize, lHostSize):
    
    installed_pkgs = 0
    # Create CheckboxTree instance

    (main_width, main_height) = GetHotKeyMainSize(insScreen)
    main_height -= 2

    if len(lstDebugPkg) > main_height:
        scroll = 1
    else:
        scroll = 0

    hotkey_base_text = "SPACE/ENTER:select/unselect  N:Next  B:Back  I:Info  X:eXit"
    wrapper = textwrap.TextWrapper(width = main_width)
    hotkey_text = wrapper.fill(hotkey_base_text)
    if hotkey_text != hotkey_base_text:
        main_height -= 1
        hotkey_line = 2
    else:
        hotkey_line = 1

    li = snack.Listbox(main_height, scroll = scroll, width = main_width)

    idx = 0
    for x in lstDebugPkg:
        if x.installed:
            status = "I"
            installed_pkgs += 1
        elif x in selected_packages:
            status = "*"
        else:
            status = " "
        str = "[%s] %s " % (status, x.name)

        li.append(str, idx)
        idx += 1

    # Set position
    num_package = len(lstDebugPkg)
    if num_package <= iPosition:
        iPosition = num_package - 1
    if  num_package > (iPosition + main_height / 2):
        before_position = (iPosition + main_height / 2)
    else:
        before_position = num_package - 1
    li.setCurrent(before_position)
    li.setCurrent(iPosition)

    # Create Text instance
    t1 = snack.Textbox(main_width, 1, "-" * main_width)
    text = "All Packages [%ld]    Installed Packages    [%ld] Selected Packages [%ld]" % \
          (num_package, installed_pkgs, len(selected_packages))

    t2 = snack.Textbox(main_width, 1, text)
    t3 = snack.Textbox(main_width, 1, "-" * main_width)
    t4 = snack.Textbox(main_width, hotkey_line, hotkey_text)

    # Create Grid instance
    g = snack.GridForm(insScreen, "Select debuginfo packages", 1, 5)
    g.add(li, 0, 0)
    g.add(t1, 0, 1, (-1, 0, -1, 0))
    g.add(t2, 0, 2)
    g.add(t3, 0, 3, (-1, 0, -1, 0))
    g.add(t4, 0, 4, (0, 0, 0, -1))



############# append test key 'S' ####
    myhotkeys = {"ENTER" : "ENTER", \
                 " "     : " ", \
                 "n"     : "n", \
                 "N"     : "n", \
                 "b"     : "b", \
                 "B"     : "b", \
                 "i"     : "i", \
                 "I"     : "i", \
                 "x"     : "x", \
                 "X"     : "x"}
    for x in myhotkeys.keys():
        g.addHotKey(x)
#####################################


    # Display window
    while True:
        result = g.run()
        idx = li.current()
        if myhotkeys.has_key(result):
            if myhotkeys[result] == "ENTER" or \
               myhotkeys[result] == " ":
                li = _StatusToggle(li, myhotkeys[result], idx, selected_packages, lstDebugPkg)
                idx += 1
                if idx >= num_package:
                    idx = num_package - 1
                li.setCurrent(idx)
            else:
                break

    insScreen.popWindow()
    return (myhotkeys[result], idx, selected_packages)

def ConfirmGplv3Window(insScreen, packages):
    if insScreen == None:
        print "error ConfirmGplv3Window: the screen is None"
    # Create CheckboxTree instance
    (main_width, main_height) = GetHotKeyMainSize(insScreen)
    main_height -= 2

    if len(packages) > main_height:
        scroll = 1
    else:
        scroll = 0

    hotkey_base_text = "These GPLv3 packages are depended, do you want to install them? (y/n)"
    wrapper = textwrap.TextWrapper(width = main_width)
    hotkey_text = wrapper.fill(hotkey_base_text)
    if hotkey_text != hotkey_base_text:
        main_height -= 1
        hotkey_line = 2
    else:
        hotkey_line = 1

    li = snack.Listbox(main_height, scroll = scroll, width = main_width)

    idx = 0
    for x in packages:
        li.append(x.name, idx)
        idx += 1

    # Set position
    iPosition=0
    li.setCurrent(iPosition)

    # Create Text instance
    t1 = snack.Textbox(main_width, 1, "-" * main_width)
    t4 = snack.Textbox(main_width, hotkey_line, hotkey_text)

    # Create Grid instance
    title = "GPLv3 that be depended"

    g = snack.GridForm(insScreen, title, 1, 5)
    g.add(li, 0, 0)
    g.add(t1, 0, 1, (-1, 0, -1, 0))
    g.add(t4, 0, 4, (0, 0, 0, -1))

############# append test key 'S' ####
    myhotkeys = {"y"     : "y", \
                 "Y"     : "y", \
                 "n"     : "n", \
                 "N"     : "n"}
    for x in myhotkeys.keys():
        g.addHotKey(x)
#####################################
    result = g.run()
    if myhotkeys.has_key(result):
        if myhotkeys[result] == "y" or \
            myhotkeys[result] == "n":
            insScreen.popWindow()
            return (myhotkeys[result])
