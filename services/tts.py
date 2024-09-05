import asyncio
import shutil
import subprocess
from openai import AsyncOpenAI
from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs

import speech_recognition as sr

VOICE_ID = '21m00Tcm4TlvDq8ikWAM'

aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
r = sr.Recognizer()


def is_installed(lib_name):
    return shutil.which(lib_name) is not None


async def text_chunker(chunks):
    """Split text into chunks, ensuring to not break sentences."""
    splitters = (".")
    buffer = ""

    async for text in chunks:
        if buffer.endswith(splitters):
            yield buffer + " "
            buffer = text
        elif text and text.startswith(splitters):
            yield buffer + text[0] + " "
            buffer = text[1:]
        elif text:
            buffer += text
        else:
            yield " "

    if buffer:
        yield buffer + " "


async def stream(audio_stream):
    """Stream audio data using mpv player."""
    if not is_installed("mpv"):
        raise ValueError(
            "mpv not found, necessary to stream audio. "
            "Install instructions: https://mpv.io/installation/"
        )

    mpv_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    async for chunk in audio_stream:
        if chunk:
            mpv_process.stdin.write(chunk)
            mpv_process.stdin.flush()

    if mpv_process.stdin:
        mpv_process.stdin.close()
    mpv_process.wait()


async def text_to_speech_input_streaming(voice_id, text_iterator):
    """Send text to ElevenLabs API and stream the returned audio."""
    
    client = AsyncElevenLabs(
    )


    async for text in text_chunker(text_iterator):
        print(text)
        data = await client.generate(
            output_format="mp3_22050_32",
            text=text,
            model="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.1,
                similarity_boost=0.3,
                style=0.2,
            ),
        )
        await stream(data)

async def text_to_speech(voice_id, text):
    """Send text to ElevenLabs API and stream the returned audio."""
    
    client = AsyncElevenLabs(
    )


    data = await client.generate(
            output_format="mp3_22050_32",
            text=text,
            model="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.1,
                similarity_boost=0.3,
                style=0.2,
            ),
        )
    await stream(data)

async def chat_completion(query, history=None):
    """Retrieve text from OpenAI and pass it to the text-to-speech function in Hindi with conversation history support."""
    if history is None:
        history = []
    history.append({'role': 'system', 'content': 'Please respond in Hindi for all queries. answere accordingly, if room is available type `#AVAIL` or `#NOT` if not, in case more infp is needed type `#CONNECT`'})
    
    history.append({'role': 'user', 'content': query})

    response = await aclient.chat.completions.create(
        model='gpt-4o',
        messages=history,
        temperature=1,
        stream=True
    )

    async def text_iterator():
        async for chunk in response:
            delta = chunk.choices[0].delta
            yield delta.content

    await text_to_speech_input_streaming(VOICE_ID, text_iterator())


if __name__ == "__main__":
    initial_input = '"नमस्ते, मैं Zeek Fab Hotels से बोल रहा हूँ। मैं 21 September से 20 October तक के लिए deluxe room की availability के बारे में जानकारी लेना चाहता हूँ। क्या आप please confirm कर सकते हैं और अगर available है तो pricing और booking process के बारे में भी बता सकते हैं?"'
    
    asyncio.run(text_to_speech(VOICE_ID, initial_input))

    history = [{'role': 'user', 'content': f"you asked customer {initial_input}"}]

    while True:
        with sr.Microphone() as source:
            audio = r.listen(source)
            response = r.recognize_whisper_api(audio, api_key=OPENAI_API_KEY)
        print(f"you : {response}")
        history.append({'role': 'user', 'content': f"customer response : {response}"})
        if response.lower() in ['exit', 'quit']:
            break
        asyncio.run(chat_completion(
            query="answer",
            history=history
        ))


