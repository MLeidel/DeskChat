# vocvlc.py (module)
# requires openai and mpv player for Linux
# no player is required for Windows
#    VOICES:
#    'alloy','ash','ballad','coral','echo','fable','nova','onyx','sage','shimmer'
#    EXAMPLE:
#    vocvlc.textospeech(key,
#                        'nova',
#                        'speak with a sad voice',
#                        'speech.mp3',
#                        'Hello, this is nova speaking. My cat just died.')
#

import sys
import os
import openai
import subprocess
import platform

def play_file(speech_file_path):
    ''' Play the audio file currently set
    different actions occur based on running OS '''

    if not os.path.exists(speech_file_path):
        print(f"File not found: {speech_file_path}")
        sys.exit()
    else:
        system = platform.system()

        if system == 'Windows':
            vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
            subprocess.Popen([vlc_path, '--play-and-exit', speech_file_path])
        elif system == 'Darwin':  # macOS
            subprocess.Popen(['open', '-a', 'VLC', speech_file_path])
        else:  # Linux
            subprocess.Popen(['vlc', '--play-and-exit', speech_file_path])


def textospeech(mod, key, voc, ins, fou, inp):
    ''' create the audio file
        get parameters from GUI
        mod = OpenAI text to speech model
        key = OpenAI gpt key variable
        voc = voice name
        ins = instructions on how to speak
        fou = name of output audio file (mp3 format)
        inp = text to speak
        and get response from openai
    '''
    speech_file_path = fou

    try:
        # Load the API key from an environment variable or a .env file
        openai.api_key = os.getenv(key)
    except Exception as e:
      print("Could Not Read Key file\n", "Did you enter your Gpt Key?")
      sys.exit()

    try:
        with openai.audio.speech.with_streaming_response.create(
          model=mod,
          voice=voc,
          response_format="mp3",
          instructions=ins,
          input=inp
        ) as response:
          response.stream_to_file(speech_file_path)
          play_file(speech_file_path)
          return 0  # success
    except Exception as e:
        return 2  # problems
