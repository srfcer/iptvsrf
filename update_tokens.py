import requests
import base64
import re
import os

# ==============================
# CONFIG
# ==============================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "srfcer/iptvsrf"
PATH = "canales.m3u"

API_URL = f"https://api.github.com/repos/{REPO}/contents/{PATH}"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# ==============================
# OBTENER STREAM (Dailymotion API)
# ==============================
def obtener_stream():
    video_id = "xa50i1c"

    url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        m3u8 = data["qualities"]["auto"][0]["url"]

        print("🎯 Detectado:", m3u8)

        # ✅ Forzar 720p
        return re.sub(r'live-\d+', 'live-720', m3u8)

    except Exception as e:
        print("❌ Error obteniendo stream:", e)
        return None


# ==============================
# GITHUB
# ==============================

def obtener_m3u():
    r = requests.get(API_URL, headers=HEADERS)

    print("🔎 GitHub status:", r.status_code)
    print("📂 URL:", API_URL)

    data = r.json()

    if "content" not in data:
        print("❌ Error GitHub:", data)
        raise Exception("No se pudo leer el archivo")

    return base64.b64decode(data["content"]).decode(), data["sha"]


def subir(contenido, sha):
    encoded = base64.b64encode(contenido.encode()).decode()

    payload = {
        "message": "Update Panamericana token auto",
        "content": encoded,
        "sha": sha,
        "branch": "main"   # ✅ ESTO SOLUCIONA EL 404
    }

    r = requests.put(API_URL, headers=HEADERS, json=payload)

    print("✅ GitHub update:", r.status_code)
    print(r.text)


# ==============================
# ACTUALIZAR M3U
# ==============================
def actualizar_m3u(contenido, nueva_url):

    lineas = contenido.splitlines()

    for i, linea in enumerate(lineas):

        if 'tvg-id="PanamericanaTkns"' in linea:

            print("✅ Canal encontrado")

            if i + 1 < len(lineas):

                actual_url = lineas[i + 1].strip()

                print("➡️ URL actual:", actual_url)
                print("➡️ URL nueva :", nueva_url)

                if actual_url == nueva_url:
                    print("✅ No hay cambios")
                    return contenido, False

                print("🔄 Actualizando URL...")
                lineas[i + 1] = nueva_url

                return "\n".join(lineas), True

    print("⚠️ No se encontró el canal")
    return contenido, False


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    if not GITHUB_TOKEN:
        raise Exception("❌ Falta GITHUB_TOKEN")

    nueva_url = obtener_stream()

    if not nueva_url:
        print("❌ No se detectó stream")
        exit()

    print("\n🎯 URL FINAL:", nueva_url)

    contenido, sha = obtener_m3u()

    nuevo_contenido, cambio = actualizar_m3u(contenido, nueva_url)

    if cambio:
        print("\n🚀 Subiendo cambios...")
        subir(nuevo_contenido, sha)
    else:
        print("\n✅ Nada que actualizar")
