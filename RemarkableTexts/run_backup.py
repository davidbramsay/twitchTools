from imessage_reader import fetch_data
from thermalprinter import *
from PIL import Image
from datetime import datetime
from os.path import expanduser, getmtime
from fpdf import FPDF
import time
import addresses

DEBUG = True

# The path to the iMessage database
DB_PATH = expanduser("~") + "/Library/Messages/chat.db-wal"

# The port for the USB printer
SERIALPORT = '/dev/tty.usbserial-14140'


def lookupName(numstring):
    ''' return contact name if in addressbook, otherwise number '''
    try:
        return addresses.ADDRESS_BOOK[numstring]
    except:
        return numstring


## SERIAL PRINTER COMMANDS
def printIncomingText(datestring, name, message):
    '''commands the thermal printer to print a well-formatted incoming text'''
    with ThermalPrinter(port=SERIALPORT, baudrate=19200) as printer:
        printer.out(datestring, bold=True, inverse=True)
        printer.out(name, bold=True)
        printer.out(message)
        printer.feed(4)

def printOutgoingText(datestring, name, message):
    '''commands the thermal printer to print a well-formatted outgoing text'''
    with ThermalPrinter(port=SERIALPORT, baudrate=19200) as printer:
        printer.out(datestring[-5:] + ' | BACK TO ' + name, bold=True)
        printer.out(message, bold=True, inverse=True)
        printer.feed(4)


## PDF GENERATION
def generatePDF(name, message):
    ''' generates a pdf for an incoming message and returns its path '''
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("CMU", '', "cmuntb.ttf", uni=True)
    pdf.set_font("CMU", size = 12)

    #cut message off after 1100 characters
    message = message[-1100:]

    pdf.cell(200, 10, txt = 'From: ' + name, ln = 1, align = 'L')
    pdf.multi_cell(180, 5, txt = message, align = 'L')
 
    #draw line below which we will write
    pdf.line(70, 100, 210-70, 100)

    #draw lines for writing
    for i in range(0,10):
        pdf.line(10, 125+i*17, 200, 125+i*17)

    # save the pdf with name .pdf
    filename = "new_texts_pdf/" + name + ".pdf"
    pdf.output(filename)  

    return filename


def handleIncomingMessage(date, numstring, text):
    #print it
    printIncomingText(date, lookupName(numstring), text)
    #generate pdf
    generatePDF(lookupName(numstring), text)



def handleOutgoingMessage(date, numstring, text):
    #print it
    printOutgoingText(date, lookupName(numstring), text)






def handleTexts(cutoff_time):
    ''' pull all new texts (after cutoff_time) and send them to appropriate text handlers '''

    #grab texts (user id, message, date, service, account, is_from_me)
    fd = fetch_data.FetchData()
    messages = fd.get_messages()

    #sort by converted timestamp strings to datetime
    messages = sorted(messages, key=lambda tup: datetime.strptime(tup[2], '%Y-%m-%d %H:%M:%S'))

    #get only messages updated since change
    index = 0
    while(datetime.strptime(messages[index-1][2], '%Y-%m-%d %H:%M:%S') > cutoff_time):
        index -= 1

    if DEBUG:
        print('New Text Count = ' + str(-1*index))
        print('Earliest New Text Time = ' + datetime.strptime(messages[index][2], '%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y, %H:%M:%S"))    

    new_messages = messages[index:]    
    
    #do something with messages
    for m in new_messages:
        if m[5]:
            handleOutgoingMessage(m[2][:-3], m[0], m[1])
        else:
            handleIncomingMessage(m[2][:-3], m[0], m[1])
        time.sleep(2)    


#check if database has changed
mtime_last = getmtime(DB_PATH)

while True:
    time.sleep(10)
    mtime_cur = getmtime(DB_PATH)
    if mtime_cur > mtime_last:

        if DEBUG:
            print('DB: prev mtime = ' + str(mtime_last) + ' | ' + datetime.fromtimestamp(mtime_last).strftime("%m/%d/%Y, %H:%M:%S"))
            print('DB:  new mtime = ' + str(mtime_cur) + ' | ' + datetime.fromtimestamp(mtime_cur).strftime("%m/%d/%Y, %H:%M:%S"))

        handleTexts(datetime.fromtimestamp(mtime_last))
    else:
        pass
    mtime_last = mtime_cur

