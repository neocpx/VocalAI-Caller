from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs


client = ElevenLabs(
)
data = client.text_to_speech.convert(
    voice_id="pMsXgVXv3BLzUgSXRplE",
    optimize_streaming_latency="0",
    output_format="mp3_22050_32",
    text="It sure does, Jackie… My mama always said: “In Carolina, the air's so thick you can wear it!”",
    voice_settings=VoiceSettings(
        stability=0.1,
        similarity_boost=0.3,
        style=0.2,
    ),
)

with open('output.mp3', 'wb') as f:
    for it in data:
        f.write(it)
