import requests
import base64
import re
import os

# CONFIG
TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "srfcer/iptvsrf"
PATH = "canales.m3u"

API = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
HEADERS = {"Authorization": f"token {TOKEN}"}


# ✅ EXTRAER CANAL
def get_channel(url):
    m = re.search(r"/bitel/([^/]+)/bitel", url)
    if m:
        return m.group(1)

    if "dmcdn.net" in url:
        return "dmcdn"

    return None


# ✅ INTENTAR REFRESCAR TOKEN (REAL)
def refresh_url(url):
    try:
        r = requests.get(url, timeout=5, allow_redirects=True)
        if r.status_code == 200:
            return url  # sigue vigente
    except:
        pass

    return None  # muerto → se debe reemplazar


# ✅ BUSCAR TOKEN NUEVO DESDE FUENTE REAL
def buscar_nuevas_urls():
    fuentes = [
        # 👉 AGREGA AQUÍ fuentes reales (muy importante)
        "https://iptv-org.github.io/iptv/languages/spa.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/pe.m3u"
    ]

    resultado = []

    for fuente in fuentes:
        try:
            txt = requests.get(fuente, timeout=10).text
            urls = re.findall(r"https?://[^\s]+\.m3u8", txt)
            resultado.extend(urls)
        except:
            continue

    return resultado


# ✅ OBTENER M3U ACTUAL
def get_m3u():
    r = requests.get(API, headers=HEADERS)
    data = r.json()
    contenido = base64.b64decode(data["content"]).decode()
    return contenido, data["sha"]


# ✅ ACTUALIZAR
def actualizar(contenido, nuevas_urls):
    lineas = contenido.splitlines()

    nuevas_lineas = []

    for linea in lineas:
        if linea.startswith("http"):

            canal_actual = get_channel(linea)

            # 1️⃣ verificar si sigue vivo
            url_ok = refresh_url(linea)

            if url_ok:
                nuevas_lineas.append(linea)
                continue

            # 2️⃣ buscar reemplazo
            reemplazado = False

            for nueva in nuevas_urls:
                canal_nuevo = get_channel(nueva)

                if canal_actual and canal_actual == canal_nuevo:
                    print(f"🔄 Reemplazado: {canal_actual}")
                    nuevas_lineas.append(nueva)
                    reemplazado = True
                    break

            if not reemplazado:
                nuevas_lineas.append(linea)

        else:
            nuevas_lineas.append(linea)

    return "\n".join(nuevas_lineas)


# ✅ SUBIR A GITHUB
def upload(contenido, sha):
    encoded = base64.b64encode(contenido.encode()).decode()

    payload = {
        "message": "Auto update tokens IPTV",
        "content": encoded,
        "sha": sha
    }

    r = requests.put(API, headers=HEADERS, json=payload)
    print("GitHub:", r.status_code)


# MAIN
contenido, sha = get_m3u()

print("🔎 Buscando nuevas URLs...")
nuevas_urls = buscar_nuevas_urls()

nuevo = actualizar(contenido, nuevas_urls)

if nuevo != contenido:
    print("🚀 Subiendo cambios...")
    upload(nuevo, sha)
else:
    print("✅ Nada que actualizar")
``
