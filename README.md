# reddit-to-voice-script
Simple script to translate reddit text post into mp3 files

Reqirements:
* AWS Polly Keys
* FFMPEG

STEP 1: Get AWS Polly accessible key from Amazon which provides 4 million free text to speech character per month.

STEP 2: Install FFMPEG. This is to provie command interface the script to use to combine mp3 files into one.

STEP 3: In a file "keys" (no extension) add Polly accessible AWS keys. First line should be your access key id and second line should be your secret access key.

STEP 4: Grab all reddit links to text base posts and add to get.txt. Browser extension such as copy tab URLs should help.

STEP 5: Run "python awsaudio.py get nameofaudio". Any URLs that did not make it will be printed in console. You may run check instead of get to pull this list anytime.

STEP 6: If any errors adjust get.txt and rerun

STEP 7: Run "python awsaudio.py combine nameofaudio". An MP3 should show in root.