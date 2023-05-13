import lib
import os
import pickle
import time


class Datastore:
    def __init__(self, textController=None):
        ''' load data from pickle or initialize.  If textcontroller is passed, it will pull latest texts and update last_text state as well. '''
        #try to load state, if not successful create empty
        try:
            with open('state.pkl', 'rb') as p:
                self.state = pickle.load(p) 

        except:
            print('CANNOT FIND STATE.PKL, initializing')
            self.state = {'last_text': {}, 'on_tablet': {}, 'print_queue': [] }

        #update last_texts if textController is passed
        if textController is not None:
            self.updateLastTexts(textController)


    def updateLastTexts(self, textController):
        ''' grab latest texts and update for people in addressbook and in last_text. '''

        keys = self.state['last_text'].keys()
        updates = textController.getLatestTexts(keys)

        for u in updates:
            self.state['last_text'][u] = updates[u]

        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 


    def printQueue(self):
        '''return print_queue'''
        return self.state['print_queue']

    def addToPrintQueue(self, messages):
        '''add messages array to print queue'''
        self.state['print_queue'].extend(messages)
        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 

    def replacePrintQueue(self, queue):
        '''replace queue'''
        self.state['print_queue'] = queue
        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 


    def lastTexts(self):
        ''' return last texts '''
        return self.state['last_text']

    def addTexts(self, textdict):    
        ''' update last texts from dictionary {numstring:text, numstring:text...} '''
        for n in textdict:
            self.state['last_text'][n] = textdict[n]

        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 

    
    def getTextsNotOnDevice(self):
        '''return dict of numstring:text that need to be pushed to device; assumes last_text is up to date, and looks for
        (1) keys in last_text that are not on device, and (2) texts on device that don't match latest text in last_text '''
        returnval = {}

        for num in self.state['last_text']:
            
            if num in self.state['on_tablet'].keys():
                if self.state['on_tablet'][num]['text'] != self.state['last_text'][num]:
                    returnval[num] = self.state['last_text'][num]
            else:    
                returnval[num] = self.state['last_text'][num]

        return returnval


    def onTablet(self):
        ''' return on_tablet state '''
        return self.state['on_tablet']

    def updateOnTablet(self, numstring, entry):
        ''' update one entry on_tablet based on numstring '''
        self.state['on_tablet'][numstring] = entry

        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 

    def removeOnTablet(self, numstring):
        del self.state['on_tablet'][numstring]

        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 


    def writeOnTablet(self, on_tablet):
        ''' update on_tablet state by overwriting and save it '''
        self.state['on_tablet'] = on_tablet

        with open('state.pkl', 'wb') as p:
            pickle.dump(self.state, p) 


    def pdfsToRemarkable(self):
        ''' return filepaths of new pdfs ready to be pushed to remarkable.'''
        return ['TO_REMARKABLE/' + f for f in os.listdir('TO_REMARKABLE') if '.pdf' in f]

    def pdfsFromRemarkable(self):
        ''' return filepaths downloaded from Remarkable, waiting to be OCRed and sent. '''
        return ['FROM_REMARKABLE/' + f for f in os.listdir('FROM_REMARKABLE') if '.pdf' in f]

    def deletePDF(self, pdf):
        ''' delete a pdf if it's in the right folder '''
        if 'TO_REMARKABLE/' in pdf and '.pdf' in pdf:
            os.remove(pdf)
            os.remove(pdf[:-3] + 'meta')
        elif 'FROM_REMARKABLE/' in pdf and '.pdf' in pdf:
            os.remove(pdf)
        else:
            print('Improper file construction, not deleting ' + pdf)




def pushPDFsToRemarkable():
    '''pushing to remarkable helper'''

    #grab all pdfs in folder
    pdfs = datastore.pdfsToRemarkable()

    #only push if we have pdfs waiting, we're connected and not editing
    if len(pdfs) and rm.notEditing():

        #for each pdf:
        for p in pdfs:
            print('pushing ' + p + ' to remarkable.')

            #push to remarkable
            node, last_mtime = rm.pushDocument(p)
            print('done.')

            #on success: 
            if node is not None:

                #create entry for on_device data 
                with open(p[:-3] + 'meta', 'rb') as metadata:

                    numstring, entry = pickle.load(metadata) 

                    entry['node'] = node
                    entry['last_mtime'] = last_mtime

                    print('success, adding on_tablet [' + numstring + '] = ' + str(entry))

                    #update entry
                    datastore.updateOnTablet(numstring, entry)

                #delete from pdfs folder
                datastore.deletePDF(p)


def pullPDFsFromRemarkable():
    '''pulling pdfs helper'''

    #grab files that are on device
    on_device = datastore.onTablet()

    #iterate over them and their last modified time
    to_remove = []
    for numstring in on_device.keys():
        #check if updated, pull file if so
        if rm.pullIfUpdated(on_device[numstring]['node'], on_device[numstring]['last_mtime'], 'FROM_REMARKABLE'):
            print('Got updated file for ' + on_device[numstring]['name'] + '...')
            #on successful pull, add it back to queue
            to_pdf_queue[numstring] = on_device[numstring]['text']
            #on successful pull, delete it from tablet state
            to_remove.append(numstring)

    for numstring in to_remove:        
        datastore.removeOnTablet(numstring)


def sendPDFsAsText():
    for p in datastore.pdfsFromRemarkable():

        print('Processing ' + p + '...', end='')
        numstring, text, img = pdf.ocrPDF(p)

        print('done.\n\t-- ' + numstring + ': ' + text + '\n\tSending text...', end='')
        failed = textControl.sendText(numstring, text)
        if not failed:
            print('Successful.\n\tDeleting PDF...', end='')
            datastore.deletePDF(p)
            print('done.\n\tSending image...', end='')
            textControl.sendImage(numstring, os.getcwd() + '/' + img)
            print('Sent.\n\tRemoving temp image file...', end='')
            os.remove(img)
            print('done.')
        else:
            print('failed. Leaving PDF to be processed again.')


def handleNewTexts(messages):
    ''' iterate over sorted new messages; add to printer queue.  print queue, add incoming to to_pdf_queue.'''

    #iterate and add new incoming to to_pdf_queue
    try:
        for m in messages:
            if not m[5]:
                print('Added message from ' + str(m[0]) + ' to to_pdf_queue.')
                to_pdf_queue[m[0]] = m[1]

    except Exception as e:
        print('ERROR: could not add incoming text to pdf queue!!')
        print(e)

    #add all new messages to print queue
    datastore.addToPrintQueue(messages)

    #get full print queue (includes potential backlog)
    queue = datastore.printQueue()

    #iterate over queue
    while(len(queue)):
        m = queue[0]

        if m[5]:
            print('>> Printing Outgoing...')
            try:
                printer.printOutgoingText(m[2][:-3], m[0], m[1])
                print('>> ' + str(m[0]) + ': ' + m[1])
                queue.pop(0)
            except:
                print('>> PRINTER NOT RESPONDING...')
                break
        else:
            print('>> Printing Incoming...')
            try:
                printer.printIncomingText(m[2][:-3], m[0], m[1])
                print('>> ' + str(m[0]) + ': ' + m[1])
                queue.pop(0)
            except:
                print('>> PRINTER NOT RESPONDING...')
                break
            to_pdf_queue[m[0]] = m[1]
        print('>> done.')

    datastore.replacePrintQueue(queue)
    print('PRINT QUEUE STATE: ' )
    for p in datastore.printQueue():
        print(p)




textControl = lib.textController(debug=True)
printer = lib.printController() 
rm = lib.remarkable 
pdf = lib.processPDF 

print('load previous data and search for new texts...')
datastore = Datastore(textControl)
print('grabbing new texts that are not on_device from addressbook...')
to_pdf_queue = datastore.getTextsNotOnDevice()
print('generating new pdfs in TO_REMARKABLE folder...')
to_pdf_queue = pdf.generatePDFs(to_pdf_queue)
print('pushing to remarkable...')
rm.connect()
print('connected.')
pushPDFsToRemarkable()

print('entering loop...')
while(1):
    print('-- ITERATE --')


    print('check pdf modified times and pull edited onces...')
    pullPDFsFromRemarkable()
    print('done.')

    print('sending downloaded PDFs as texts...')
    sendPDFsAsText()
    print('done.')

    print('check for new messages...', end='')
    messages = textControl.getTexts()
    print('got ' + str(len(messages)) + '.')
    handleNewTexts(messages)
    print('done.')

    print('generate new pdfs...', end='')
    #generate PDFs in TO_REMARKABLE folder
    to_pdf_queue = pdf.generatePDFs(to_pdf_queue)
    print('done.')

    print('push new pdfs...', end='')
    #push pdfs to remarkable
    pushPDFsToRemarkable()
    print('done.')

    rm.disconnect()
    time.sleep(15)
    rm.connect()
