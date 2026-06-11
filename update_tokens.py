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
# PANAMERICANA (Dailymotion)
# ==============================
def obtener_panamericana():
    video_id = "xa50i1c"

    url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = r.json()

        m3u8 = data["qualities"]["auto"][0]["url"]

        print("🎯 Panamericana:", m3u8)

        return re.sub(r'live-\d+', 'live-720', m3u8)

    except Exception as e:
        print("❌ Error Panamericana:", e)
        return None


# ==============================
# AMÉRICA TV (MediaStream)
# ==============================
def obtener_america():
    stream_id = "6099b04d9418ac082441dd74"

    url = f"https://mdstrm.com/live-stream/{stream_id}.m3u8"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://tvgo.americatv.com.pe/"
    }

    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = r.url

        print("🎯 America TV:", final_url)

        return final_url

    except Exception as e:
        print("❌ Error America:", e)
        return None


# ==============================
# GITHUB
# ==============================
def obtener_m3u():
    r = requests.get(API_URL, headers=HEADERS)

    print("🔎 GitHub status:", r.status_code)

    data = r.json()

    if "content" not in data:
        print("❌ Error GitHub:", data)
        raise Exception("No se pudo leer el archivo")

    contenido = base64.b64decode(data["content"]).decode()
    return contenido, data["sha"]


def subir(contenido, sha):
    encoded = base64.b64encode(contenido.encode()).decode()

    payload = {
        "message": "Auto update IPTV tokens (America + Panamericana)",
        "content": encoded,
        "sha": sha,
        "branch": "main"
    }

    r = requests.put(API_URL, headers=HEADERS, json=payload)

    print("✅ GitHub update:", r.status_code)
    print(r.text)


# ==============================
# ACTUALIZAR M3U
# ==============================
def actualizar_m3u(contenido, nuevas_urls):

    lineas = contenido.splitlines()
    cambio = False

    for i, linea in enumerate(lineas):

        # PANAMERICANA
        if 'tvg-id="PanamericanaTkns"' in linea:
            if i + 1 < len(lineas) and nuevas_urls.get("panamericana"):
                actual = lineas[i + 1].strip()
                nueva = nuevas_urls["panamericana"]

                if actual != nueva:
                    print("🔄 Panamericana actualizado")
                    lineas[i + 1] = nueva
                    cambio = True
                else:
                    print("✅ Panamericana sin cambios")

        # AMERICA TV
        if 'tvg-id="AmericaTkns"' in linea:
            if i + 1 < len(lineas) and nuevas_urls.get("america"):
                actual = lineas[i + 1].strip()
                nueva = nuevas_urls["america"]

                if actual != nueva:
                    print("🔄 America TV actualizado")
                    lineas[i + 1] = nueva
                    cambio = True
                else:
                    print("✅ America sin cambios")

    return "\n".join(lineas), cambio


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    if not GITHUB_TOKEN:
        raise Exception("❌ Falta GITHUB_TOKEN")

    nuevas_urls = {}

    # Obtener streams
    nuevas_urls["panamericana"] = obtener_panamericana()
    nuevas_urls["america"] = obtener_america()

    print("\n🎯 URLs finales:")
    for k, v in nuevas_urls.items():
        print(k, ":", v)

    contenido, sha = obtener_m3u()

    nuevo_contenido, cambio = actualizar_m3u(contenido, nuevas_urls)

    
    if cambio:
        print("\n🚀 Subiendo cambios...")
        subir(nuevo_contenido, sha)
    else:
        print("\n✅ Nada que actualizar")

