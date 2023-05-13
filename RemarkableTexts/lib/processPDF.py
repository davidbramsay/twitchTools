from fpdf import FPDF
from pdf2image import convert_from_path
import cv2
import numpy as np 
from google.cloud import vision
import emoji
import random
import pickle

from .addresses import ADDRESS_BOOK

#MUST 'brew install poppler'

def _getName(numstring):
    '''given a numstring with +12223334444, return name associated if in dictionary (otherwise return string) '''
    try:
        return ADDRESS_BOOK[numstring]
    except:
        return numstring


def _getNumstring(name):
    '''given a name, return associated numstring from addressbook or preserve numstring otherwise'''
    for numstring in ADDRESS_BOOK.keys():
        if ADDRESS_BOOK[numstring] == name:
            return numstring

    return name


def generatePDFs(to_pdf_queue):
    ''' generate pdfs in dictionary {numstring:text, numstring:text...}.  Return queue-- if success it will be empty, otherwise it will remain full '''
    try:
        for numstring in to_pdf_queue.keys():
            generatePDF(numstring, to_pdf_queue[numstring])
        return {}
    except Exception as e:
        print('Error generating PDFs')
        print(e)
        return to_pdf_queue


def generatePDF(numstring, message):
    '''create a pdf and save it in the 'TO_REMARKABLE' folder alongside useful metadata'''

    try:
        metadata= {numstring: {'text': message, 'name': _getName(numstring)}}
        print('Generating PDF for ' + metadata[numstring]['name'] + '...')

        # save FPDF() class into a variable
        pdf = FPDF()
         
        # Add a page
        pdf.add_page()
         
        #demoji and cut message off after 1100 characters
        printmessage = emoji.demojize(message)[-1100:]

        #convert phonenumber to name
        name = _getName(numstring)

        # set style and size of font
        # that you want in the pdf
        pdf.add_font("CMU", '', "cmuntb.ttf", uni=True)
        pdf.set_font("CMU", size = 12)
     
        # create a cell
        pdf.cell(200, 10, txt = 'From: ' + name,
                 ln = 1, align = 'L')
         
        # add another cell
        pdf.multi_cell(180, 5, txt = printmessage, align = 'L')
         

        #draw line below which we will write
        pdf.line(70, 100, 210-70, 100)

        #draw lines for writing
        for i in range(0,10):
            pdf.line(10, 125+i*17, 200, 125+i*17)

        # save the pdf with name .pdf
        filename = 'TO_REMARKABLE/' +  name + '.pdf'
        pdf.output(filename)  

        #generate metadata
        metadata= [numstring, {'text': message, 'name': name}]

        #write metadata as well
        with open(filename[:-3] + 'meta', 'wb') as p:
            pickle.dump(metadata, p) 

        print('done.')
        return filename

    except Exception as e:
        print('FAILED TO TURN INTO PDF:')
        print(e)
        print(name + ': ' + message)
        return None


def ocrPDF(pathPDF):
    ''' return (numstring, OCRed_text) from PDF at path '''

    # grab handwriting pdf with convert_from_path function
    images = convert_from_path(pathPDF, poppler_path="/usr/local/Cellar/poppler/23.03.0/bin")
    img = np.array(images[0])

    # Crop to just the part with the handwriting
    img = img[2*395:2*1170,0:2*827]

    print('using google cloud for ocr on ' + pathPDF + '...')
    success, img_jpg = cv2.imencode('.jpg', img)
    byte_img = img_jpg.tobytes()
    google_img = vision.Image(content=byte_img)

    client = vision.ImageAnnotatorClient()
    resp =  client.text_detection(image=google_img)
    ocr_output = resp.text_annotations[0].description.replace('\n',' ')

    ocr_output += ' (OCRed in python; forgive typos)'

    name = pathPDF.split('/')[-1][:-4]          
    numstring = _getNumstring(name)          

    img_filepath = 'temp/' + numstring[1:] + format(random.getrandbits(32), 'x') + '.jpg'          
    if not cv2.imwrite(img_filepath, img):
        print('error writing file')
    print('created ' + img_filepath)    

    return numstring, ocr_output, img_filepath


