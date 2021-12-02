# -*- coding: utf-8 -*-

from pathlib import Path


class UISettings:
    """
    class that holds the constants for the user interface
    """
    # branding color names
    INCUVERS_BLACK = (0, 0, 0)
    INCUVERS_DARK_GREY = (35, 35, 35)
    INCUVERS_GREY = (51, 51, 51)
    INCUVERS_LIGHT_GREY = (66, 66, 66)
    INCUVERS_BLUE = (0, 193, 243)
    INCUVERS_WHITE = (255, 255, 255)
    INCUVERS_ORANGE = (255, 136, 14)  # FF880E
    INCUVERS_RED = (198, 40, 40)  # C62828
    INCUVERS_GREEN = (0, 158, 115)     # 009E73

    # color roles
    DISABLED_OBJ = (160, 160, 160)
    DISABLED_TEXT = (100, 100, 100)
    MENU_COLOR = INCUVERS_GREY  # incuvers dark grey
    MENU_COLOR_TITLE = INCUVERS_BLUE  # incuvers blue
    COLOR_SELECTED = INCUVERS_BLUE  # incuvers blue
    COLOR_ALARM = INCUVERS_ORANGE

    WIDGET_BACKGROUND = INCUVERS_GREY  # just the background
    PROGRESS_BAR_FILL = INCUVERS_BLUE  # the inside of the progress bar
    TEXT_COLOR = INCUVERS_WHITE  # regular textbox text
    LINK_COLOR = INCUVERS_BLUE  # for links
    HEIGHT = 1024
    WIDTH = 576
    # Sizing ratios
    DEVICE_WIDGET_HEIGHT = 128
    DEVICE_WIDGET_WIDTH = WIDTH
    EXPERIMENT_WIDGET_HEIGHT = 180
    EXPERIMENT_WIDGET_WIDTH = WIDTH
    GAUGE_WIDGET_HEIGHT = 358
    GAUGE_WIDGET_WIDTH = 288
    # loading wheel parameters
    LOAD_CENTER = (170, 262)
    LOAD_SIZE = (23, 23)
    REFRESH_ANGLE = 10
    AVATAR_PADDING = 20
    GAUGE_TEXT_PADDING = 35
    FPS = 60  # refresh rate

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
