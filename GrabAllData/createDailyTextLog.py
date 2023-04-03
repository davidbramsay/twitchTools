from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flair.models import TextClassifier
from flair.data import Sentence
from textblob import TextBlob
from imessage_reader import fetch_data
from datetime import datetime, timedelta
from os.path import expanduser, getmtime
import time
import json

# The path to the iMessage database
DB_PATH = expanduser("~") + "/Library/Messages/chat.db-wal"

#if HOURS24, get texts in last 24 hours;
#else get texts sharing today's date 
HOURS24 = True

sia = SentimentIntensityAnalyzer()
flair = TextClassifier.load('en-sentiment')
     
def processText(m):

    flair_sentence = Sentence(m[1])
    flair.predict(flair_sentence)

    results = {'phoneID': hash(m[0]), 
               'localtime': m[2],
               'timestamp': datetime.timestamp(datetime.strptime(m[2], '%Y-%m-%d %H:%M:%S')),
               'vader': sia.polarity_scores(m[1]),
               'textblob': TextBlob(m[1]).sentiment,
               'flair': {'value': flair_sentence.labels[0].value, 'score': flair_sentence.labels[0].score},
               'incoming': 0 if m[5] else 1,
               'wordcount': len(m[1].split(' '))}
    '''
    if m[5]:
        print(m[2] + ':' + m[1] + ' (TO ' + m[0] + ')')
    else:
        print(m[2] + ':' + m[1] + ' (FROM ' + m[0] + ')')
    '''

    return results


def grabTextsToday():
    #grab texts (user id, message, date, service, account, is_from_me)
    fd = fetch_data.FetchData()
    messages = fd.get_messages()

    d = datetime.now()

    #sort by converted timestamp strings to datetime
    messages = sorted(messages, key=lambda tup: datetime.strptime(tup[2], '%Y-%m-%d %H:%M:%S'))
    index = -1

    results =[] 

    while(1):
        m = messages[index]
        if (HOURS24 and ((d - datetime.strptime(m[2], '%Y-%m-%d %H:%M:%S')) < timedelta(hours=24))):     
            results.append(processText(m))
        elif (not HOURS24 and (d.strftime("%Y-%m-%d") in m[2])):
            results.append(processText(m))
        else:    
            break
        index -= 1

    return results

if __name__=="__main__":

    d = datetime.now()
    timestring = d.strftime("%m%d%Y_%H%M%S")

    results = grabTextsToday()
    for r in results:
        print(r)
        print('--')

    jsonfile = json.dumps(results)
    with open(timestring + "_textlog.json", "w") as outfile:
        outfile.write(jsonfile)
