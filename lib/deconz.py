import json
import logging
import requests
import time
from threading import Thread, Event

logging.basicConfig(level=logging.INFO)

KEY = "1B9FCFEEF1"
BASE_URL = f"http://192.168.0.214:8081/api/{KEY}/lights"
MIN_BRIGHTNESS = 20


class ShowListeningThread(Thread):
    def __init__(self, gui):
        self.gui = gui
        self.stop = Event()
        self.orig_on = gui.on
        self.orig_bri = gui.bri
        super().__init__()

    def run(self):
        bri = max(MIN_BRIGHTNESS, self.gui.bri)
        while not self.stop.is_set():
            for x in range(2):
                state = {"on": True, "bri": bri + 20*x}
                self.gui.set_state(state)
                time.sleep(0.2)
            for x in reversed(range(1)):
                state = {"on": True, "bri": bri + 20*x}
                self.gui.set_state(state)
                time.sleep(0.2)
        # restore original state
        self.gui.set_state({"on": self.orig_on, "bri": self.orig_bri})
        

class DeconzClient:
    def __init__(self, name):
        r = requests.get(BASE_URL)
        if r.status_code != 200:
            logging.error("Failed to GET current light status")
            return
        data = json.loads(r.text)
        try:
            self._id = [_id for _id, obj in data.items() if obj["name"] == name][0]
        except IndexError:
            logging.error("Failed to find object with name = %s", name)
            self._id = 0
        
    def set_state(self, state):
        url = f"{BASE_URL}/{self._id}/state"
        r = requests.put(url, json=state)
        if r.status_code != 200:
            logging.error("Failed to PUT new light status: %s", json.dumps(state))
            r.raise_for_status()
            return
        logging.info("Updated state to %s", json.dumps(state))

    def _refresh(self):
        url = f"{BASE_URL}/{self._id}"
        r = requests.get(url, timeout=0.025)
        return json.loads(r.text)


class KaffeeBarGui(DeconzClient):
    def __init__(self):
        super().__init__("Kaffeebar")
        self.bri = 0
        self.on = False
        self.refresh()
        self.thread = None

    def refresh(self):
        data = self._refresh()
        self.on = data["state"]["on"] == True
        self.bri = data["state"]["bri"]

    def show_listening(self):
        self.thread = ShowListeningThread(self)
        self.thread.start()

    def done(self):
        logging.info("DONE")
        if self.thread:
            logging.info("Stopping thread")
            self.thread.stop.set()
            self.thread = None
        self.refresh()

    def acknowledge(self):
        assert self.thread is None
        self.refresh()
        orig = {"on": self.on, "bri": self.bri}
        for _ in range(2):
            self.set_state({"on": True, "bri": 110})
            time.sleep(0.25)
            self.set_state({"on": True, "bri": MIN_BRIGHTNESS})
            time.sleep(0.25)
        self.set_state(orig)
        
class Kaffeemaschine(DeconzClient):
    def __init__(self):
        super().__init__("Kaffeemaschine")

    def on(self):
        self.set_state({"on": True})

    def off(self):
        self.set_state({"on": False})


def refresh():
    r = requests.get(BASE_URL)
    if r.status_code != 200:
        logging.error("Failed to GET current light status")
        return

    # convert status to object by parsing the json
    data = json.loads(r.text)

    # find the object for which the script is configured
    try:
        my_id, my_obj = [(_id, obj) for _id, obj in data.items() if obj[ATTRIB] == TARGET][0]
    except:
        logging.error("Failed to find object with %s = %s", ATTRIB, TARGET)
        return

    # nothing to do if the state is off
    if not my_obj["state"]["on"]:
        return

    # repeat if the value has changed
    current_bri = my_obj["state"]["bri"]
    global VALUE
    if current_bri == VALUE:
        logging.debug("current_bri unchanged at %d", current_bri)
        return

    # make the request to set the bri again
    url = f"{BASE_URL}/{my_id}/state"
    r = requests.put(url, json={"on": True, "bri": current_bri})

    if r.status_code != 200:
        logging.error("Failed to PUT current light status")
        r.raise_for_status()
        return
    logging.info("Updated bri to %d", current_bri)
    VALUE = current_bri


if __name__ == "__main__":
    gui = KaffeeBarGui()
    gui.show_listening()
    time.sleep(3)
    gui.done()
    
    
