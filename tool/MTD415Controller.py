from thorlabs_mtd415t import MTD415TDevice
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from time import sleep
from tool.Worker import Worker
import csv
import time
import datetime
import logging

log = logging.getLogger(__name__)


class MTDController(QObject):
    s_data_changed = pyqtSignal(dict)
    s_pid_changed = pyqtSignal(str)

    def __init__(self, port):
        super(MTDController, self).__init__()
        self.mtd = None
        self.port = port
        self.start_connection(self.port)
        self.mtd.clear_errors()
        try:
            if self.mtd.is_open:
                self.mtd.close()
        except Exception:
            pass
        self.baseTemp = self.mtd.temp
        self.setup_thread_routine()
        self.routineValues = {'temp': [25.0, 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7, 25.8, 25.9, 26.0, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1], 'waitTime': 500000}
        self.actualData = {'voltage': {'x':[], 'y':[]}, 'current': {'x':[], 'y':[]}, 'temperature': {'x':[], 'y':[]}}
        self.running = 1
        self.commandRoutineFinished = 0
        self.loop = 0
        self.kwargs = {'v': False, 'c': False, 't': True}

    def set_enabled_loop(self, value):
        self.loop = value

    def save_command(self, value):
        # commandList = list(map(float, (value.split(','))))
        self.routineValues['temp'] = value
        print(self.routineValues['temp'])

    def set_waitTime(self, time_ms):
        self.routineValues['waitTime'] = time_ms

    def current_voltage_temperature_to_csv(self, filepath):
        with open(filepath, 'w') as f:
            fieldnames = ['time', 'voltage', 'current', 'temperature']
            file = csv.DictWriter(f, fieldnames=fieldnames)
            dict = {'time': str(datetime.datetime.now()), 'voltage': str(self.mtd.tec_voltage),
                    'current': str(self.mtd.tec_current), 'temperature': str(self.mtd.temp)}
            file.writerow(dict)

    def setup_thread_routine(self):
        log.info("Thread routine setup")
        self.routineThread = QThread()
        self.routineWorker = Worker(self.start_routine)
        self.routineWorker.moveToThread(self.routineThread)
        self.routineThread.started.connect(self.routineWorker.run)

    def start_thread_routine(self):
        if self.routineThread.isRunning():
            self.commandRoutineFinished = 0
            log.info("thread routine RESTART")
        else:
            self.routineThread.start()
            log.info("thread routine START")

    def clear_data(self):
        self.actualData = {'voltage': {'x':[], 'y':[]}, 'current': {'x':[], 'y':[]}, 'temperature': {'x':[], 'y':[]}}

    def set_pid_parameters(self, P, I, D):
        if self.routineThread.isRunning():
            self.s_pid_changed.emit("Close Reading THread to send PID settings.")
        else:
            try:
                self.mtd.p_gain = P
                self.mtd.d_gain = D
                self.mtd.i_gain = I
                self.s_pid_changed.emit("PID parameters saved. P={}, I={}, D={}".format(P, I, D))
                log.info("PID parameters saved.")
                #self.routineThread.start()
            except Exception as e:
                self.s_pid_changed.emit("PID parameters NOT saved. Error Occured.")
                log.info("PID parameters NOT saved, error occured")

    def launch_read_without_command(self):
        if self.routineThread.isRunning():
            log.info("Routine Thread Already Running")
            self.s_pid_changed.emit("Routine Thread Already Running")
        else:
            log.info("hello1")
            self.commandRoutineFinished = 1
            self.loop = 0
            self.start_thread_routine()
            log.info("hello2")

    def start_routine(self, *args, **kwargs):
        log.info("Starting Read Routine...")
        self.running = 1
        absoluteTime = time.time_ns()

        while self.running:

            # log.debug(str(self.routineFinished), str(self.loop))
            if self.commandRoutineFinished == 0 or self.loop == 1:
                log.info("Starting Command Routine...")
                for i, value in enumerate(self.routineValues['temp']):
                    if self.commandRoutineFinished and self.loop==0:
                        break
                    print(value)
                    log.debug("Sending Command...#{}".format(i))
                    self.mtd.temp_setpoint = float(value)
                    a = time.time_ns()
                    log.debug("Command sent. #{}".format(i))
                    if i == len(self.routineValues['temp'])-1:
                        self.commandRoutineFinished = 1
                        log.info("Command Routine Finished")

                    b = time.time_ns()

                    while b-a <= self.routineValues['waitTime']*1000000:
                        # print(self.routineValues['waitTime']*1000000)
                        c = (b-absoluteTime)/1000000
                        self.send_data_to_plot(**self.kwargs, i=c)
                        b = time.time_ns()

            c = (time.time_ns()-absoluteTime)/1000000
            self.send_data_to_plot(**self.kwargs, i=c)

        self.routineThread.terminate()
        log.info("Reading Routine Stopped")

    def send_data_to_plot(self, i=0.0, *args, **kwargs):
        if kwargs['v']:
            voltage = self.mtd.tec_voltage
            self.actualData['voltage']['x'].append(i)
            self.actualData['voltage']['y'].append(voltage)
        if kwargs['c']:
            current = self.mtd.tec_current
            self.actualData['current']['x'].append(i)
            self.actualData['current']['y'].append(current)
        if kwargs['t']:
            temp = self.mtd.temp
            self.actualData['temperature']['x'].append(i)
            self.actualData['temperature']['y'].append(temp)
        self.s_data_changed.emit(self.actualData)

    def stop_routine(self):
        self.running = 0
        self.routineThread.terminate()

    def stop_command_routine(self):
        self.commandRoutineFinished = 1

    def start_connection(self, port):
        self.mtd = MTD415TDevice(port, auto_save=True)

    def reset_connection(self):
        log.debug("Resetting connection...")
        self.stop_command_routine()
        self.stop_routine()
        self.close_connection()
        self.clear_data()
        self.start_connection(self.port)
        log.debug("Reset successful.")
        self.start_thread_routine()

    def close_connection(self):
        log.debug("Closing Connection")
        self.mtd.close()
        log.debug("Connection closed.")
