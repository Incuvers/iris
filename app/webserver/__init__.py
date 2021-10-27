#!/usr/bin/python3
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#
from dominate import tags
from flask import Flask
from flask_nav import Nav
from flask_bootstrap import Bootstrap
from flask_nav.elements import View
from .nav import ExtendedNavbar, CustomBootstrapRenderer

from . import arduino
from . import system

nav = Nav()
nav.register_element(
    'frontend_top',
    ExtendedNavbar(
        title=tags.img(src="static/logo_nav.png", height="25", alt="Incuvers"),
        root_class='navbar navbar-inverse',
        items=(
            View('Home', 'system.welcome'),
            View('Details', 'arduino.details'),
            View('Network', 'system.network'),
            View('Advanced', 'system.advanced'),
            View('Benchmark Tests', 'system.view_benchmark_tests'),
            View('System Logs', 'system.fetch_logs'),
        )
    )
)

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    Bootstrap(app)
    nav.init_app(app)

    with app.app_context():
        app.extensions['nav_renderers'][None] = CustomBootstrapRenderer
        app.register_blueprint(system.bp)
        app.register_blueprint(arduino.bp)
        return app
