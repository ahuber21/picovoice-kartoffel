import os
import sys
import struct
import time
import wave
from threading import Thread
from dotenv import load_dotenv

import numpy as np
from picovoice import Picovoice
from pvrecorder import PvRecorder

from lib.deconz import (
    KaffeeBarGui,
    Kaffeemaschine,
    Lights,
    Neon,
    Weihnachtsstern,
)

gui = KaffeeBarGui()
coffee_machine = Kaffeemaschine()
lights = Lights()
neon = Neon()
weihnachtsstern = Weihnachtsstern()

DEFAULT_AUDIO_DEVICE_NAME = "Built-in Audio Stereo"

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
        output_path=None,
    ):
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
            require_endpoint=require_endpoint,
        )

        self.audio_device_index = audio_device_index
        self.output_path = output_path

    @staticmethod
    def _wake_word_callback():
        print("[wake word]\n")
        gui.show_listening()

    @staticmethod
    def _inference_callback(inference):
        if inference.is_understood:
            gui.done()
            print("{")
            print("  intent : '%s'" % inference.intent)
            print("  slots : {")
            for slot, value in inference.slots.items():
                print("    %s : '%s'" % (slot, value))
            print("  }")
            print("}\n")
            if inference.intent == "changeState":
                if inference.slots["object"] in ("Maschine", "Maschinchen"):
                    # gui.acknowledge()
                    if inference.slots["state"] == "an":
                        coffee_machine.on()
                    elif inference.slots["state"] == "aus":
                        coffee_machine.off()
                elif inference.slots["object"] == "Lichter":
                    if inference.slots["state"] == "an":
                        lights.on()
                        neon.on()
                        weihnachtsstern.on()
                    elif inference.slots["state"] == "aus":
                        lights.off()
                        neon.off()
                        weihnachtsstern.off()
                    elif inference.slots["state"] == "Film":
                        lights.recall_scene("Film")
                    elif inference.slots["state"] == "Frühstück":
                        lights.recall_scene("Frühstück")
                    elif inference.slots["state"] == "Tag":
                        lights.recall_scene("Tag")
                    elif inference.slots["state"] == "Bar":
                        lights.recall_scene("Kaffeebar only")
        else:
            print("Didn't understand the command.\n")
            gui.done()

    def run(self):
        recorder = None
        wav_file = None

        try:
            recorder = PvRecorder(
                device_index=self.audio_device_index,
                frame_length=self._picovoice.frame_length,
            )
            recorder.start()

            if self.output_path is not None:
                wav_file = wave.open(self.output_path, "w")
                wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))

            print(f"Using device: {recorder.selected_device}")
            print("[Listening ...]")

            while True:
                pcm = recorder.read()

                if wav_file is not None:
                    wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

                self._picovoice.process(pcm)

        except KeyboardInterrupt:
            sys.stdout.write("\b" * 2)
            print("Stopping ...")
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
            print(f"index: {i}, device name: {devices[i]}")

    @classmethod
    def get_default_device_index(cls) -> int:
        devices = PvRecorder.get_audio_devices()
        for idx, device in enumerate(devices):
            if device == DEFAULT_AUDIO_DEVICE_NAME or device == "":
                return idx
        raise ValueError(f"No audio device '{DEFAULT_AUDIO_DEVICE_NAME}' found")


def main():
    print("Available audio devices:")
    PicovoiceApp.show_audio_devices()
    idx = os.getenv("AUDIO_DEVICE_INDEX") or PicovoiceApp.get_default_device_index()
    PicovoiceApp(
        access_key=os.environ["ACCESS_KEY"],
        audio_device_index=int(idx),
        keyword_path=cwd(os.environ["KEYWORD_FILE_PATH"]),
        context_path=cwd(os.environ["CONTEXT_FILE_PATH"]),
        porcupine_model_path=cwd(os.environ["PORCUPINE_MODEL_FILE_PATH"]),
        porcupine_sensitivity=0.5,
        rhino_model_path=cwd(os.environ["RHINO_MODEL_FILE_PATH"]),
        rhino_sensitivity=0.5,
        # require_endpoint=require_endpoint,
            output_path=None,
    ).run()


def cwd(relative):
    return os.path.join(os.getcwd(), relative)


if __name__ == "__main__":
    load_dotenv()
    main()
