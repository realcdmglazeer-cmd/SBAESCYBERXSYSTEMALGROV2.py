import moviepy
import numpy as np
import random
import os
import time
import datetime

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

BLOCKS = [
    "▀", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▉", "▊", "▋", "▌", "▍", "▎",
    "▏", "▐", "░", "▒", "▔", "▕", "▙", "▚", "▛", "▜", "▟"
]
ORTHODOX_CROSS = "☦"

DURATION = 16
PIXEL_INTERVAL = 0.5
FLASH_DURATION = 4
FLASH_INTERVAL = 0.2
N_PIXELS = 341
VIDEO_SIZE = (1280, 720)

def random_title(n_blocks=6):
    blocks = [random.choice(BLOCKS) for _ in range(n_blocks)]
    return ORTHODOX_CROSS + ''.join(blocks)

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))

def pixel_positions(n, size):
    positions = set()
    while len(positions) < n:
        positions.add((random.randint(0, size[0]-1), random.randint(0, size[1]-1)))
    return list(positions)

def make_frame_factory(pixels, pixel_colors, bg_color):
    def make_frame(t):
        img = np.zeros((VIDEO_SIZE[1], VIDEO_SIZE[0], 3), dtype=np.uint8)
        img[:,:] = bg_color
        if t < DURATION:
            idx = int(t // PIXEL_INTERVAL)
            for i in range(min(idx+1, N_PIXELS)):
                x, y = pixels[i]
                img[y, x] = pixel_colors[i]
        else:
            if (int(((t-DURATION)/FLASH_INTERVAL)) % 2) == 0:
                img[:,:] = random_color()
        return img
    return make_frame

def make_audio(duration, pixels, pixel_colors, bg_color):
    fps = 48000
    total_samples = int(fps * (duration))
    audio = np.zeros(total_samples)
    t = 0.0
    while t < duration:
        if t < DURATION:
            idx = int(t // PIXEL_INTERVAL)
            if idx < N_PIXELS:
                if (t % PIXEL_INTERVAL) < 0.5:
                    freq = random.randint(1400, 3189)
                    samples = int(fps * 0.5)
                    start = int(t * fps)
                    end = min(start + samples, total_samples)
                    beep = 0.2 * np.sin(2 * np.pi * freq * np.linspace(0, 0.5, end-start))
                    audio[start:end] = beep
            t += PIXEL_INTERVAL
        else:
            if ((t - DURATION) % FLASH_INTERVAL) < 0.2:
                freq = random.randint(1400, 3189)
                samples = int(fps * 0.2)
                start = int(t * fps)
                end = min(start + samples, total_samples)
                beep = 0.2 * np.sin(2 * np.pi * freq * np.linspace(0, 0.2, end-start))
                audio[start:end] = beep
            t += FLASH_INTERVAL
    audio_stereo = np.vstack([audio, audio])
    return moviepy.audio.AudioClip.AudioArrayClip(audio_stereo, fps=fps)

def generate_video(filename, duration):
    pixels = pixel_positions(N_PIXELS, VIDEO_SIZE)
    pixel_colors = [random_color() for _ in range(N_PIXELS)]
    bg_color = random_color()
    video = moviepy.editor.VideoClip(make_frame_factory(pixels, pixel_colors, bg_color), duration=duration)
    audio = make_audio(duration, pixels, pixel_colors, bg_color)
    video = video.set_audio(audio)
    video.write_videofile(filename, fps=24, logger=None)

def upload_to_youtube(video_file, title, description, youtube=None, credentials=None):
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secrets.json"

    if youtube is None or credentials is None:
        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

    body=dict(
        snippet=dict(
            title=title,
            description=description,
            tags=[],
            categoryId='22'
        ),
        status=dict(
            privacyStatus="unlisted"
        )
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=video_file
    )
    response = request.execute()
    print(f"Uploaded video ID: {response.get('id')}")
    return youtube, credentials

def main():
    duration = DURATION + FLASH_DURATION
    total_videos = 1440  # 1 per minute for 24h
    seconds_between = 60

    youtube = None
    credentials = None

    for i in range(total_videos):
        start_time = time.time()
        now = datetime.datetime.now().isoformat()
        print(f"\n[{now}] Starting video {i + 1} of {total_videos}")

        title = random_title()
        description = title
        filename = f"pixel_cross_video_{i+1}.mp4"
        generate_video(filename, duration)
        print(f"[{now}] Generated video: {filename}")

        # Upload
        try:
            youtube, credentials = upload_to_youtube(filename, title, description, youtube, credentials)
        except Exception as e:
            print("YouTube upload failed:", e)
            # Optionally: retry logic or break
        finally:
            if os.path.exists(filename):
                os.remove(filename)

        elapsed = time.time() - start_time
        if elapsed < seconds_between:
            time.sleep(seconds_between - elapsed)

if __name__ == "__main__":
    main()
