import remarkableAPI
import time

document = './TO_REMARKABLE/8234567890.pdf'

if remarkableAPI.isConnected():
    print('connected successfully')
    node, last_mtime = remarkableAPI.pushDocument(document)

for i in range(10):
    if remarkableAPI.isConnected():
        print('connected successfully')
        if remarkableAPI.notEditing():
            print('not editing, pull if updated')
            remarkableAPI.pullIfUpdated(node, last_mtime, 'FROM_REMARKABLE')
        else:
            print('Editing Detected')
    
    time.sleep(3)


