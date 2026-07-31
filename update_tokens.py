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

    metadata_url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"

    try:
        r = requests.get(
            metadata_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )

        data = r.json()

        # URL inicial entregada por Dailymotion
        m3u8 = data["qualities"]["auto"][0]["url"]

        print("📡 URL inicial:")
        print(m3u8)

        # Descargar contenido del playlist
        playlist = requests.get(
            m3u8,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        ).text

        # Debug opcional
        # print(playlist[:5000])

        # Buscar URL dmcdn real
        match = re.search(
            r'https://live[^"\s]+dmcdn\.net[^"\s]+\.m3u8',
            playlist
        )

        if match:
            url_final = match.group(0)

            url_final = re.sub(
                r'live-\d+',
                'live-720',
                url_final
            )

            print("🎯 Panamericana FINAL:")
            print(url_final)

            return url_final

        print("❌ No se encontró URL dmcdn dentro del playlist")
        return None

    except Exception as e:
        print("❌ Error Panamericana:", e)
        return None


# ==============================
# GITHUB
# ==============================
def obtener_m3u():

    r = requests.get(API_URL, headers=HEADERS)

    print("🔎 GitHub status:", r.status_code)

    data = r.json()

    if "content" not in data:
        print(data)
        raise Exception("Error leyendo GitHub")

    contenido = base64.b64decode(data["content"]).decode()
    return contenido, data["sha"]


def subir(contenido, sha):

    payload = {
        "message": "Auto update Panamericana token",
        "content": base64.b64encode(contenido.encode()).decode(),
        "sha": sha,
        "branch": "main"
    }

    r = requests.put(
        API_URL,
        headers=HEADERS,
        json=payload
    )

    print("✅ GitHub update:", r.status_code)
    print(r.text)


# ==============================
# ACTUALIZAR M3U
# ==============================
def actualizar_m3u(contenido, nueva_url):

    lineas = contenido.splitlines()

    for i, linea in enumerate(lineas):

        if 'tvg-id="PanamericanaTkns"' in linea:

            if i + 1 >= len(lineas):
                return contenido, False

            actual = lineas[i + 1].strip()

            print("➡️ URL actual:", actual)
            print("➡️ URL nueva :", nueva_url)

            if actual == nueva_url:
                print("✅ Panamericana sin cambios")
                return contenido, False

            lineas[i + 1] = nueva_url

            print("🔄 Panamericana actualizado")
            return "\n".join(lineas), True

    print("⚠️ No se encontró tvg-id=\"PanamericanaTkns\"")
    return contenido, False


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    if not GITHUB_TOKEN:
        raise Exception("❌ Falta GITHUB_TOKEN")

    nueva_url = obtener_panamericana()

    if not nueva_url:
        raise Exception("❌ No se pudo obtener la URL de Panamericana")

    contenido, sha = obtener_m3u()

    nuevo_contenido, cambio = actualizar_m3u(
        contenido,
        nueva_url
    )

    if cambio:
        print("\n🚀 Subiendo cambios...")
        subir(nuevo_contenido, sha)
    else:
        print("\n✅ Nada que actualizar")
