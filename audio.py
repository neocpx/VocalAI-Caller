import speech_recognition as sr

# obtain audio from the microphone
r = sr.Recognizer()


while True:
    with sr.Microphone() as source:
        audio = r.listen(source)
    try:
        print(f"You : {r.recognize_whisper_api(audio, api_key=OPENAI_API_KEY)}")
    except sr.RequestError as e:
        print(f"Could not request results from Whisper API; {e}")
