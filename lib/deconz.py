import json
import logging
import requests
import time
from threading import Thread, Event

logging.basicConfig(level=logging.INFO)

KEY = "1B9FCFEEF1"
LIGHTS_URL = f"http://192.168.0.214:8081/api/{KEY}/lights"
GROUPS_URL = f"http://192.168.0.214:8081/api/{KEY}/groups"
MIN_BRIGHTNESS = 20


class ShowListeningThread(Thread):
    def __init__(self, gui):
        self.gui = gui
        self.stop = Event()
        self.stop.clear()
        self.orig_on = gui.on
        self.orig_bri = gui.bri
        super().__init__()

    def run(self):
        on = True
        bri = self.orig_bri if self.orig_on else 110
        while not self.stop.is_set():
            on = not on
            self.gui.set_state(on=on, bri=bri)
            time.sleep(0.4)
        # restore original state
        self.gui.set_state(on=self.orig_on, bri=self.orig_bri)


class AcknowledgeThread(Thread):
    def __init__(self, gui):
        self.gui = gui
        super().__init__()

    def run(self):
        orig = {"on": self.gui.on, "bri": self.gui.bri}
        for _ in range(2):
            self.gui.set_state(on=True, bri=110)
            time.sleep(0.2)
            self.gui.set_state(on=True, bri=MIN_BRIGHTNESS)
            time.sleep(0.2)
        self.gui.set_state(**orig)

class DeconzClient:
    def __init__(self, name, url):
        self.url = url
        try:
            r = requests.get(self.url)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize DeconzClient {name} with URL {url}") from e
        if r.status_code != 200:
            logging.error("Failed to GET current light status")
            return
        data = json.loads(r.text)
        try:
            self._id = [_id for _id, obj in data.items() if obj["name"] == name][0]
        except IndexError:
            logging.error("Failed to find object with name = %s", name)
            self._id = 0

    def set_state(self, **kwargs):
        url = f"{self.url}/{self._id}/state"
        r = requests.put(url, json=kwargs)
        if r.status_code != 200:
            logging.error("Failed to PUT new light status: %s", json.dumps(kwargs))
            r.raise_for_status()
            return
        logging.debug("Updated state to %s", json.dumps(kwargs))

    def set_action(self, **kwargs):
        url = f"{self.url}/{self._id}/action"
        r = requests.put(url, json=kwargs)
        if r.status_code != 200:
            logging.error("Failed to PUT new group status: %s", json.dumps(kwargs))
            r.raise_for_status()
            return
        logging.debug("Updated action to %s", json.dumps(kwargs))


    def recall_scene(self, scene_name):
        # need to find the id
        data = self._refresh()
        for scene in data["scenes"]:
            if scene["name"] == scene_name:
                url = f"{self.url}/{self._id}/scenes/{scene['id']}/recall"
                r = requests.put(url, timeout=2)
                if r.status_code != 200:
                    logging.error("Failed to PUT scene: %s", scene_name)
                    r.raise_for_status()
                    return
                logging.debug("Updated scene to %s", scene_name)

    def _refresh(self):
        url = f"{self.url}/{self._id}"
        r = requests.get(url, timeout=2)
        return json.loads(r.text)


class KaffeeBarGui(DeconzClient):
    def __init__(self):
        super().__init__("Kaffeebar", LIGHTS_URL)
        self.bri = 0
        self.on = False
        self.refresh()
        self.thread = None

    def refresh(self):
        data = self._refresh()
        self.on = data["state"]["on"] == True
        self.bri = data["state"]["bri"]

    def show_listening(self):
        self.refresh()
        self.thread = ShowListeningThread(self)
        self.thread.start()

    def done(self):
        if self.thread:
            self.thread.stop.set()
            self.thread.join()
            self.thread = None
        self.refresh()

    def acknowledge(self):
        assert self.thread is None
        self.refresh()
        self.thread = AcknowledgeThread(self)
        self.thread.start()

class Kaffeemaschine(DeconzClient):
    def __init__(self):
        super().__init__("Kaffeemaschine", LIGHTS_URL)

    def on(self):
        self.set_state(on=True)

    def off(self):
        self.set_state(on=False)


class Lights(DeconzClient):
    def __init__(self):
        super().__init__("Alle Lichter", GROUPS_URL)

    def on(self):
        self.set_action(on=True)

    def off(self):
        self.set_action(on=False)

    def scene(self, scene_name):
        self.recall_scene(scene_name)

class Neon(DeconzClient):
    def __init__(self):
        super().__init__("Neon", GROUPS_URL)

    def on(self):
        self.set_action(on=True)

    def off(self):
        self.set_action(on=False)

class Weihnachtsstern(DeconzClient):
    def __init__(self):
        super().__init__("Weihnachtsstern", LIGHTS_URL)

    def on(self):
        self.set_state(on=True)

    def off(self):
        self.set_state(on=False)


if __name__ == "__main__":
    lights = Lights()
    lights.off()
