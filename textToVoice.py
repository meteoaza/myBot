import pyttsx3

tts = pyttsx3.init()
voices = tts.getProperty('voices')
for voice in voices:
    if voice.name == 'Aleksandr':
        tts.setProperty('voice', voice.id)
        tts.setProperty('rate', 200)
snd = tts.say('text')
tts.runAndWait()