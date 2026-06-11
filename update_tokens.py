from playwright.sync_api import sync_playwright
import requests
import base64
import re
import time
import os

# ==============================
# CONFIG
# ==============================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "srfcer/iptvsrf"
PATH = "canales.m3u"

API_URL = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

stream_detectado = None


# ==============================
# DETECTAR STREAM
# ==============================
def es_stream(url):
    return "live-" in url and "m3u8" in url and "dmcdn.net" in url


def convertir_a_720(url):
    return re.sub(r'live-\d+', 'live-720', url)


def obtener_stream():
    global stream_detectado

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        )

        page.set_extra_http_headers({
            "Accept-Language": "es-ES,es;q=0.9"
        })

        def handle_request(request):
            global stream_detectado
            url = request.url

            if es_stream(url) and stream_detectado is None:
                stream_detectado = url
                print("🎯 Detectado:", url)

        page.on("request", handle_request)

        print("🔎 Abriendo página...")
        page.goto("https://panamericana.pe/tvenvivo", wait_until="load")

        # ✅ simular usuario
        page.mouse.move(500, 400)
        page.mouse.click(500, 400)

        time.sleep(20)

        browser.close()

    if stream_detectado:
        return convertir_a_720(stream_detectado)

    return None

# ==============================
# GITHUB
# ==============================
def obtener_m3u():
    r = requests.get(API_URL, headers=HEADERS)
    data = r.json()

    if "content" not in data:
        print(data)
        raise Exception("Error leyendo GitHub")

    contenido = base64.b64decode(data["content"]).decode()
    return contenido, data["sha"]


def subir(contenido, sha):
    encoded = base64.b64encode(contenido.encode()).decode()

    payload = {
        "message": "Update Panamericana token",
        "content": encoded,
        "sha": sha
    }

    r = requests.put(API_URL, headers=HEADERS, json=payload)

    print("✅ GitHub:", r.status_code)


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

                else:
                    print("🔄 Actualizando URL...")
                    lineas[i + 1] = nueva_url
                    return "\n".join(lineas), True

    print("⚠️ No se encontró el canal")
    return contenido, False


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

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
