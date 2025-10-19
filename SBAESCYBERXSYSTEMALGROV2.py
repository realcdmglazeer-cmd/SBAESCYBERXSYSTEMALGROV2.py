import os
import random
import time
import logging
from moviepy.editor import ColorClip, concatenate_videoclips, AudioFileClip
from pydub import AudioSegment
from pydub.generators import Sine

# ============ USER CONFIGURATION ============
YOUTUBE_CLIENT_SECRETS = "client_secrets.json"      # replace with your actual client secrets file path
YOUTUBE_CREDENTIALS = "youtube_credentials.json"    # replace with your actual credentials file path
RESOLUTION = (1280, 720)
VIDEO_DURATION = 25
FIRST_PHASE_DURATION = 16
SECOND_PHASE_DURATION = 9
FPS = 30

# Block/shade unicode alphabet a-z, 's' is the last character in the set
BLOCK_ALPHABET = [
    '▀','▁','▂','▃','▄','▅','▆','▇','█','▉','▊','▋','▌','▍','▎','▏','▐','░','▒','▔','▕','▙','▚','▛','▜','▟'
]
# 's' for ending (as per user request)
BLOCK_S = 's'

logging.basicConfig(
    filename='video_uploader.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def upload_to_youtube(video_path, title, description):
    try:
        command = (
            f'youtube-upload '
            f'--client-secrets="{YOUTUBE_CLIENT_SECRETS}" '
            f'--credentials-file="{YOUTUBE_CREDENTIALS}" '
            f'--title="{title}" '
            f'--description="{description}" '
            f'"{video_path}"'
        )
        result = os.system(command)
        if result != 0:
            logging.error(f"Upload failed for {video_path}")
        else:
            logging.info(f"Uploaded {video_path} successfully")
    except Exception as e:
        logging.error(f"Error uploading to YouTube: {e}")

def random_color():
    return tuple(random.randint(0,255) for _ in range(3))

def generate_beep(frequency, duration):
    try:
        return Sine(frequency).to_audio_segment(duration=duration*1000)
    except Exception as e:
        logging.error(f"Error generating beep: {e}")
        return AudioSegment.silent(duration=duration*1000)

def generate_audio():
    try:
        audio = AudioSegment.silent(duration=VIDEO_DURATION*1000)
        for start in range(0, FIRST_PHASE_DURATION):
            freq = random.randint(521, 2483)
            beep = generate_beep(freq, 1)
            audio = audio.overlay(beep, position=start*1000)
        t = FIRST_PHASE_DURATION
        while t < VIDEO_DURATION:
            freq = random.randint(521, 2483)
            beep = generate_beep(freq, 0.3)
            audio = audio.overlay(beep, position=int(t*1000))
            t += 0.3
        audio.export("temp_audio.wav", format="wav")
        return "temp_audio.wav"
    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        return None

def generate_video():
    try:
        color1 = random_color()
        clip1 = ColorClip(size=RESOLUTION, color=color1, duration=FIRST_PHASE_DURATION)
        clips = []
        for i in range(SECOND_PHASE_DURATION * FPS):
            color = random_color()
            clips.append(ColorClip(size=RESOLUTION, color=color, duration=1/FPS))
        clip2 = concatenate_videoclips(clips)
        final_clip = concatenate_videoclips([clip1, clip2])
        audio_path = generate_audio()
        if not audio_path or not os.path.exists(audio_path):
            logging.error("Audio file not generated, skipping this video.")
            return None
        final_clip = final_clip.set_audio(AudioFileClip(audio_path))
        outname = f"video_{random.randint(100000,999999)}.mp4"
        final_clip.write_videofile(outname, fps=FPS, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        os.remove(audio_path)
        return outname
    except Exception as e:
        logging.error(f"Error generating video: {e}")
        if os.path.exists("temp_audio.wav"):
            try:
                os.remove("temp_audio.wav")
            except Exception as rm_e:
                logging.warning(f"Error removing temp audio: {rm_e}")
        return None

def random_block6():
    # 5 random from the block alphabet, end with 's'
    chars = random.choices(BLOCK_ALPHABET, k=5)
    chars.append(BLOCK_S)
    return ''.join(chars)

def main():
    i = 0
    while True:
        try:
            video_path = generate_video()
            if not video_path or not os.path.exists(video_path):
                logging.error(f"Video generation failed at index {i}")
                time.sleep(60)
                continue
            title = random_block6()
            description = random_block6()
            upload_to_youtube(video_path, title, description)
            try:
                os.remove(video_path)
            except Exception as e:
                logging.warning(f"Error removing video file {video_path}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in main loop at index {i}: {e}")
        i += 1
        time.sleep(60)

if __name__ == "__main__":
    main()
