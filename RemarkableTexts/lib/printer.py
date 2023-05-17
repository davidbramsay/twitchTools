from thermalprinter import *
from PIL import Image
import emoji

from .addresses import ADDRESS_BOOK

class printController:

    def __init__(self, serialport='/dev/tty.usbserial-1422110'):
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
            if (message.startswith('ATTACHFILE:')):
                try:
                    printer.image(Image.open(message[11:]))
                except:
                    printer.out('attachment that could not be printed.')
            else:
                printer.out(emoji.demojize(message))
            printer.feed(4)


    def printOutgoingText(self, datestring, numstring, message):
        '''commands the thermal printer to print a well-formatted outgoing text'''
        if (message.startswith('ATTACHFILE:') or message=='<Message with no text, but an attachment.>'):
            pass
        else:
            with ThermalPrinter(port=self.serialport, baudrate=19200) as printer:
                printer.out(datestring[-5:] + ' | BACK TO ' + self._getName(numstring), bold=True)
                printer.out(emoji.demojize(message))
                printer.feed(4)
