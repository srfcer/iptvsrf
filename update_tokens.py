import os
import requests
import base64
import re
import sys

# Configuración: usamos el GITHUB_TOKEN automático
token = os.getenv("GITHUB_TOKEN")
repo = "srfcer/iptvsrf"
path = "canales.m3u"
url_api = f"https://api.github.com/repos/{repo}/contents/{path}"

# URLs a vigilar
urls_objetivo = [
    "https://live-evg20.tv360.bitel.com.pe/Bah3sYEeFjSg7iF4I_K3kA/1778376747/bitel/America-udp/bitel/America-udp_1080p/chunks.m3u8",
    "https://live-evg20.tv360.bitel.com.pe/L3GEuiSeNitng3XoMDrDsQ/1778377722/bitel/Panamericana-UDP_abr/bitel/Panamericana-udp_720p/chunks.m3u8",
    "https://live2.eu-north-1a.cf.dmcdn.net/sec2(j47xu9S2Z8Yf3sbZOi9QiQfnhkOJPNjRvA3kJ45T9ncoAQ2kQD8rjBpynNVpRpx3ZN5L6NySm2BLvcDGEUQS-kxzj8WLe_ks8rMhVgXkiV8Qxn_6bjwQQJpMF8Rju_Vr)/cloud/3/x80ac48/d/live-720.m3u8"
]

patterns = {
    "bitel": r"tv360\.bitel\.com\.pe/([^/]+/[^/]+)/bitel",
    "dmcdn": r"sec2\(([^)]+)\)"
}

# Obtener contenido actual del archivo en GitHub
headers = {"Authorization": f"token {token}"}
r = requests.get(url_api, headers=headers)

if r.status_code != 200:
    print(f"❌ Error al obtener el archivo desde GitHub. Código: {r.status_code}")
    print("Respuesta:", r.text)
    sys.exit(1)

data = r.json()
if "sha" not in data or "content" not in data:
    print("❌ La respuesta de la API no contiene el archivo esperado.")
    print("Respuesta:", data)
    sys.exit(1)

sha = data["sha"]
contenido = base64.b64decode(data["content"]).decode()
nuevo_contenido = contenido

# Revisar cada URL
for url in urls_objetivo:
    if "bitel.com.pe" in url:
        match = re.search(patterns["bitel"], url)
    elif "dmcdn.net" in url:
        match = re.search(patterns["dmcdn"], url)
    else:
        match = None

    if match:
        token_actual = match.group(1)
        # Aquí deberías obtener el token nuevo desde la fuente original
        nuevo_token = token_actual  # simulado
        if nuevo_token != token_actual:
            if "bitel.com.pe" in url:
                fixed_part = url.split("/bitel/", 1)[1]
                nueva_url = f"https://live-evg20.tv360.bitel.com.pe/{nuevo_token}/bitel/{fixed_part}"
            else:
                fixed_part = url.split(")/", 1)[1]
                nueva_url = f"https://live2.eu-north-1a.cf.dmcdn.net/sec2({nuevo_token})/{fixed_part}"
            nuevo_contenido = nuevo_contenido.replace(url, nueva_url)
            print(f"🔄 Token actualizado en: {url}")
        else:
            print(f"✅ Token sin cambios en: {url}")
    else:
        print(f"⚠️ No se encontró token en: {url}")

# Si hubo cambios, subir archivo actualizado
if nuevo_contenido != contenido:
    encoded_content = base64.b64encode(nuevo_contenido.encode()).decode()
    payload = {
        "message": "Actualización automática de tokens en canales.m3u",
        "content": encoded_content,
        "sha": sha
    }
    res = requests.put(url_api, headers=headers, json=payload)

    if res.status_code in (200, 201):
        print("✅ Archivo actualizado correctamente en GitHub.")
    else:
        print(f"❌ Error al actualizar el archivo. Código: {res.status_code}")
        print("Respuesta:", res.text)
else:
    print("ℹ️ No hubo cambios en los tokens, no se actualizó el archivo.")
