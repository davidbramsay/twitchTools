import PySimpleGUI as sg
from datetime import datetime
  
# Add some color
# to the window
sg.theme('SandyBeach')     
  
# Very basic window.
# Return values using
# automatic-numbered keys
layout = [
    [sg.Text('Note', size =(35, 1)), sg.Input('', key='-INPUT-', )],
    [sg.Button('Submit', visible=False, bind_return_key=True)]
]
  
window = sg.Window('Simple Notes', layout)

while True:

    event, values = window.read()

    if event in (None, 'Exit'):
        break
    elif event == 'Submit':
        now = datetime.now()
        currentTime = now.strftime("%H:%M:%S")
        currentDate = now.strftime("%m%d%y")

        with open('notes/' + currentDate + '_notes.txt', 'a+') as f:
            f.write(currentTime + ',' + values['-INPUT-'] + '\n')

        window['-INPUT-'].update('')

window.close()

