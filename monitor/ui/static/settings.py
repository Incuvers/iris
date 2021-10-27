# -*- coding: utf-8 -*-

from pathlib import Path


class UISettings:
    """
    class that holds the constants for the user interface
    """
    # branding color names
    INCUVERS_BLACK = (0, 0, 0)
    INCUVERS_DARK_GREY = (51, 51, 51)
    INCUVERS_LIGHT_GREY = (66, 66, 66)
    INCUVERS_BLUE = (0, 193, 243)
    INCUVERS_WHITE = (255, 255, 255)
    INCUVERS_ORANGE = (255, 136, 14)  # FF880E
    INCUVERS_RED = (198, 40, 40)  # C62828
    INCUVERS_GREEN = (0, 158, 115)     # 009E73

    # color roles
    DISABLED_OBJ = (160, 160, 160)
    DISABLED_TEXT = (100, 100, 100)
    MENU_COLOR = INCUVERS_DARK_GREY  # incuvers dark grey
    MENU_COLOR_TITLE = INCUVERS_BLUE  # incuvers blue
    COLOR_SELECTED = INCUVERS_BLUE  # incuvers blue
    COLOR_ALARM = INCUVERS_ORANGE

    WIDGET_EDGE = INCUVERS_BLACK  # border around widgets
    WIDGET_BACKGROUND = INCUVERS_DARK_GREY  # just the background
    PROGRESS_BAR_FILL = INCUVERS_BLUE  # the inside of the progress bar
    TEXT_COLOR = INCUVERS_WHITE  # regular textbox text
    LINK_COLOR = INCUVERS_BLUE  # for links

    # Sizing ratios
    IW_HEIGHT_RATIO = 0.125  # for 100 px @ 1024
    EW_HEIGHT_RATIO = 0.1758  # for 180 px @ 1024
    GW_HEIGHT_RATIO = 0.36328125  # for 372 px @ 1024
    GW_WIDTH_RATIO = 0.5

    # loading wheel parameters
    LOAD_CENTER = (170, 262)
    LOAD_SIZE = (23, 23)
    REFRESH_ANGLE = 10

    HEIGHT = 1024
    WIDTH = 600
    AVATAR_PADDING = 20
    GAUGE_TEXT_PADDING = 35
    PADDING = 1  # padded frame (or edge) around every widget, x2 between them
    FPS = 60  # frames per second

    FONT_PATH = "{}/fonts/DroidSansFallback.ttf".format(Path(__file__).parent)

    # Incuvers Logo
    LOGO = "{}/img/incuvers-logo.png".format(Path(__file__).parent)
    IRIS = "{}/img/iris.png".format(Path(__file__).parent)
    AVATAR = "{}/img/logo.png".format(Path(__file__).parent)
    AVATAR_MASK = "{}/img/mask.png".format(Path(__file__).parent)
    # Loading Wheel
    LOADING_WHEEL_HI_RES = "{}/img/load_wheel.png".format(Path(__file__).parent)
    LOADING_WHEEL_LOW_RES = "{}/img/load_wheel_low_res.png".format(Path(__file__).parent)

    # Connection status
    STATUS_OFFLINE = "{}/img/status_offline.png".format(Path(__file__).parent)
    STATUS_SYNCING = "{}/img/status_syncing.png".format(Path(__file__).parent)
    STATUS_ONLINE = "{}/img/status_idle.png".format(Path(__file__).parent)

    # System status
    STATUS_ALERT = "{}/img/status_alert.png".format(Path(__file__).parent)
    STATUS_WIFI = "{}/img/status_wifi.png".format(Path(__file__).parent)
    STATUS_WORKING = "WORKING"
    STATUS_OK = "{}/img/status_ok.png".format(Path(__file__).parent)

    # Protocol status
    EXP_PROTOCOL = "{}/img/exp_protocol.png".format(Path(__file__).parent)
    USR_PROTOCOL = "{}/img/usr_protocol.png".format(Path(__file__).parent)
    STATIC_PROTOCOL = "{}/img/static_protocol.png".format(Path(__file__).parent)
