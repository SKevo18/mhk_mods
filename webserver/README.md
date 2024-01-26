# MHK Mods Webserver

This is the (very simple) FastAPI + Flask MHK mods webserver.

You can access it live at [https://mhk-mods.svit.ac](https://mhk-mods.svit.ac).

API documentation is available at [https://mhk-mods.svit.ac/api/docs](https://mhk-mods.svit.ac/api).

> **Note:** Mod folders starting with dot (`.`) are marked as WIP/temporary, and will be excluded from the webpage's mod list.

## Running it locally (for development)

1. Copy config files from `conf.d`
2. Install Python 3.6+ virtualenv in `./.venv`: `python3 -m venv .env`
3. Install dependencies: `pip install -r requirements.txt`
4. `service mhkmods start` if running via systemd, or simply `./start.sh`

The webserver runs as a Unix `.sock` socket file.

You can connect it to a webserver such as [Caddy](https://caddyserver.com) to make it publicly available (see [`conf.d/Caddyfile`](https://github.com/SKevo18/mhk_mods/blob/main/webserver/conf.d/Caddyfile)).

Please, follow the [`LICENSE.md`](https://github.com/SKevo18/mhk_mods/blob/main/LICENSE.md) when customizing this!
