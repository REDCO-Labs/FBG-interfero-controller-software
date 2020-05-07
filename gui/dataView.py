from PyQt5.QtWidgets import QWidget, QLineEdit, QSlider
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, QMutex
from pyqtgraph import PlotItem
import os
from PyQt5 import uic
import numpy as np
from tool.agilentController import Agilent1000XController
import logging
from tool.Worker import Worker
import pandas as pd
import csv
import math
import threading

log = logging.getLogger(__name__)

dataViewUiPath = os.path.dirname(os.path.realpath(__file__)) + "\\dataViewUi.ui"
Ui_dataView, QtBaseClass = uic.loadUiType(dataViewUiPath)

SIGNAL_PLOT_TOGGLED = "plot.toggled.indicator"


class DataView(QWidget, Ui_dataView):
    SIGNAL_toggled_plot_indicator = "indicator"
    s_messageBar = pyqtSignal(str)

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

    def start_acquisition_thread(self):
        self.acqThread = QThread()
        self.acqWorker = Worker(self.acquisition_routine)
        self.acqWorker.moveToThread(self.acqThread)
        self.acqThread.started.connect(self.acqWorker.run)
        self.acqThread.finished.connect(lambda:self.s_messageBar.emit("acquisitionThread ended."))
        self.acqThread.start()

    def acquisition_routine(self, *args, **kwargs):
        self.data_routine()
        while self.chb_loop.isChecked():
            self.data_routine()
        self.acqThread.terminate()

    def data_routine(self, *args, **kwargs):
        self.visaDevice.clear()
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
        formattedDataDict = {'x': dataArray[:, 0], 'y': dataArray[:, 1]}
        print(formattedDataDict)
        self.update_graph(formattedDataDict)



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
