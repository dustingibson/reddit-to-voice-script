import requests, sys, os, json, boto3, io, string, subprocess, time, random
from os import path
from pathlib import Path
from pydub import AudioSegment
import struct
#print(struct.calcsize("P") * 8)

# AudioSegment.converter = "C:\\ffmpeg\\bin\\ffmpeg.exe"
# AudioSegment.ffmpeg = "C:\\ffmpeg\\bin\\ffmpeg.exe"
# AudioSegment.ffprobe ="C:\\ffmpeg\\bin\\ffprobe.exe"

def getKeys():
    return open('keys', 'r').readlines()

voices = ['Amy', 'Emma', 'Brian', 'Kendra', 'Kimberly', 'Salli', 'Joey', 'Joanna', 'Matthew' ]

aws_akey_id  = getKeys()[0].strip()
aws_sec_key = getKeys()[1].strip()

client = boto3.client('polly', 
    region_name='us-west-2',
    aws_access_key_id=aws_akey_id,
    aws_secret_access_key=aws_sec_key)

def saveAWS(voice, speechText, savePath):
    try:
        time.sleep(0.2)
        response = client.synthesize_speech(
            Engine='standard',
            LanguageCode='en-US',
            Text=speechText,
            VoiceId=voice,
            OutputFormat='mp3'
        )
        open(savePath,'wb').write(response['AudioStream'].read())
        return True
    except:
        print(sys.exc_info()[0])
        #print("Unable to save")
        return False

def convert(inFname, outFname):
    subprocess.call(['ffmpeg', '-i', inFname + '.wav', '-vn', '-ar', '44100', '-ac' , '2', '-b:a', '96k', outFname + '.mp3'])
    os.remove(inFname + ".wav")

def combineVoices(num, folderName):
    combined = AudioSegment.empty()
    dirName = folderName + "/"
    for i in range(1, num + 1):
        fname = dirName + "voice" + str(i) + '.mp3'
        part = AudioSegment.from_mp3(fname)
        combined += part
    combined.export(dirName + "ALL.wav", format='wav')
    subprocess.call(['ffmpeg', '-i', (dirName + "ALL.wav"), '-vn', '-ar', '44100', '-ac' , '2', '-b:a', '96k', (dirName + "ALL.mp3")])
    os.remove((dirName + "ALL.wav"))


def combineAllVoices(fnames, transitionFname, mp3Fname):
    longTransition = 't/long.mp3'
    combined = AudioSegment.empty()
    outFnames = []
    for i in range(0, len(fnames)):
        print("processing " + str(i+1) + " of " + str(len(fnames)))
        part = AudioSegment.from_mp3(fnames[i])
        transition = AudioSegment.from_mp3( transitionFname if i+1 < len(fnames) and fnames[i+1].find('title') == -1 else longTransition )
        combined += part
        if(i != len(fnames)-1):
            combined += transition
        if( (i % 100 == 0 or i == len(fnames)-1) and i != 0 ) :
            partFname = mp3Fname + '/' + mp3Fname + str(i)
            combined.export(partFname + '.wav', format='wav')
            convert(partFname, partFname)
            combined = AudioSegment.empty()
            outFnames.append(partFname)
    combined = AudioSegment.empty()
    for i in range(0, len(outFnames)):
        print("processing " + str(i+1) + " of " + str(len(outFnames)))
        part = AudioSegment.from_mp3(outFnames[i] + '.mp3')
        combined += part
    combined.export(mp3Fname + ".wav", format='wav')
    subprocess.call(['ffmpeg', '-i', mp3Fname + ".wav", '-vn', '-ar', '44100', '-ac' , '2', '-b:a', '96k', mp3Fname + ".mp3"])
    os.remove(mp3Fname + ".wav")
    for outFname in outFnames:
        os.remove(outFname + ".mp3")

def printLink(listLinks, folderName):
    for link in listLinks:
        if( link.find(folderName) > -1 ):
            print(link.strip())
            return 1
    print(folderName)
    return 0

def checkFiles(folderName):
    listLinks = open("get.txt", 'r').readlines()
    for dirName, subdirList, fileList in os.walk(folderName + '/txt'):
        prevVoice = ''
        for fname in fileList:
            textFname = folderName + '/txt/' + fname
            noExtFname = fname.replace('.txt', '')
            if(not path.exists(folderName + '/mp3/' + noExtFname)):
                #print(folderName + '/mp3/' + noExtFname + ' does not exist')
                printLink(listLinks, noExtFname)
            else:
                prevVoice = getVoice(prevVoice)
                content = open(textFname, 'r', encoding='utf-8').read()
                content = cleanText(content)
                splitAndCheck(prevVoice, content, folderName + '/mp3', noExtFname)

def splitText(text, charLimit):
    if(len(text) <= charLimit):
        return [text]
    else:
        textList = []
        while True:
            idx = charLimit
            while(text[idx] not in string.whitespace and idx > 0):
                idx = idx - 1
            textList.append(text[0:idx])
            text = text[idx:len(text)]
            if len(text) <= charLimit:
                textList.append(text)
                break
        return textList

def splitAndSave(voice, allText, folderName, saveName):
    #Process 1000 char at a time.
    saveFolder = folderName + "/" + saveName
    if(not path.exists(folderName)):
        return False
    if(not path.exists(saveFolder)):
        os.mkdir(saveFolder)
    textList = splitText(allText , 1000)
    cnt = 0
    for curText in textList:
        cnt = cnt + 1
        fname = saveFolder + "/voice"  + str(cnt) + ".mp3"
        if not saveAWS(voice, curText, fname):
            return False
    combineVoices(cnt, saveFolder)
    return True

def splitAndCheck(voice, allText, folderName, saveName):
    try:
        #Process 1000 char at a time.
        saveFolder = folderName + "/" + saveName
        if(not path.exists(folderName)):
            print(folderName + " does not exist")
            return False
        nFiles = len(os.listdir(saveFolder))
        textList = splitText(allText , 1000)
        if(len(textList)+1 != nFiles):
            print("Issue with " + saveFolder)
            os.rmdir(saveFolder)
        # for curText in textList:
        #     cnt = cnt + 1
        #     fname = saveFolder + "/voice"  + str(cnt) + ".mp3"
        #     if not saveAWS(voice, curText, fname):
        #         return False
        #combineVoices(cnt, saveFolder)
        return True
    except:
        print(saveName + " - no bueno")
        return False


def saveAllVoices(folderName):
    prevVoice = ''
        #    for fileList in sorted(folderName + '/txt').iterdir(), key=os.path.getmtime):#os.walk(folderName + '/txt'):
    for fnamePath in sorted(Path(folderName + '/txt').iterdir(), key=os.path.getmtime):
        fname = str(fnamePath)
        print(fname)
        #textFname = folderName + '/txt/' + fname
        noExtFname = path.basename(fname).replace('.txt', '')
        if(not path.exists(folderName + '/mp3/' + noExtFname)):
            prevVoice = getVoice(prevVoice)
            content = open(fname, 'r', encoding='utf-8').read()
            content = cleanText(content)
            splitAndSave(prevVoice, content, folderName + '/mp3', noExtFname)

def grabAll(folderName, transitionName):
    fnames = []
    cnt = 0
    if( os.path.exists(folderName + '/keys.txt')):
        grabAllComments(folderName, transitionName)
    else:
        for dirNamePath in sorted(Path(folderName + '/mp3').iterdir(), key=os.path.getmtime):
            dirName = str(dirNamePath)
            if( os.path.exists(dirName + "/ALL.mp3")):
                fnames.append(dirName + "/ALL.mp3")
                cnt = cnt + 1
        combineAllVoices(fnames, 't/' + transitionName + '.mp3', folderName)

def grabAllComments(folderName, transitionName):
    fnames = []
    cnt = 0
    keys = open(folderName + '/keys.txt', 'r').readlines()
    for key in keys:
        dirName = folderName + '/mp3/' + key.strip()
        print(dirName)
        if( os.path.exists(dirName + "/ALL.mp3")):
            fnames.append(dirName + "/ALL.mp3")
            cnt = cnt + 1
    print(fnames)
    combineAllVoices(fnames, 't/' + transitionName + '.mp3', folderName)


def testVoice():
    text = open('sample.txt', 'r').read()
    splitAndSave('Amy', text, "hobby_drama",  "blah")
    #saveAWS('Amy', text, 'sample.mp3')

def makeTitle(text):
    illegalChars = ['/', '\\', '<', '>', '"', '|', '?', ':', '*']
    if(text[0] in '0123456789'):
        text = 'T' + text[0]
    for iChar in illegalChars:
        text = text.replace(iChar, '')
    return text

def getRedditPost(url):
    try:
        newUrl = url + '.json'
        r = requests.get(url = newUrl,headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36	'}) 
        data = json.loads(r.text)
        #text = data['data']['children'][0]['data']['selftext'] + '\r\n'
        if('error' in data):
            print(data)
            return ['','']
        titleFname = makeTitle(data[0]['data']['children'][0]['data']['permalink'].split('/')[5])
        title = data[0]['data']['children'][0]['data']['title']
        text = title + ' by ' + data[0]['data']['children'][0]['data']['author_fullname'] + '\r\n'
        text = text + cleanText(data[0]['data']['children'][0]['data']['selftext'])
        return [titleFname,text]
    except:
        print("Unable to get reddit post")
        return ['','ERROR']

def getRedditComments(url):
    allComments = {}
    topURL = url[0:len(url)-1] + '.json?sort=top'
    bestURL = url[0:len(url)-1] + '.json?sort=best'
    newURLs = [topURL, bestURL]
    for curURL in newURLs:
        r = requests.get(url = curURL,headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36	'}) 
        data = json.loads(r.text)
        #text = data['data']['children'][0]['data']['selftext'] + '\r\n'
        if('error' in data):
            print(data)
            return ['','']
        threadId = data[0]['data']['children'][0]['data']['name']
        allComments['title_' + threadId] = data[0]['data']['children'][0]['data']['title']
        #titleFname = makeTitle(data[0]['data']['children'][0]['data']['permalink'].split('/')[5])
        for commentObj in data[1]['data']['children']:
            linkID = ''
            if 'id' in commentObj['data']:
                linkID = commentObj['data']['id']
                if 'body' in commentObj['data']:
                    text = cleanText(commentObj['data']['body'])
                    #Has to be at least 10 words
                    if(len(text.split(' ')) >= 10):
                        allComments[threadId + '_' + linkID] = text
    return allComments

def cleanText(text):
    try:
        noChars = ['&gt;', '&lt;', '[', ']', '*', '#', '&amp;', 'x200B;', '&amp;nbsp;']
        text = text.encode('ascii', 'ignore').decode('ascii')
        #Remove links
        while True:
            startIdx = text.find('http')
            endIdx = startIdx
            while endIdx < len(text) and text[endIdx] not in string.whitespace:
                endIdx = endIdx + 1
            text = text.replace(text[startIdx:endIdx], '')
            if(text.find('http') < 0):
                break
        for curChar in noChars:
            text = text.replace(curChar, ' ')
        text = text.replace("\'", "'")
        return text
    except:
        print("Clean text issue")

def runList(folderName):
    if(not os.path.exists(folderName)):
        os.mkdir(folderName)
        os.mkdir(folderName + '/txt')
        os.mkdir(folderName + '/mp3')
    listURLs = open('get.txt', 'r').readlines()
    for url in listURLs:
        content = getRedditPost(url.strip())
        if content[1] == 'ERROR':
            print(url)
        elif content != '':
            open(folderName + '/txt/' + content[0] + '.txt', 'w', encoding='utf-8').write(content[1])
            saveAllVoices(folderName)

def runComments(folderName):
    if(not os.path.exists(folderName)):
        os.mkdir(folderName)
        os.mkdir(folderName + '/txt')
        os.mkdir(folderName + '/mp3')
    listURLs = open('get.txt', 'r').readlines()
    keys = []
    for url in listURLs:
        allComments = getRedditComments(url.strip())
        for key,comment in allComments.items():
            open(folderName + '/txt/' + key + '.txt', 'w', encoding='utf-8').write(comment)
            keys.append(key + '\n')
    listURLs = open('get.txt', 'r').readlines()
    open(folderName + '/keys.txt', 'w').writelines(keys)
    saveAllVoices(folderName)
        


def getVoice(prevVoice):
    voiceList = list(voices)
    if prevVoice != '':
        voiceList.remove(prevVoice)
    return voiceList[random.randint(0, len(voiceList)-1)]


#Usage
#1. Run text to speech from posts of get.txt - get <folder> <url>
#2. Run text to speech from comments of get.txt - comments <folder>
#3. Combine if needed - combine <folder>
#4. Check to make sure all files went through - check <folder> 

action = sys.argv[1]

if action == 'get':
    folderName = sys.argv[2]
    runList(folderName)
    checkFiles(folderName)
    grabAll(folderName, "whoosh")
elif action == 'comments':
    folderName = sys.argv[2]
    runComments(folderName)
    grabAll(folderName, "whoosh")
elif action == 'combine':
    folderName = sys.argv[2]
    grabAll(folderName, "whoosh")
elif action == 'check':
    folderName = sys.argv[2]
    checkFiles(folderName)