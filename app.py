import os
from picovoice import Picovoice
from dotenv import load_dotenv

def wake_word_callback():
    # wake word detected
    pass

def inference_callback(inference):
   if inference.is_understood:
      intent = inference.intent
      slots = inference.slots
      print("UNDERSTOOD")
      print(inference)
   else:
      print("NOT UNDERSTOOD")
      pass

def cwd(relative):
   return os.path.join(os.getcwd(), relative)

if __name__ == "__main__":
   load_dotenv()
   handle = Picovoice(
      access_key=cwd(os.environ["ACCESS_KEY"]),
      keyword_path=cwd(os.environ["KEYWORD_FILE_PATH"]),
      wake_word_callback=wake_word_callback,
      context_path=cwd(os.environ["CONTEXT_FILE_PATH"]),
      inference_callback=inference_callback,
      porcupine_model_path=cwd(os.environ["PORCUPINE_MODEL_FILE_PATH"]),
      rhino_model_path=cwd(os.environ["RHINO_MODEL_FILE_PATH"]))