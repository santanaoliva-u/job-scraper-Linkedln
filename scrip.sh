#!/bin/bash

# Instalador profesional para Firefox Developer Edition + perfil de Bug Bounty en Arch Linux

set -e

# 1. Verificar yay
if ! command -v yay &>/dev/null; then
  echo "[!] 'yay' no encontrado. Instálalo antes de ejecutar este script."
  exit 1
fi

# 2. Instalar Firefox Developer Edition
echo "[+] Instalando Firefox Developer Edition..."
yay -S --noconfirm firefox-developer-edition firefox-developer-edition-i18n-es-mx

# 3. Crear perfil personalizado
PROFILE_NAME="pentesting"
echo "[+] Creando perfil '$PROFILE_NAME'..."
firefox-developer-edition --no-remote -CreateProfile "$PROFILE_NAME"

# 4. Instrucciones visuales
echo -e "\n📦 Extensiones recomendadas para instalar manualmente:\n"

cat <<EOF
🔧 Extensiones esenciales para Bug Bounty (instálalas manualmente en Firefox):

--- Fingerprinting / Recon ---
1. Wappalyzer ➤ https://addons.mozilla.org/en-US/firefox/addon/wappalyzer/
2. BuiltWith ➤ https://addons.mozilla.org/en-US/firefox/addon/builtwith-technology-profiler/

--- Inyección / Fuzzing ---
3. HackTools ➤ https://addons.mozilla.org/en-US/firefox/addon/hacktools/
4. RESTED ➤ https://addons.mozilla.org/en-US/firefox/addon/rested/
5. XSS Me ➤ https://addons.mozilla.org/en-US/firefox/addon/xss-me/
6. Tamper Data ➤ https://addons.mozilla.org/en-US/firefox/addon/tamper-data/

--- Manipulación de Headers ---
7. ModHeader ➤ https://addons.mozilla.org/en-US/firefox/addon/modheader-firefox/
8. Modify Headers ➤ https://addons.mozilla.org/en-US/firefox/addon/modify-headers/
9. User-Agent Switcher ➤ https://addons.mozilla.org/en-US/firefox/addon/user-agent-string-switcher/

--- Cookies / Sessions ---
10. Cookie Editor ➤ https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/
11. EditThisCookie ➤ https://addons.mozilla.org/en-US/firefox/addon/editthiscookie/
12. Cookies Manager+ ➤ https://addons.mozilla.org/en-US/firefox/addon/cookies-manager-plus/

--- JWT / OAuth ---
13. JWT Debugger ➤ https://addons.mozilla.org/en-US/firefox/addon/jwt-debugger/
14. OAuth 2.0 Playground ➤ https://chrome.google.com/webstore/detail/oauth-20-playground/...

--- Dev / Intercept ---
15. Web Developer ➤ https://addons.mozilla.org/en-US/firefox/addon/web-developer/
16. Live HTTP Headers ➤ https://addons.mozilla.org/en-US/firefox/addon/live-http-headers/
17. Firebug Lite ➤ https://addons.mozilla.org/en-US/firefox/addon/firebug-lite/

--- WebSocket Testing ---
18. WebSocket King Client ➤ https://addons.mozilla.org/en-US/firefox/addon/websocket-client/
19. HTTP Toolkit (versión web) ➤ https://httptoolkit.tech

--- CSRF / Forms ---
20. Form Fuzzer ➤ https://addons.mozilla.org/en-US/firefox/addon/form-fuzzer/
21. Auto Fill Forms ➤ https://addons.mozilla.org/en-US/firefox/addon/autofill-forms-e10s/

--- CSP / CORS Bypass ---
22. Disable CSP ➤ https://addons.mozilla.org/en-US/firefox/addon/disable-csp/
23. CORS Everywhere ➤ https://addons.mozilla.org/en-US/firefox/addon/cors-everywhere/

--- Anti-fingerprint ---
24. CanvasBlocker ➤ https://addons.mozilla.org/en-US/firefox/addon/canvasblocker/
25. Random User-Agent ➤ https://addons.mozilla.org/en-US/firefox/addon/random-user-agent/

---

✅ Firefox Developer Edition instalado.
✅ Perfil '$PROFILE_NAME' creado.
⚠️ Abre Firefox con el siguiente comando para configurarlo manualmente:

firefox-developer-edition --no-remote -P "$PROFILE_NAME"

💡 Recuerda: configura tu proxy (127.0.0.1:8080), importa el certificado de Burp Suite, y ajusta about:config para evitar el caché.
EOF
