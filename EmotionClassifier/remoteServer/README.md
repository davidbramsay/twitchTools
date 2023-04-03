This moves the emotion classifier from the laptop to the audio-mafia server.

Run the classifier remote server on the server and it waits with an open socket,
grabs a serialized stream of an open-cv streamed image, converts it to a jpg, and
runs deepface on it.  It then creates the classifier image and sends the final image
back to the requesting socket.


FOR THIS:

activate the venv:
source /emtionClassifier/bin/activate

run this on the server:
python3 classifierRemoteServer.py

run the remote classifier script on the laptop.
(python3 ../runClassifierREMOTE.py)


This requires the full deepface and gaze_tracking folders from the parent.

tensorflow              1.9.0
tensorflow-estimator    2.2.0
deepface                0.0.75
h5py                    2.10.0
Keras                   2.2.5
dlib                    19.24.1
opencv-python           4.6.0.66
protobuf                3.19.6
