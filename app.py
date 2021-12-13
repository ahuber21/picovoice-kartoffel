#
# Copyright 2020-2021 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

import argparse
import os
import sys
import struct
import wave
from threading import Thread
from dotenv import load_dotenv

import numpy as np
from picovoice import Picovoice
from pvrecorder import PvRecorder


class PicovoiceApp(Thread):
    def __init__(
            self,
            access_key,
            audio_device_index,
            keyword_path,
            context_path,
            porcupine_library_path=None,
            porcupine_model_path=None,
            porcupine_sensitivity=0.5,
            rhino_library_path=None,
            rhino_model_path=None,
            rhino_sensitivity=0.5,
            require_endpoint=True,
            output_path=None):
        super().__init__()

        self._picovoice = Picovoice(
            access_key=access_key,
            keyword_path=keyword_path,
            wake_word_callback=self._wake_word_callback,
            context_path=context_path,
            inference_callback=self._inference_callback,
            porcupine_library_path=porcupine_library_path,
            porcupine_model_path=porcupine_model_path,
            porcupine_sensitivity=porcupine_sensitivity,
            rhino_library_path=rhino_library_path,
            rhino_model_path=rhino_model_path,
            rhino_sensitivity=rhino_sensitivity,
            require_endpoint=require_endpoint)

        self.audio_device_index = audio_device_index
        self.output_path = output_path

    @staticmethod
    def _wake_word_callback():
        print('[wake word]\n')

    @staticmethod
    def _inference_callback(inference):
        if inference.is_understood:
            print('{')
            print("  intent : '%s'" % inference.intent)
            print('  slots : {')
            for slot, value in inference.slots.items():
                print("    %s : '%s'" % (slot, value))
            print('  }')
            print('}\n')
        else:
            print("Didn't understand the command.\n")

    def run(self):
        recorder = None
        wav_file = None

        try:
            recorder = PvRecorder(device_index=self.audio_device_index, frame_length=self._picovoice.frame_length)
            recorder.start()

            if self.output_path is not None:
                wav_file = wave.open(self.output_path, "w")
                wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))

            print(f"Using device: {recorder.selected_device}")
            print('[Listening ...]')

            while True:
                pcm = recorder.read()

                if wav_file is not None:
                    wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

                self._picovoice.process(pcm)
        except KeyboardInterrupt:
            sys.stdout.write('\b' * 2)
            print('Stopping ...')
        finally:
            if recorder is not None:
                recorder.delete()

            if wav_file is not None:
                wav_file.close()

            self._picovoice.delete()

    @classmethod
    def show_audio_devices(cls):
        devices = PvRecorder.get_audio_devices()

        for i in range(len(devices)):
            print(f'index: {i}, device name: {devices[i]}')


def main():
    if not os.getenv("AUDIO_DEVICE_INDEX"):
        PicovoiceApp.show_audio_devices()
        print("Please select a device from the above list and add its index as AUDIO_DEVICE_INDEX to your .env file")
    else:
        PicovoiceApp(
            access_key=os.environ["ACCESS_KEY"],
            audio_device_index=int(os.environ["AUDIO_DEVICE_INDEX"]),
            keyword_path=cwd(os.environ["KEYWORD_FILE_PATH"]),
            context_path=cwd(os.environ["CONTEXT_FILE_PATH"]),
            porcupine_model_path=cwd(os.environ["PORCUPINE_MODEL_FILE_PATH"]),
            porcupine_sensitivity=0.5,
            rhino_model_path=cwd(os.environ["RHINO_MODEL_FILE_PATH"]),
            rhino_sensitivity=0.5,
            # require_endpoint=require_endpoint,
            output_path=None).run()


def cwd(relative):
   return os.path.join(os.getcwd(), relative)


if __name__ == '__main__':
    load_dotenv()
    main()
