import requests, sys, os, json, boto3, io, string, subprocess, time, random
from os import path


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


def combineVoices(num, folderName):
    command = "cd \"" + folderName + "\" ; "
    command += "ffmpeg -i " #sample1.mp3 -i sample2.mp3 -i sample3.mp3 -i sample4.mp3 -filter_complex '[0:0][1:0][2:0][3:0]concat=n=4:v=0:a=1[out]' -map '[out]' output.mp3"
    for i in range(1, num + 1):
        if(i == num):
            command += "voice" + str(i) + '.mp3'
        else:
            command += "voice" + str(i) + '.mp3 -i '
    command += " -filter_complex '"
    for i in range(0, num):
        command += "[" + str(i) + ":0]"
    command += "concat=n=" + str(num)
    command += ":v=0:a=1[out]' -map '[out]' ALL.mp3"
    #$print(command)
    subprocess.call('C:/Windows/system32/WindowsPowerShell/v1.0/powershell.exe ' + command, shell=True)
    #os.system(command)

def combineAllVoices(fnames, transitionFname, mp3Fname):
    command = "ffmpeg -i " #sample1.mp3 -i sample2.mp3 -i sample3.mp3 -i sample4.mp3 -filter_complex '[0:0][1:0][2:0][3:0]concat=n=4:v=0:a=1[out]' -map '[out]' output.mp3"
    cnt = 0
    for i in range(0, len(fnames)):
        if(i == len(fnames)-1):
            command += fnames[i]
            cnt = cnt + 1
        else:
            command += fnames[i] +  ' -i '
            command += transitionFname + ' -i '
            cnt = cnt + 2
    command += " -filter_complex '"
    for i in range(0, cnt):
        command += "[" + str(i) + ":0]"
    command += "concat=n=" + str(cnt)
    command += ":v=0:a=1[out]' -map '[out]' -threads 4 " + mp3Fname + ".mp3"
    print(command)
    subprocess.call('C:/Windows/system32/WindowsPowerShell/v1.0/powershell.exe ' + command, shell=True)

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
    try:
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
    except:
        print(sys.exc_info()[0])
        return False

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
    for dirName, subdirList, fileList in os.walk(folderName + '/txt'):
        prevVoice = ''
        for fname in fileList:
            textFname = folderName + '/txt/' + fname
            noExtFname = fname.replace('.txt', '')
            if(not path.exists(folderName + '/mp3/' + noExtFname)):
                prevVoice = getVoice(prevVoice)
                content = open(textFname, 'r', encoding='utf-8').read()
                content = cleanText(content)
                splitAndSave(prevVoice, content, folderName + '/mp3', noExtFname)

def grabAll(folderName, transitionName):
    fnames = []
    for dirName, subdirList, fileList in os.walk(folderName + '/mp3'):
        if( os.path.exists(dirName + "/ALL.mp3")):
            if(dirName.find('\\title') > -1):
                print('Title found')
                fnames.insert(0, dirName + "/ALL.mp3")
            else:
                fnames.append(dirName + "/ALL.mp3")
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
        allComments['title'] = data[0]['data']['children'][0]['data']['title']
        #titleFname = makeTitle(data[0]['data']['children'][0]['data']['permalink'].split('/')[5])
        for commentObj in data[1]['data']['children']:
            linkID = ''
            if 'id' in commentObj['data']:
                linkID = commentObj['data']['id']
                if 'body' in commentObj['data']:
                    text = cleanText(commentObj['data']['body'])
                    #Has to be at least 10 words
                    if(len(text.split(' ')) >= 10):
                        allComments[linkID] = text
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

def runComments(folderName, url):
    if(not os.path.exists(folderName)):
        os.mkdir(folderName)
        os.mkdir(folderName + '/txt')
        os.mkdir(folderName + '/mp3')
    allComments = getRedditComments(url.strip())
    for key,comment in allComments.items():
        open(folderName + '/txt/' + key + '.txt', 'w', encoding='utf-8').write(comment)
        saveAllVoices(folderName)
        


def getVoice(prevVoice):
    voiceList = list(voices)
    if prevVoice != '':
        voiceList.remove(prevVoice)
    return voiceList[random.randint(0, len(voiceList)-1)]


#Usage
#1. Get post - get <folder> <url>
#2. Text to speech - speech <folder>

action = sys.argv[1]

if action == 'get':
    folderName = sys.argv[2]
    runList(folderName)
    checkFiles(folderName)
elif action == 'comments':
    folderName = sys.argv[2]
    url = sys.argv[3]
    runComments(folderName, url)
    grabAll(folderName, "whoosh")
elif action == 'combine':
    folderName = sys.argv[2]
    grabAll(folderName, "whoosh")
elif action == 'check':
    folderName = sys.argv[2]
    checkFiles(folderName)