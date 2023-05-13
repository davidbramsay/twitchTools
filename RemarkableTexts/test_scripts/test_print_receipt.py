from thermalprinter import *
from PIL import Image

SERIALPORT = '/dev/tty.usbserial-14140'

def printLogo():
    with ThermalPrinter(port=SERIALPORT, baudrate=19200) as printer:
        printer.feed(1)
        printer.image(Image.open('printer_test_image_2.png'))
        printer.feed(1)

def printText(datestring, number, message):
    with ThermalPrinter(port=SERIALPORT, baudrate=19200) as printer:
        printer.out(datestring, bold=True, inverse=True)
        printer.out(number, bold=True)
        printer.out(message)
        printer.feed(4)

def printTitle(title):
    with ThermalPrinter(port=SERIALPORT, baudrate=19200) as printer:
        printer.feed(1)
        printer.out(title, double_height=True)
        printer.feed(1)


if __name__ == '__main__':
    printTitle('Test Print for Texts')
    #printLogo()
    printText('12/23/23 08:15', '+17035551234', 'This is a very long test text message to make sure texts are printing well and working properly.  We need to make sure it wraps just fine when its received.')
    printText('12/24/23 14:15', '+17035551234', 'We are now responding to that long text message from before.  Hooray!')
