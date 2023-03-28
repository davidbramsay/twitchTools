from fpdf import FPDF
 
 
# save FPDF() class into a
# variable pdf
pdf = FPDF()
 
# Add a page
pdf.add_page()
 
phoneNumber='8234567890'
message='this is a test, lets see how it goes with a longer string that could realistically be sent as a text message.'
message = (message + ' | ')*10

#cut message off after 1100 characters
message = message[-1100:]

# set style and size of font
# that you want in the pdf
pdf.add_font("CMU", '', "cmuntb.ttf", uni=True)
pdf.set_font("CMU", size = 12)
 
# create a cell
pdf.cell(200, 10, txt = 'From: ' + phoneNumber[0:3] + '-' + phoneNumber[3:6] + '-' + phoneNumber[6:],
         ln = 1, align = 'L')
 
# add another cell
pdf.multi_cell(180, 5, txt = message, align = 'L')
 

#draw line below which we will write
pdf.line(70, 100, 210-70, 100)

#draw lines for writing
for i in range(0,10):
    pdf.line(10, 125+i*17, 200, 125+i*17)

# save the pdf with name .pdf
pdf.output("new_texts_pdf/" + phoneNumber + ".pdf")  
