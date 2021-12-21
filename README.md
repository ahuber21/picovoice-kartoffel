# Smart home based on picovoice

https://picovoice.ai/docs/quick-start/picovoice-python/

### Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

In order to use the apt-get installed numpy (which does not cause an Illegal Instruction on the Pi Zero W) set up the `PYTHONPATH` like this

```bash
export PYTHONPATH=/usr/lib/python3/dist-packages
```
