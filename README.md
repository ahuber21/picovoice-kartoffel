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


### Set up service

```bash
# as su
cp kartoffel.service /lib/systemd/system/
chmod 644 /lib/systemd/system/kartoffel.service
systemctl daemon-reload
systemctl enable kartoffel.service
systemctl start kartoffel.service
systemctl status kartoffel.service
```
