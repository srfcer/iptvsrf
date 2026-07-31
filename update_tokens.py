import os
import base64
import requests
import re

from playwright.sync_api import sync_playwright


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
# PANAMERICANA
# ==============================
def obtener_panamericana():

    stream = None

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        
        def on_request(request):
        
            nonlocal stream
        
            url = request.url
        
            if (
                "dmcdn.net" in url
                and ".m3u8" in url
                and "live-" in url
                and "xa50i1c" in url
            ):
        
                stream = re.sub(
                    r"live-\d+",
                    "live-720",
                    url
                )
        
                print("🎯 STREAM 720:")
                print(stream)
                

        page.on("request", on_request)

        print("🔎 Abriendo Panamericana...")

        page.goto(
            "https://panamericana.pe/tvenvivo",
            wait_until="networkidle"
        )

        page.wait_for_timeout(15000)

        browser.close()

    return stream


# ==============================
# GITHUB
# ==============================
def obtener_m3u():

    r = requests.get(
        API_URL,
        headers=HEADERS
    )

    print("🔎 GitHub status:", r.status_code)

    data = r.json()

    if "content" not in data:
        print(data)
        raise Exception("Error leyendo GitHub")

    contenido = base64.b64decode(
        data["content"]
    ).decode()

    return contenido, data["sha"]


def subir(contenido, sha):

    payload = {
        "message": "Auto update Panamericana token",
        "content": base64.b64encode(
            contenido.encode()
        ).decode(),
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

            print("➡️ URL actual:")
            print(actual)

            print("➡️ URL nueva:")
            print(nueva_url)

            if actual == nueva_url:
                print("✅ Sin cambios")
                return contenido, False

            print("🔄 Actualizando URL...")

            lineas[i + 1] = nueva_url

            return "\n".join(lineas), True

    print("⚠️ No se encontró PanamericanaTkns")

    return contenido, False


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    if not GITHUB_TOKEN:
        raise Exception("❌ Falta GITHUB_TOKEN")

    nueva_url = obtener_panamericana()

    if not nueva_url:
        raise Exception(
            "❌ No se pudo obtener la URL de Panamericana"
        )

    contenido, sha = obtener_m3u()

    nuevo_contenido, cambio = actualizar_m3u(
        contenido,
        nueva_url
    )

    if cambio:
        print("\n🚀 Subiendo cambios...")
        subir(
            nuevo_contenido,
            sha
        )
    else:
        print("\n✅ Nada que actualizar")
