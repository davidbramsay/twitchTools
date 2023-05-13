from thermalprinter import *
from PIL import Image
from .addresses import ADDRESS_BOOK

class printController:

    def __init__(self, serialport='/dev/tty.usbserial-14140'):
        self.serialport = serialport


    def _getName(self, numstring):
        '''given a numstring with +12223334444, return name associated if in dictionary (otherwise return string) '''
        try:
            return ADDRESS_BOOK[numstring]
        except:
            return numstring


    def printIncomingText(self, datestring, numstring, message):
        '''commands the thermal printer to print a well-formatted incoming text'''
        with ThermalPrinter(port=self.serialport, baudrate=19200) as printer:
            printer.out(datestring, bold=True, inverse=True)
            printer.out(self._getName(numstring), bold=True)
            printer.out(message)
            printer.feed(4)


    def printOutgoingText(self, datestring, numstring, message):
        '''commands the thermal printer to print a well-formatted outgoing text'''
        with ThermalPrinter(port=self.serialport, baudrate=19200) as printer:
            printer.out(datestring[-5:] + ' | BACK TO ' + self._getName(numstring), bold=True)
            printer.out(message, bold=True, inverse=True)
            printer.feed(4)
