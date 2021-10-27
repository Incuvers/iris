#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#
import logging.config
import glob
import io
import os
import time
from flask import (
    Blueprint, render_template,
    abort,
    send_from_directory,
    send_file,
    request,
)

from app.webserver.log_request import LogRequest
from app.webserver.netplan.netplan_config_creator import NetplanConfig 

bp = Blueprint('system', __name__, url_prefix='/')
ALLOWED_EXTENSIONS = set(['yaml', 'yml'])
_logger = logging.getLogger(__name__)

_log_request = LogRequest()


@bp.route('/network', methods=('GET', 'POST'))
def network():
    # TODO implement issue 318
    return render_template('network.html')

@bp.route('/fetchLogs', methods=('GET', 'POST'))
def fetch_logs():
    logs =  ''
    requested_log = request.form.get('requested_log')
    if  requested_log == 'snap':
        logs = _log_request.get_log(cmd='sudo snap logs iris-incuvers -n 1000', log_type='snap')
    elif requested_log == 'sysctl':
        logs = _log_request.get_log(cmd='systemctl status snap.iris-incuvers.monitor -n 1000', log_type='sysctl')
    elif requested_log == 'syslog':
        logs = _log_request.get_log(cmd='cat /var/log/syslog', log_type='syslog')
    elif requested_log == 'journalctl':
        logs = _log_request.get_log(cmd='journalctl -xe', log_type='journalctl')
    return render_template('log_results.html', logs=logs)


@bp.route('/downloadLogFile', methods=('GET', 'POST'))
def download_logs():
    creation_time = time.strftime('%a %H:%M:%S').replace(" ", "_")
    log_download = request.form.get('output')
    buffer = io.BytesIO()
    encoded_log = str.encode(log_download)
    buffer.write(encoded_log)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     attachment_filename=f'{creation_time} _ {_log_request.get_selected_log()}.txt',
                     mimetype='text/csv')


@bp.route('/advanced', methods=('GET', 'POST'))
def advanced():
    return render_template('advanced_network_settings.html')


@bp.route('/deleteBenchmark', methods=('GET', 'POST'))
def delete_benchmark_image():
    resource_name = request.args.get('selected_file')
    resource_path = os.environ.get('SNAP_COMMON')
    try:
        os.remove(resource_path + '/' + resource_name)
    except OSError:
        _logger.error('Error processing users request to delete a benchmark resource in SNAP COMMON')
        abort(404)
    return render_template('benchmark_tests.html',
                           image_len=len(get_available_benchmark_images()),
                           images=get_available_benchmark_images(),
                           csv_len=len(get_available_benchmark_csv_files()),
                           csv_files=get_available_benchmark_csv_files())


@bp.route('/benchmarkTests', methods=('GET', 'POST'))
def view_benchmark_tests():
    return render_template('benchmark_tests.html',
                           image_len=len(get_available_benchmark_images()),
                           images=get_available_benchmark_images(),
                           csv_len=len(get_available_benchmark_csv_files()),
                           csv_files=get_available_benchmark_csv_files())


@bp.route('/downloadResource', methods=('GET', 'POST'))
def download_selected_file():
    requested_file = request.args.get('selected_file')
    resource_path = os.environ.get('SNAP_COMMON')

    try:
        return send_from_directory(  resource_path + '/' , requested_file, as_attachment=True)
    except FileNotFoundError:
        abort(404)

        
@bp.route('/addNetwork',  methods=('GET', 'POST'))
def create_wifi_connection_from_user_input():
    ssid = request.form.get('ssid_name')
    password = request.form.get('network_password')
    if validate_form_entry(ssid):
        netplan_config = NetplanConfig(ssid.strip(' "\'\t\r\n'), password.strip(' "\'\t\r\n'))
        status, message = netplan_config.create_netplan_config_from_wifi_template()
        if status is True:
            return render_template('network_added.html',
                                   message=message)
        else:
            return render_template('network_credentials_failure.html', error_message=message)

    else:
        return render_template('network_credentials_failure.html', error_message=
                               'Please check your ssid and password for any mistakes')


@bp.route("/uploadNetplan", methods=["GET", "POST"])
def create_connection_from_uploaded_file():
    if request.method == "POST":
        if request.files:
            netplan_file = request.files["netplan"]
            # verify the file is of a legal upload type and the size is less than 800 bytes
            if netplan_file and allowed_file(netplan_file.filename) and get_file_size(netplan_file) < 800:
                netplan_config = NetplanConfig()
                status, message = netplan_config.create_netplan_config_from_upload(netplan_file)
                if status is True:
                    return render_template('network_added.html', message=message)
                else:
                    return render_template('netplan_file_upload_failure.html', error_message=message)

            else:
                return render_template('netplan_file_upload_failure.html',
                                       error_message=
                                       'Please verify your netplan file has the yaml file '
                                       'extension and is less than 800 bytes')


@bp.route('/', methods=('GET', 'POST'))
def welcome():
    return render_template('welcome.html')


def validate_form_entry(ssid: str) -> bool:
    """
    :param ssid: ssid from user input
    :param password: password from user input
    :return: conditional boolean if/not the input fields have characters
    """
    if ssid == '':
        return False
    else:
        return True


def allowed_file(filename: str) -> str:
    """
    :param filename: filename from user input
    :return: boolean if extension is acceptable
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_file_size(uploaded_file) -> int:
    """
    :param uploaded_file: assumed yaml file user has uploaded
    :return: file size
    """
    if uploaded_file.content_length:
        return uploaded_file.content_length
    try:
        pos = uploaded_file.tell()
        uploaded_file.seek(0, 2)  # seek to end
        size = uploaded_file.tell()
        uploaded_file.seek(pos)  # back to original position of file
        return size
    except (AttributeError, IOError):
        pass
    # in-memory file object that doesn't support seeking or tell
    return 0


def get_available_benchmark_images() -> list:
    """
    :return: list of benchmark test images that are active and living in the static directory
    """
    resource_path = os.environ.get('SNAP_COMMON')
    original_benchmark_img_file_path = glob.glob(resource_path + '/*_benchmark.png', recursive=True)
    generated_benchmark_img_files = []
    for available_benchmark in original_benchmark_img_file_path:
        generated_benchmark_img_files.append(available_benchmark.replace(resource_path+'/', ''))
    return generated_benchmark_img_files


def get_available_benchmark_csv_files() -> list:
    """
    :return: list of benchmark test csv that are active and living in the static directory
    """
    resource_path = os.environ.get('SNAP_COMMON')
    original_benchmark_csv_file_path = glob.glob(resource_path + '/*_benchmark.csv', recursive=True)
    generated_benchmark_csv_files = []
    for available_benchmark in original_benchmark_csv_file_path:
        generated_benchmark_csv_files.append(available_benchmark.replace(resource_path+'/', ''))
    return generated_benchmark_csv_files
