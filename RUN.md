# Running the app (any device)

`run.bat` works **outside Cursor** and from any folder: it uses `%~dp0` so it always switches to the project directory first. You can double‑click it in Explorer or run it from a terminal.

## On another Windows PC

1. Copy the whole project folder to the other machine (or clone the repo).
2. Install **Python 3.10+** from [python.org](https://www.python.org/downloads/) (check “Add Python to PATH”).
3. **Optional:** create a venv and install deps:
   ```bat
   cd path\to\lightsapprevamp
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
   If you skip the venv, install globally: `python -m pip install -r requirements.txt`
4. Ensure **backend/data/config.json** exists and has `server_host` and `server_port` (e.g. `127.0.0.1` and `8000`). Copy your existing `backend/data/` (config, devices, presets, etc.) if you already have it set up.
5. Double‑click **run.bat** or run:
   ```bat
   run.bat
   ```
   Or: `python backend\main.py`
6. Open **http://127.0.0.1:8000** (or the host/port in config) in a browser. To use from other devices on the LAN, set `server_host` to `0.0.0.0` in config and use this machine’s IP (e.g. http://192.168.0.5:8000).

## On Linux or macOS

No `.bat` support; use the shell:

```bash
cd /path/to/lightsapprevamp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/main.py
```

Or without venv: `python3 -m pip install -r requirements.txt` then `python3 backend/main.py`.

Use the same **backend/data/config.json** and, for LAN access, `server_host": "0.0.0.0"`.

## Summary

- **run.bat** works outside Cursor; it only needs the project folder and Python.
- On another device: copy the project, install Python + `pip install -r requirements.txt`, keep **backend/data/** (especially **config.json**), then run **run.bat** (Windows) or `python backend/main.py` (any OS).
- For access from other machines, set `server_host` to `0.0.0.0` in **backend/data/config.json**.
