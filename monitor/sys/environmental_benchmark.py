# -*- coding: utf-8 -*-
"""
Environment Benchmarks
======================

Environment benchmarks for QA and system diagnostics.
It is intended to be used on the live system and not ran locally approx. 840 rows created per hour.

Dependancies
------------
```
import time
import numpy as np
import logging
from PIL import Image
from datetime import datetime
from datetime import timedelta
from matplotlib import pyplot as plt
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.environment.context_manager import ContextManager
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import time
import numpy as np
import logging
from PIL import Image
from datetime import datetime
from datetime import timedelta
from matplotlib import pyplot as plt
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.context_manager import ContextManager
from monitor.environment.thread_manager import ThreadManager as tm


class EnvironmentBenchmark:

    # the time to wait between sending commands to the arduino
    COMMAND_DIGEST_TIME = 10  # in seconds
    DURATION_HOURS = 2  # in hours

    def __init__(self):
        """
        :param event_handler: event handler object
        """
        self._logger = logging.getLogger(__name__)
        # self.event_handler = event_handler
        self.filename = None
        self.sensorframe = {}
        self.test_in_progress = False
        self.y_axis_label = ''
        self.progress_label = ''
        self.progress_sublabel = ''
        self.setpoint_idx = 0
        self.actual_idx = 0
        self.benchmark_start_time = datetime.now()  # this will be redefined later...

        self._marker_color = np.array(uis.INCUVERS_WHITE) / 255.  # this will change

        # these are to be plotted
        self.series = []

        # self.event_handler.register(events.SENSORFRAME_UPDATED, callback=self.sensorframe_reading)
        # self.event_handler.register(events.BENCHMARK_TEST_REQUESTED,
        #                             callback=self.start_benchmark_test)

    def sensorframe_reading(self, sensorframe: dict):
        """
        :param sensorframe: sensorframe from arduino
        :return:
        """
        self.sensorframe = sensorframe

    def start_benchmark_test(self, benchmark_test_type: str):
        """ Start benchmark test
        This methods starts a test thread
        """
        self._logger.info('%s Starting', benchmark_test_type)
        if self.test_in_progress is False:
            creation_time = time.strftime('%a %H:%M:%S').replace(" ", "_")
            self.filename = f"{creation_time}_{benchmark_test_type}_benchmark"
            self.series = []
            if benchmark_test_type == 'TEMP' and not self.test_in_progress:
                self.test_type = 'Temperature Benchmark'
                self.y_axis_label = 'Temperature (°C)'
                self.actual_idx = 1
                self.setpoint_idx = 4
                self._marker_color = np.array(uis.INCUVERS_ORANGE) / 255.
                self.run_temp()
            elif benchmark_test_type == 'CO2' and not self.test_in_progress:
                self.test_type = 'CO\u2082 Benchmark'
                self.y_axis_label = 'CO\u2082 concentration (%)'
                self.actual_idx = 2
                self.setpoint_idx = 5
                self._marker_color = np.array(uis.INCUVERS_GREEN) / 255.
                self.run_co2()
            elif benchmark_test_type == 'O2' and not self.test_in_progress:
                self.test_type = 'O\u2082 Benchmark'
                self.y_axis_label = 'O\u2082 concentration (%)'
                self._marker_color = np.array(uis.INCUVERS_BLUE) / 255.
                self.actual_idx = 3
                self.setpoint_idx = 6
                self.run_o2()
            elif benchmark_test_type == 'FULL' and not self.test_in_progress:
                self._logger.info('Full benchmark Starting')
                self.run_full()
            else:
                self._logger.error(
                    'Invalid input %s unable to run benchmark test', benchmark_test_type)
                return

    @tm.threaded(daemon=True)
    def run_temp(self, duration=None) -> None:
        """
        :param duration: duration of test execution:
        """
        # zero/disable everything
        self.progress_label = 'Normalizing...'
        self._zero_all_setpoints()

        self.benchmark_start_time = datetime.now()
        # warmup for 15 minutes
        self.progress_label = 'Running Phase I...'
        self.progress_sublabel = '0'
        self.run_test_phase({'TP': 37.5}, duration=self.DURATION_HOURS * 0.125)  # 15 min

        self.progress_label = 'Running Phase II...'
        self.progress_sublabel = '0'
        self.run_test_phase({'TP': 37.5}, duration=self.DURATION_HOURS)  # 2 hours

        self.progress_label = 'Running Phase III...'
        self.progress_sublabel = '0'
        self.run_test_phase({'TP': 25.00}, duration=self.DURATION_HOURS * .5)  # 1 hour

        self.progress_label = 'Benchark Complete!'
        self.progress_sublabel = ''
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)

        self.test_in_progress = False
        # self.event_handler.trigger(events.BENCHMARK_TEST_COMPLETED)
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg="Test Complete!")
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        self._logger.info("%s benchmark test has completed and data available in \
            the resources folder", self.test_type)
        self.save_data_as_csv()
        self.save_plot()

    @tm.threaded(daemon=True)
    def run_co2(self):
        """
        :param duration: duration of test execution:
        """
        # zero/disable everything
        self.progress_label = 'Normalizing...'
        self._zero_all_setpoints()

        self.benchmark_start_time = datetime.now()
        # warmup for 15 minutes
        self.progress_label = 'Running Phase I...'
        self.progress_sublabel = '0'
        self.run_test_phase({'CP': 5.00}, duration=self.DURATION_HOURS * 0.125)

        self.progress_label = 'Running Phase II...'
        self.progress_sublabel = '0'
        self.run_test_phase({'CP': 5.00}, duration=self.DURATION_HOURS)

        self.progress_label = 'Running Phase III...'
        self.progress_sublabel = '0'
        self.run_test_phase({'CP': 0.10}, duration=self.DURATION_HOURS * .5)

        self.progress_label = 'Benchark Complete!'
        self.progress_sublabel = ''
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)

        self.test_in_progress = False
        # self.event_handler.trigger(events.BENCHMARK_TEST_COMPLETED)
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg="Test Complete!")
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        self._logger.info("%s benchmark test has completed and data available in \
            the resources folder", self.test_type)
        self.save_data_as_csv()
        self.save_plot()

    @tm.threaded(daemon=True)
    def run_o2(self):
        """
        :param duration: duration of test execution:
        """
        # zero/disable everything
        self.progress_label = 'Normalizing...'
        self._zero_all_setpoints()

        self.benchmark_start_time = datetime.now()
        # warmup for 15 minutes
        self.progress_label = 'Running Phase I...'
        self.progress_sublabel = '0'
        self.run_test_phase({'OP': 5.00}, duration=self.DURATION_HOURS * 0.125)

        self.progress_label = 'Running Phase II...'
        self.progress_sublabel = '0'
        self.run_test_phase({'OP': 5.00}, duration=self.DURATION_HOURS)

        self.progress_label = 'Running Phase III...'
        self.progress_sublabel = '0'
        self.run_test_phase({'OP': 21.00}, duration=self.DURATION_HOURS * .5)

        self.progress_label = 'Benchark Complete!'
        self.progress_sublabel = ''
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)

        self.test_in_progress = False
        # self.event_handler.trigger(events.BENCHMARK_TEST_COMPLETED)
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg="Test Complete!")
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        self._logger.info("%s benchmark test has completed and data available in \
            the resources folder", self.test_type)
        self.save_data_as_csv()
        self.save_plot()

    @tm.threaded(daemon=True)
    def run_full(self):
        """
        :param duration: duration of test execution
        """
        self.test_type = 'Full'
        # TODO: run the test

    def log_remaining_time(self, start_time, end_time):
        """
        :param start_time: start time of opertion
        :param end_time: end time of operation

        this function is intended to communicate elapsed time in a simplistic manner
        """
        elapsed = datetime.now() - start_time
        total = end_time - start_time
        self.progress_sublabel = str(int(100 * elapsed.total_seconds() / total.total_seconds()))
        self._logger.info(f'Current benchmark phase: {(total-elapsed).total_seconds()} s remaining')

    def _zero_all_setpoints(self):
        """ Zeros all setpoints
        This is to make sure all controllers are OFF
        """
        # zero everything
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        # self.event_handler.trigger(events.SETPOINT_UPDATED, 'OP', 21.00)
        self.progress_label = "Turning off O\u2082 (set 20.99%)"
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        time.sleep(self.COMMAND_DIGEST_TIME)
        # self.event_handler.trigger(events.SETPOINT_UPDATED, 'CP', 0.10)
        self.progress_label = "Turning off CO\u2082 (set 0.11%)"
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        time.sleep(self.COMMAND_DIGEST_TIME)
        # self.event_handler.trigger(events.SETPOINT_UPDATED, 'TP', 25.00)
        self.progress_label = "Turning off Temp. (set 25.00°C)"
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        time.sleep(self.COMMAND_DIGEST_TIME)

    def run_test_phase(self, setpoints, duration):
        """
        :param setpoints: sensorframe setpoints
        :param duration: time (in hours) for the test
        this method is responsible for keeping track of time but also
        collects the setpoints in a list
        """
        self._logger.info("Running %s benchmark test phase", self.test_type)
        # self.event_handler.trigger(events.SYSTEM_STATUS_UPDATED, msg=self.progress_label)
        # self.event_handler.trigger(events.LOAD_SET, True)
        # self.event_handler.trigger(events.LOAD_SET, False)
        test_phase_start_time = datetime.now()
        for key, value in setpoints.items():
            # self.event_handler.trigger(events.SETPOINT_UPDATED, key, value)
            time.sleep(self.COMMAND_DIGEST_TIME)
        end_time = test_phase_start_time + timedelta(hours=duration)
        while True:
            now_time = datetime.now()
            if now_time < end_time:
                timestamp = (now_time - self.benchmark_start_time).total_seconds() / 60.
                environmental_snapshot = [
                    timestamp,  # in minutes
                    self.sensorframe.get('TC', 0),
                    self.sensorframe.get('CC', 0),
                    self.sensorframe.get('OC', 0),
                    self.sensorframe.get('TP', 0),
                    self.sensorframe.get('CP', 0),
                    self.sensorframe.get('OP', 0)
                ]
                self.series.append(environmental_snapshot)
                self.log_remaining_time(test_phase_start_time, end_time)
                # self.event_handler.trigger(
                #     accessed_type=events.SYSTEM_STATUS_UPDATED,
                #     msg=str(self.progress_label + " " + self.progress_sublabel + "%")
                # )
                _ = self.update_plot()
                # self.event_handler.trigger(events.BENCHMARK_IMAGE_GENERATED, plt_img)

                # self.event_handler.trigger(events.LOAD_SET, True)
                # self.event_handler.trigger(events.LOAD_SET, False)
                time.sleep(5)
                continue
            else:
                break
        self._logger.warning("%s test phase completed.", self.test_type)

    def save_data_as_csv(self):
        """
        :param series: numpy array that includes the collection of environmental snapshots taken 
        from the incubator
        """
        series = np.asarray(self.series)
        with ContextManager() as context:
            # append extension to filename
            with open(context.get_env('COMMON') + f'/{self.filename}.csv', 'w') as fp:
                np.savetxt(fp, series,
                           header='Time (minutes), TC, CC, OC, TP, CP, OP',
                           delimiter=',')

    def save_plot(self):
        """
        load the csv and plot the results
        """

        plot_img = self.update_plot()
        img = Image.fromarray(plot_img)
        with ContextManager() as context:
            fname = f"{context.get_env('COMMON')}/{self.filename}.png"
        img.save(fname, format='png', lossless=False)

    def update_plot(self):
        """
        update plot with current results
        Triggers "BENCHMARK_IMAGE_GENERATED"
        """
        plt.rcParams.update({
            "lines.color": np.array(uis.INCUVERS_WHITE) / 255.,
            "patch.edgecolor": np.array(uis.INCUVERS_DARK_GREY) / 255.,
            "text.color": np.array(uis.INCUVERS_WHITE) / 255.,
            "axes.facecolor": np.array(uis.INCUVERS_LIGHT_GREY) / 255.,
            "axes.edgecolor": np.array(uis.INCUVERS_WHITE) / 255.,
            "axes.labelcolor": np.array(uis.INCUVERS_WHITE) / 255.,
            "xtick.color": np.array(uis.INCUVERS_WHITE) / 255.,
            "ytick.color": np.array(uis.INCUVERS_WHITE) / 255.,
            "grid.color": np.array(uis.INCUVERS_DARK_GREY) / 255.,
            "figure.facecolor": np.array(uis.INCUVERS_LIGHT_GREY) / 255.,
            "figure.edgecolor": np.array(uis.INCUVERS_DARK_GREY) / 255.,
            "savefig.facecolor": np.array(uis.INCUVERS_LIGHT_GREY) / 255.,
            "savefig.edgecolor": np.array(uis.INCUVERS_DARK_GREY) / 255.
        })
        dpi = 120
        fig = plt.figure(figsize=(uis.WIDTH / dpi,
                         uis.WIDTH / dpi), dpi=dpi)
        ax = fig.add_subplot(111)
        fig.suptitle(self.test_type)
        ax.set_xlabel('Elapsed Time (min)')
        ax.set_ylabel(self.y_axis_label)
        data_to_plot = np.array(self.series)

        ax.plot(data_to_plot[:, 0], data_to_plot[:, self.actual_idx],
                color=self._marker_color, marker='o', ls='', label='actual')
        ax.plot(data_to_plot[:, 0], data_to_plot[:, self.setpoint_idx],
                color=np.array(uis.INCUVERS_WHITE) / 255., marker='', ls='--', label='setpoint')

        ax.axvline(x=self.DURATION_HOURS * 0.125 * 60, linewidth=1,
                   linestyle=':', color=self._marker_color)
        ax.axvline(x=self.DURATION_HOURS * 1.125 * 60, linewidth=1,
                   linestyle=':', color=self._marker_color)

        ax.grid(True)
        ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2),
                  loc="lower left",
                  mode="expand",
                  borderaxespad=0,
                  ncol=4)
        ax.set_xlim([0, self.DURATION_HOURS * 1.625 * 60])
        fig.canvas.draw()
        plot_as_img_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        plot_as_img_array = plot_as_img_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        fig.clf()
        plt.close(fig)
        return plot_as_img_array
