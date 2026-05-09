import os
import requests
import base64
import re
import sys

# Configuración
token = os.getenv("MY_TOKEN")  # El token se pasa como variable de entorno desde GitHub Secrets
repo = "srfcer/iptvsrf"
path = "canales.m3u"
url_api = f"https://api.github.com/repos/{repo}/contents/{path}"

# URLs a vigilar
urls_objetivo = [
    "https://live-evg20.tv360.bitel.com.pe/Bah3sYEeFjSg7iF4I_K3kA/1778376747/bitel/America-udp/bitel/America-udp_1080p/chunks.m3u8",
    "https://live-evg20.tv360.bitel.com.pe/L3GEuiSeNitng3XoMDrDsQ/1778377722/bitel/Panamericana-UDP_abr/bitel/Panamericana-udp_720p/chunks.m3u8"
]

pattern = r"tv360\.bitel\.com\.pe/([^/]+/[^/]+)/bitel"

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
    match = re.search(pattern, url)
    if match:
        token_actual = match.group(1)
        # Aquí deberías obtener el token nuevo desde la fuente original
        # Por ahora simulamos que sigue igual
        nuevo_token = token_actual

        if nuevo_token != token_actual:
            fixed_part = url.split("/bitel/", 1)[1]
            nueva_url = f"https://live-evg20.tv360.bitel.com.pe/{nuevo_token}/bitel/{fixed_part}"
            nuevo_contenido = nuevo_contenido.replace(url, nueva_url)
            print(f"🔄 Token actualizado en: {url}")
        else:
            print(f"✅ Token sin cambios en: {url}")
    else:
        print(f"⚠️ No se encontró token en la URL: {url}")

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
