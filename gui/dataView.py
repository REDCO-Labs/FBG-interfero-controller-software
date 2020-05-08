from PyQt5.QtWidgets import QWidget, QLineEdit, QSlider
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, QMutex
from pyqtgraph import PlotItem
import os
from PyQt5 import uic
import numpy as np
from tool.agilentController import Agilent1000XController
import logging
from tool.Worker import Worker
import csv
from scipy.signal import *
import math
import threading

log = logging.getLogger(__name__)

dataViewUiPath = os.path.dirname(os.path.realpath(__file__)) + "\\dataViewUi.ui"
Ui_dataView, QtBaseClass = uic.loadUiType(dataViewUiPath)

SIGNAL_PLOT_TOGGLED = "plot.toggled.indicator"


class DataView(QWidget, Ui_dataView):
    SIGNAL_toggled_plot_indicator = "indicator"
    s_messageBar = pyqtSignal(str)
    s_data_ready = pyqtSignal()
    s_data_plot_ready = pyqtSignal(dict)

    def __init__(self, model=None, controller=None):
        super(DataView, self).__init__()
        self.setupUi(self)
        self.visaDevice = Agilent1000XController()
        self.search_devices()
        self.setup_buttons()
        self.connect_buttons()
        self.connect_signals()
        self.create_plots()
        self.initialize_view()
        self.connect_threads()
        
        self.dataArray = [[]]
        self.formattedDataDict = {}

    def search_devices(self):
        deviceList = self.visaDevice.refresh_resource_list()
        self.cb_device.clear()
        self.cb_device.addItems(deviceList)

    def try_device_connection(self):
        try:
            deviceName = self.cb_device.currentText()
            self.visaDevice.change_instrument(deviceName)
            self.s_messageBar.emit("connection to {} succesful".format(deviceName))

        except Exception as e:
            print(e)
            self.s_messageBar.emit(str(e))

    def initialize_view(self):
        pass

    def setup_buttons(self):
        pass

    def connect_buttons(self):
        self.pb_connect.clicked.connect(lambda: self.try_device_connection())
        self.pb_startAcquisition.clicked.connect(lambda: self.start_acquisition_thread())
        self.pb_search.clicked.connect(lambda: self.search_devices())
        self.s_data_ready.connect(lambda: self.data_analysis())
        self.s_data_plot_ready.connect(self.update_graph)

    def connect_threads(self):
        self.acqThread = QThread()
        self.acqWorker = Worker(self.acquisition_routine)
        self.acqWorker.moveToThread(self.acqThread)
        self.acqThread.started.connect(self.acqWorker.run)
        self.acqThread.finished.connect(lambda: self.s_messageBar.emit("acquisitionThread ended."))
        
        self.dataAnalysisThread = QThread()
        self.dataAnalysisWorker = Worker(self.data_analysis_routine)
        self.dataAnalysisWorker.moveToThread(self.dataAnalysisThread)
        self.dataAnalysisThread.started.connect(self.dataAnalysisWorker.run)
        self.dataAnalysisThread.finished.connect(lambda: self.s_messageBar.emit("dataAnalysisThread ended."))

    def start_acquisition_thread(self):
        self.acqThread.start()

    def acquisition_routine(self, *args, **kwargs):
        self.data_acquisition_routine()
        while self.chb_loop.isChecked():
            self.data_acquisition_routine()
        self.acqThread.terminate()

    def data_acquisition_routine(self, *args, **kwargs):
        log.info("Acquisition Begun...")
        self.visaDevice.clear()
        self.visaDevice.setup_acquisition_parameters()
        self.visaDevice.acquisition_start()
        self.visaDevice.save_data_csv()
        with open("waveform_data.csv", 'r') as file:
            reader = csv.reader(file)
            dataArray = []
            for row in reader:
                row = list(map(float, row))
                dataArray.append(row)
        # print(dataArray)
        dataArray = np.array(dataArray)

        # print(dataArray)
        self.dataArray = dataArray
        log.info("Acquisition Ended")
        self.start_data_analysis_thread()

    def start_data_analysis_thread(self, *args, **kwargs):
        self.dataAnalysisThread.start()

    def data_analysis_routine(self, *args, **kwargs):
        log.info("Data Analysis Begun...")
        time = self.dataArray[:, 0] + max(self.dataArray[:,0])
        data = self.dataArray[:, 1] - np.mean(self.dataArray[:, 1])
        # print("time", time)
        # print("data", data)
        phase_data = np.unwrap(np.angle(hilbert(data)))
        # print("phase", phase_data)
        val = phase_data[0]
        counter = 0
        constant = []
        counter_constant = []
        time_constant = []
        value_constant = []

        # print(len(phase_data))

        while counter <= len(phase_data) - 1:
            new_val = np.round(phase_data[counter], 2)
            compareTo = np.round(np.abs(new_val/2*math.pi), 2)
            if compareTo.is_integer():
                constant.append(new_val)
                counter_constant.append(counter)
                time_constant.append(time[counter])
                value_constant.append(data[counter])
                val = new_val

            counter += 1

        # print("Amount of constant phase points:", len(time_constant))
        # print("CONSTANT PHASE INCREMENT DATA:", value_constant)
        ts = np.mean(np.diff(time_constant))
        # print(np.std(np.diff(time_constant)))
        # print(ts)
        fs = 1 / ts
        f = np.linspace(-fs, fs , len(value_constant))
        # freq = np.fft.rfftfreq(len(value_constant), d=1)
        tf = np.fft.fftshift(np.fft.fft((np.fft.fftshift(value_constant))))
        self.formattedDataDict = {'x': f, 'y': 10 * np.log10(np.abs(tf))}
        # print("FormatedData:", formattedDataDict)
        self.s_data_plot_ready.emit(self.formattedDataDict)
        log.info("Data Analysis Ended...")
        self.dataAnalysisThread.terminate()

    def connect_signals(self):
        pass

    def reset_connection(self):
        self.device.reset_connection()
        self.clear_graph()

    def clear_graph(self):
        self.allPlotsDict["plotDataItem"].clear()

    def create_plots(self):
        self.plotDict = {"plotItem": PlotItem(), "plotDataItem": None, "displayed": 1}
        self.pyqtgraphWidget.addItem(self.plotDict["plotItem"])
        self.plotDict["plotDataItem"] = self.plotDict["plotItem"].plot()

    @pyqtSlot(dict)
    def update_graph(self, data):
        self.plotDict["plotDataItem"].setData(**data)
        log.debug("Data confirmed")
