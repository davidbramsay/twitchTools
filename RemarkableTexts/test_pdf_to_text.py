from pdf2image import convert_from_path
import cv2
import numpy as np 
import easyocr
import pytesseract
from autocorrect import Speller
from google.cloud import vision

#MUST 'brew install poppler'
#MUST 'brew install tesseract'

#to test simpleHTR, I created a PNG of the text
#and ran 'python main.py --img_file ../handwritingTestImage.png'
#in its src folder after importing the line model

#for google vision API, install google CLI using
#
#"curl https://sdk.cloud.google.com | bash"
#"gcloud init"
#"gcloud projects create dramsayocrtext" #this name must be unique to your project, of all projects ever created in gcloud
#"gcloud auth login"
#"gcloud config set project dramsayocrtext"
#"gcloud auth application-default login"
#"gcloud auth application-default set-quota-project dramsayocrtext"
#
#enable API in google cloud console
#enable billing in google cloud console ($1.50/1000 images)
#
#pip3 install google-cloud-vision

SHOW_IMAGES = False
SHARPEN = False
SPELLCHECK = False
OCR_ENGINE = 'GOOGLE' # 'GOOGLE', 'EASYOCR', 'TESSERACT'

def show(img):
    cv2.imshow("img", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



# grab handwriting pdf with convert_from_path function
images = convert_from_path('8234567890.pdf', poppler_path="/usr/local/Cellar/poppler/23.03.0/bin")
img = np.array(images[0])

# Crop to just the part with the handwriting
img = img[2*395:2*1170,0:2*827]

# Greyscale and Sharpen
if SHARPEN:
    print('using greyscale and threshold to sharpen.')
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if SHOW_IMAGES: show(img)

    sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    img = cv2.filter2D(img, -1, sharpen_kernel)
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    if SHOW_IMAGES: show(img)

# OCR
if OCR_ENGINE=='EASYOCR':
    print('using easyocr.')
    reader = easyocr.Reader(['en'],gpu = False)
    ocr_output = reader.readtext(img,paragraph=True)[0][1]

elif OCR_ENGINE=='TESSERACT':
    print('using tesseract.')
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    ocr_output = pytesseract.image_to_string(img_rgb)

elif OCR_ENGINE=='GOOGLE':
    print('using google cloud.')
    success, img_jpg = cv2.imencode('.jpg', img)
    byte_img = img_jpg.tobytes()
    google_img = vision.Image(content=byte_img)

    client = vision.ImageAnnotatorClient()
    resp =  client.text_detection(image=google_img)
    ocr_output = resp.text_annotations[0].description.replace('\n',' ')

else:
    ocr_output = ' ERROR: no ocr tool selected. Choose "GOOGLE","EASYOCR", or "TESSERACT"'

# Spellcheck
if SPELLCHECK:
    print('using autocorrect.')
    spell = Speller(only_replacements=True)
    final_text = spell(ocr_output)

ocr_output += ' (OCRed in python; forgive typos)'

print('-'*10)
print(ocr_output)
print('-'*10)
