import string
import time
import sys
import array
import pyvisa
import struct
import os

class Agilent1000XController:

    def __init__(self):
        self.ressourceManager = pyvisa.ResourceManager(
            "C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll")
        try:
            print(1)
            ressourcePath = os.path.dirname(os.path.realpath(__file__)) + "\\visa32.dll"
            print(2)
            self.ressourceManager = pyvisa.ResourceManager("C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll")
            print(3)
            print(self.ressourceManager)
            self.ressourcesList = self.ressourceManager.list_resources()
        except Exception as e:
            print(e, ":: the ressource manager couldn't find the visa32.dll . Specify the path manually.")

        self.acquisitionParameters = {"timebaseScale": 0.1, "timebasePosition": 0.0, "channel1Scale": 0.2, "channel2Scale": 0.2,
                                   "channel1Offset": 0.750, "channel2Offset": 0.0,
                                   "triggerMode": "EDGE", "triggerSource": "SOURCe CHANnel1",
                                   "triggerSlope": "POS", "triggerLevel": 0.8, "acquisitionType": "NORMAL", "timeout":10000}
        self.savingParameters = {}

        if self.ressourcesList:
            try:
                self.instrumentObject = self.ressourceManager.open_resource(self.ressourcesList[0])
                print("Connection successful to device :: {}".format(self.instrumentObject.resource_name))
                self.instrumentObject.timeout = self.acquisitionParameters["timeout"]
                self.instrumentObject.term_chars = r'\n'
                self.setup_acquisition_parameters()

            except Exception as e:
                print(e, ":: The connection couldn't occur. Please procceed manually.")
                self.instrumentObject = None
        else:
            self.instrumentObject = None

    def reset_connection(self):
        if self.instrumentObject is not None:
            self.instrumentObject.close()
        if self.ressourcesList:
            try:
                self.instrumentObject = self.ressourceManager.open_resource(self.ressourcesList[0])
                print("Connection successful to device :: {}".format(self.instrumentObject.resource_name))
                self.instrumentObject.timeout = self.acquisitionParameters["timeout"]
                self.instrumentObject.term_chars = r'\n'
            except Exception as e:
                print(e, ":: The connection couldn't occur. Please procceed manually.")
        else:
            self.instrumentObject = None

    def refresh_resource_list(self):
        self.ressourcesList = self.ressourceManager.list_resources()
        print("Resources List: {}".format(self.ressourcesList))
        return self.ressourcesList

    def change_instrument(self, visaAdress):
        if self.instrumentObject is not None:
            self.instrumentObject.close()
            self.instrumentObject = self.ressourceManager.open_resource(visaAdress)
        else:
            self.instrumentObject = self.ressourceManager.open_resource(visaAdress)

    def clear(self):
        self.send_command("*CLS")
        self.send_command("*RST")

    def terminate_session(self):
        self.instrumentObject.close()

    def verify_intrinsect(self):
        if (int(self.acquisitionParameters["timebaseScale"]) * 10 * 1000 >= int(self.acquisitionParameters["timeout"])):
            self.acquisitionParameters["timeout"] = self.acquisitionParameters["timebaseScale"] * 10 * 1000 * 2
            self.instrumentObject.timeout = self.acquisitionParameters["timeout"]

    def acquisition_get_parameters(self):
        pass

    def acquisition_set_parameters(self, Vdiv=None, tDiv = None, trigLvl = None, trigEdgeSide = None, channel1Scale=1, channel2Scale=1):
        pass

    def setup_acquisition_parameters(self):
        self.verify_intrinsect()
        self.send_command(":TIMebase:SCALe {}".format(self.acquisitionParameters["timebaseScale"]))
        self.send_command(":TIMebase:POSition {}".format(self.acquisitionParameters["timebasePosition"]))

        self.send_command(":TRIGger:MODE {}".format(self.acquisitionParameters["triggerMode"]))
        self.send_command(":TRIGger:EDGE:SLOPe {}".format(self.acquisitionParameters["triggerSlope"]))
        self.send_command(":TRIGger:EDGE:LEVel {}".format(self.acquisitionParameters["triggerLevel"]))
        self.send_command(":ACQuire:TYPE {}".format(self.acquisitionParameters["acquisitionType"]))
        self.send_command(":CHANnel1:OFFSet {}".format(self.acquisitionParameters["channel1Offset"]))
        self.send_command(":CHANnel2:OFFSet {}".format(self.acquisitionParameters["channel2Offset"]))
        self.send_command(":CHANnel1:SCALe {}".format(self.acquisitionParameters["channel1Scale"]))
        self.send_command(":CHANnel2:SCALe {}".format(self.acquisitionParameters["channel2Scale"]))

    def acquisition_start(self, * args, **kwargs):
        self.send_command(":DIGitize CHANnel1")

    def setup_save_parameters(self):
        self.send_command(":WAVeform:POINts:MODE RAW")
        qresult = self.send_query(":WAVeform:POINts:MODE?")
        print("Waveform points mode: %s" % qresult)
        # Get the number of waveform points available.
        self.send_command(":WAVeform:POINts 10240")
        qresult = self.send_query(":WAVeform:POINts?")
        print("Waveform points available: %s" % qresult)
        # Set the waveform source.
        self.send_command(":WAVeform:SOURce CHANnel1")
        qresult = self.send_query(":WAVeform:SOURce?")
        print("Waveform source: %s" % qresult)
        # Choose the format of the data returned:
        self.send_command(":WAVeform:FORMat BYTE")
        print("Waveform format: %s" % self.send_query(":WAVeform:FORMat?"))

    def save_scope_image(self):
        self.send_command(":HARDcopy:INKSaver OFF")
        image_bytes = self.send_query(":DISPlay:DATA? PNG, COLor")
        nLength = len(image_bytes)
        f = open("c:\scope\data\screen.png", "wb")
        f.write(bytearray(image_bytes))
        f.close()
        print("Screen image written to c:\scope\data\screen.png.")

    def save_measures(self):
        self.send_command(":MEASure:SOURce CHANnel1")
        qresult = self.send_query(":MEASure:SOURce?")
        print("Measure source: %s" % qresult)
        self.send_command(":MEASure:FREQuency")
        qresult = self.send_query(":MEASure:FREQuency?")
        print("Measured frequency on channel 1: %s" % qresult)
        self.send_command(":MEASure:VAMPlitude")
        qresult = self.send_query(":MEASure:VAMPlitude?")
        print("Measured vertical amplitude on channel 1: %s" % qresult)

    def save_data_csv(self):
        # Get numeric values for later calculations.
        x_increment = self.instrumentObject.query_ascii_values(":WAVeform:XINCrement?")
        x_origin =  self.instrumentObject.query_ascii_values(":WAVeform:XORigin?")
        y_increment =  self.instrumentObject.query_ascii_values(":WAVeform:YINCrement?")
        y_origin =  self.instrumentObject.query_ascii_values(":WAVeform:YORigin?")
        y_reference =  self.instrumentObject.query_ascii_values(":WAVeform:YREFerence?")
        # Get the waveform data.
        self.instrumentObject.write(":WAVeform:DATA?")
        sData = self.instrumentObject.read_bytes(50000)
        print(sData)
        # sData = self.get_definite_length_block_data(sData)
        # Unpack unsigned byte data.
        values = struct.unpack("%dB" % len(sData), sData)
        print("Number of data values: %d" % len(values))
        # Save waveform data values to CSV file.
        f = open("waveform_data.csv", "w")
        for i in range(0, len(values) - 1):
            time_val = x_origin[0] + (i * x_increment[0])
            #print(values[i], y_reference, y_increment, y_origin)
            voltage = ((values[i] - y_reference[0]) * y_increment[0]) + y_origin[0]
            f.write("%E, %f\n" % (time_val, voltage))
        f.close()
        print("Waveform format BYTE data written to waveform_data.csv.")

    def get_definite_length_block_data(self, sBlock):
        # First character should be "#".
        pound = sBlock[0:1]
        if pound != "#":
            print("PROBLEM: Invalid binary block format, pound char is '%s'." % pound)
            print("Exited because of problem.")
            sys.exit(1)
        # Second character is number of following digits for length value.
        digits = sBlock[1:2]
        # Get the data out of the block and return it.
        sData = sBlock[int(digits) + 2:]
        return sData

    def send_command(self, command):
        self.instrumentObject.write(command)
        self.check_instrument_errors(command)

    def send_query(self, query):
        response = self.instrumentObject.query(query)
        self.check_instrument_errors(query)
        return response

    def send_query_string(self, query):
        response = self.instrumentObject.query(query)
        self.check_instrument_errors(query)
        return response

    def check_instrument_errors(self, command):
        error_string = self.instrumentObject.query(":SYSTem:ERRor?")
        if error_string: # If there is an error string value.
            if error_string.find("+0,", 0, 3) == -1: # Not "No error".
                print ("ERROR: %s, command: '%s'" % (error_string, command))
                print ("Exited because of error.")
                sys.exit(1)
        else: # :SYSTem:ERRor? should always return string.
            print ("ERROR: :SYSTem:ERRor? returned nothing, command: '%s'" % command)
            print ("Exited because of error.")
            sys.exit(1)

    def save_capture_parameters(self):
        # Save oscilloscope setup.
        setup_bytes = self.send_query(":SYSTem:SETup?")
        nLength = len(setup_bytes)
        f = open("../07-control_code/agilent_edux100g/tempSteupFile.txt", "wb")
        f.write(bytearray(setup_bytes))
        f.close()
        print("Setup bytes saved: %d" % nLength)

    def setup_capture_from_file(self, filePath):
        f = open(filePath, "rb")
        setup_bytes = f.read()
        f.close()
        self.send_command(":SYSTem:SETup", array.array('B', setup_bytes))
        print("Setup bytes restored: %d" % len(setup_bytes))


# =========================================================

if __name__ == "__main__":
    scope = Agilent1000XController()
    # scope.reset_connection()
    scope.clear()
    scope.setup_acquisition_parameters()

    scope.acquisition_start()

    scope.save_data_csv()
    scope.terminate_session()
