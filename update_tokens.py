import os
import requests
import base64
import re

# Configuración
token = os.getenv("MY_TOKEN")  # lee el token desde el secreto
repo = "srfcer/iptvsrf"
path = "canales.m3u"
url_api = f"https://api.github.com/repos/{repo}/contents/{path}"

# URLs a vigilar
urls_objetivo = [
    "https://live-evg20.tv360.bitel.com.pe/Bah3sYEeFjSg7iF4I_K3kA/1778376747/bitel/America-udp/bitel/America-udp_1080p/chunks.m3u8",
    "https://live-evg20.tv360.bitel.com.pe/L3GEuiSeNitng3XoMDrDsQ/1778377722/bitel/Panamericana-UDP_abr/bitel/Panamericana-udp_720p/chunks.m3u8"
]

pattern = r"tv360\.bitel\.com\.pe/([^/]+/[^/]+)/bitel"

headers = {"Authorization": f"token {token}"}
r = requests.get(url_api, headers=headers)
data = r.json()
sha = data["sha"]
contenido = base64.b64decode(data["content"]).decode()

# Revisar cada URL
nuevo_contenido = contenido
for url in urls_objetivo:
    match = re.search(pattern, url)
    if match:
        token_actual = match.group(1)
        # Aquí deberías obtener la URL real desde la fuente original
        # (ejemplo: requests.get(url) o desde otra API)
        # Simulamos que cambió el token:
        nuevo_token = token_actual  # reemplazar con el token detectado
        if nuevo_token != token_actual:
            # Rearmar URL
            fixed_part = url.split("/bitel/", 1)[1]
            nueva_url = f"https://live-evg20.tv360.bitel.com.pe/{nuevo_token}/bitel/{fixed_part}"
            # Reemplazar en el archivo
            nuevo_contenido = nuevo_contenido.replace(url, nueva_url)

# Si hubo cambios, subir archivo actualizado

r = requests.get(url_api, headers=headers)
data = r.json()

if "sha" not in data:
    print("❌ Error al obtener el archivo:", data)
    exit(1)

sha = data["sha"]


if nuevo_contenido != contenido:
    encoded_content = base64.b64encode(nuevo_contenido.encode()).decode()
    payload = {
        "message": "Actualización automática de tokens en canales.m3u",
        "content": encoded_content,
        "sha": sha
    }
    res = requests.put(url_api, headers=headers, json=payload)
    print(res.json())
else:
    print("✅ No hubo cambios en los tokens")
