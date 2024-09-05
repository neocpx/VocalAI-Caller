import config
from openai import AsyncOpenAI
from fastapi import APIRouter
from fastapi.websockets import WebSocket
from fastapi.websockets import WebSocketDisconnect
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings
from collections.abc import AsyncIterator


class ElevenLabsService:
    def __init__(self):
        self._client = AsyncElevenLabs(api_key="sk_71ad2d07a0fd8b1ce238504de63e375f3bab36ccf4c25628")
    
    async def get_audio(self, text: str) -> AsyncIterator[bytes]:
        return await self._client.generate(
        output_format="mp3_22050_32",
        text=text,
        model="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.1,
            similarity_boost=0.3,
            style=0.2,
        ),
    )

class OpenAiService:
    def __init__(self):
        self._client = AsyncOpenAI(api_key=config.OPENAI_API_KEY) 
    async def chat_completion(self, query: str, history: list):
        if history is None:
            history = []

        history.append({'role': 'system', 'content': 'Please respond in Hindi for all queries. answere accordingly'})
        history.append({'role': 'user', 'content': query})

        response = await self._client.chat.completions.create(
            model='gpt-4o',
            messages=history,
            temperature=1,
            stream=True
        )

        async def text_iterator():
            async for chunk in response:
                delta = chunk.choices[0].delta
                yield delta.content

        return text_iterator()


router = APIRouter()
@router.websocket("/tts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    eleven_labs_service = ElevenLabsService()
    openai_servive = OpenAiService()
    try:
        initial_message = "Hello, this is bot communication."
        history = [{'role': 'user', 'content': f"you asked customer {initial_message}"}]
        audio_stream = await eleven_labs_service.get_audio(initial_message)
        async for chunk in audio_stream:
            await websocket.send_bytes(chunk)
        while True:
            text = await websocket.receive_text()
            history.append({'role': 'user', 'content': f"merchant response : {text}"})
            text_stream = await openai_servive.chat_completion(query="reply as a customer", history=history)
            async for text_chunk in text_stream:
                audio_stream = await eleven_labs_service.get_audio(text_chunk)
                async for audio_chunk in audio_stream:
                    await websocket.send_bytes(audio_chunk)
    
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.close()
