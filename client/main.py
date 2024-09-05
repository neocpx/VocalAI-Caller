
import shutil
import subprocess
import websockets
import asyncio

def is_installed(lib_name: str):
    return shutil.which(lib_name) is not None

async def stream(audio_stream, timeout=5):
    if not is_installed("mpv"):
        raise ValueError("mpv not found, necessary to stream audio.")

    mpv_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    try:
        while True:
            try:
                chunk = await asyncio.wait_for(audio_stream.__anext__(), timeout=timeout)
                if chunk:
                    mpv_process.stdin.write(chunk)
                    mpv_process.stdin.flush()
                else:
                    break
            except asyncio.TimeoutError:
                print(f"No audio chunk received for {timeout} seconds. Stopping the stream.")
                break
            except StopAsyncIteration:
                break
    except asyncio.CancelledError:
        print("Streaming cancelled.")
    finally:
        if mpv_process.stdin:
            mpv_process.stdin.close()
        mpv_process.wait()


async def receive_initial_audio(conn):
    async def audio_stream():
        try:
            while True:
                chunk = await conn.recv()
                if chunk:
                    yield chunk
                else:
                    break
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server.")
        except asyncio.CancelledError:
            print("Audio stream cancelled.")

    print("Receiving initial audio from server...")
    await stream(audio_stream())

async def connect_with_server(uri: str):
    try:
        async with websockets.connect(uri) as conn:
            print("Connection established")
            
            await receive_initial_audio(conn)
            
            while True:
                text = input("you: ")
                await conn.send(text)
            
                async def audio_stream():
                    try:
                        while True:
                            chunk = await conn.recv()
                            if chunk:
                                yield chunk
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection closed by server.")
                    except asyncio.CancelledError:
                        print("Audio stream cancelled.")

                await stream(audio_stream())
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    uri = "ws://localhost:8000/tts"
    try:
        asyncio.run(connect_with_server(uri))
    except KeyboardInterrupt:
        print("Client terminated.")

