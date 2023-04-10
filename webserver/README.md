# MHK Mods Webserver

This is the (very simple) FastAPI + Flask MHK mods webserver.

You can access it live at [https://mhk-mods.svit.ac](https://mhk-mods.svit.ac).

API documentation is available at [https://mhk-mods.svit.ac/api/docs](https://mhk-mods.svit.ac/api/docs).

## Running it locally

1. Copy config files from `conf.d`
2. Install Python 3.6+ requirements: `pip install -r requirements.txt`
3. `service mhkmods start` if running via systemd, or simply `./start.sh`

The webserver runs as a Unix `.sock` socket file. You can connect it to a webserver such as [Caddy](https://caddyserver.com) to make it publicly available.
