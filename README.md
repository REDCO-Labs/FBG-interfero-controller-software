# FBG-interfero-controller-software
Software that enables the communication with MTD415T temperature controller and can read data real time from an Agilent Oscilloscope. Data manipulation can be made to draw the Fourier Transform of the signal and analyse the data and more.

To get started

1. Install Python 3.7.6 or 3.7.8
2. Download and Install: https://www.ni.com/fr-ca/support/downloads/drivers/download/packaged.ni-visa.329456.html 
3. Download and Install: https://www.keysight.com/en/pd-1985909/io-libraries-suite?nid=-33330.977662&cc=CA&lc=eng
4. Install requirements.txt + "pip install git+git://github.com/nelsond/thorlabs-mtd415t.git"
5. Inside `controlView.py`, set the good port name to COMX: `self.device = MTDController('COM4')`
6. Try to launch the `main.py`

If the application is not running, verufy that this really exists and that it has the same PATH:
`"C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll")`
If visa32.dll is in a different path, you can specify it manually in the `agilentController.py`, with the variable `self.ressourceManager = pyvisa.ResourceManager(PATH)`