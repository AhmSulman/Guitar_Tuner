# Guitar Tuner

Precision multiplatform guitar tuner — **Windows** and **Android**.

Built with Kivy (Python), YIN pitch detection, 12 tunings, real-time mic display, animated semi-circular gauge.

---

## Run on Windows

```bash
pip install -r requirements.txt
python main.py
```

> **Microphone input** — uses `plyer` for recording on Windows and Android.
>
> `requirements.txt` now includes `plyer` instead of `pyaudio`.

### Microphone permission (Windows 10/11)

If the app shows **"Mic unavailable"**, check:
`Settings → Privacy & security → Microphone → Allow apps to access your microphone → On`

---

## Build Android APK via WSL2 (Ubuntu)

Buildozer runs only on Linux. On Windows, use **WSL2 with Ubuntu**.

### 1 — Set up WSL2 Ubuntu (one-time)

Open PowerShell as Administrator:

```powershell
wsl --install -d Ubuntu
```

Restart when prompted. Ubuntu will open and ask you to set a username/password.

### 2 — Install system dependencies inside Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 python3-pip python3-venv \
    git zip unzip openjdk-17-jdk \
    build-essential libssl-dev libffi-dev \
    libsqlite3-dev zlib1g-dev libbz2-dev \
    libreadline-dev libncurses5-dev \
    autoconf automake libtool
```

### 3 — Install Buildozer and Cython

```bash
pip3 install --user --upgrade buildozer cython
```

Add `~/.local/bin` to PATH if needed:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 4 — Copy the project into WSL2

From **Windows**, the WSL filesystem is at `\\wsl$\Ubuntu\home\<your-user>\`.

Option A — copy via Windows Explorer to `\\wsl$\Ubuntu\home\<user>\Tuner`

Option B — from inside WSL2:

```bash
cp -r /mnt/c/Users/<WindowsUser>/Desktop/Tuner ~/Tuner
```

### 5 — Build the debug APK

```bash
cd ~/Tuner
buildozer android debug
```

First build downloads the Android SDK, NDK, and python-for-android — expect **20–40 minutes**.

The APK lands at:

```text
bin/guitartuner-1.0.0-arm64-v8a-debug.apk
```

### 6 — Deploy to Pixel 10 via ADB

Enable **Developer Options** and **USB Debugging** on the phone, then:

```bash
# Install ADB inside WSL2
sudo apt install -y adb

# Connect phone via USB (or wireless ADB)
adb devices

# Install the APK
adb install bin/guitartuner-1.0.0-arm64-v8a-debug.apk
```

Or copy the APK to Windows and sideload via **Files** app on the phone.

### 7 — Build a release (signed) APK

```bash
buildozer android release
```

You will need a keystore. Generate one:

```bash
keytool -genkey -v -keystore my-release-key.jks \
        -alias guitartuner -keyalg RSA -keysize 2048 -validity 10000
```

---

## File map

| File | Purpose |
| --- | --- |
| `main.py` | App entry point, UI layout, `MicStatusWidget` |
| `gauge.py` | Semi-circular animated needle gauge |
| `pitch.py` | YIN pitch detection (FFT-accelerated) |
| `tunings.py` | 12 tunings, note↔frequency conversion |
| `audio_input.py` | PyAudio wrapper, Bluetooth avoidance |
| `buildozer.spec` | Android APK build config |

---

## Microphone permissions

| Platform | Handling |
| --- | --- |
| Android | Runtime permission request on first launch (`RECORD_AUDIO`). If denied, restart the app and tap **Allow**. |
| Windows | Requires mic access in **Settings → Privacy → Microphone**. App shows a specific error message if blocked. |

---

## Troubleshooting

**`buildozer android debug` fails with Java error** — ensure OpenJDK 17:

```bash
sudo update-alternatives --config java   # select java-17
```

**`adb: command not found` in WSL2** — install it:

```bash
sudo apt install -y adb
```

**App crashes on Android with "audio error"** — test on a real device (not emulator). Emulators often lack audio input support.

**Bluetooth mic detected** — the app warns with an orange dot. Bluetooth HFP mode limits sample rate to 8–16 kHz and reduces detection accuracy. Use a wired or built-in mic for best results.
