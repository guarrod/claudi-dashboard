#!/usr/bin/env bash
# Instala el hub en el VPS (host ssh "pulsar"). Idempotente; se ejecuta desde la PC:
#     bash deploy/install-vps.sh
# Lee el token de config.json, copia hub.py y collector.py, deja el token solo
# en el servidor (chmod 600), anade el location de nginx (con backup y
# `nginx -t`: si la prueba falla restaura el backup y NO recarga) y arranca el
# hub con pm2.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=${1:-pulsar}
DIR=/var/www/apps/claude-dashboard
NGINX=/etc/nginx/sites-enabled/default   # archivo real en uso (no es symlink; sites-available esta desactualizado)

TOKEN=$(python -c "import json;print(json.load(open('config.json'))['token'])")
[ ${#TOKEN} -ge 24 ] || { echo "token de config.json demasiado corto"; exit 1; }

ssh "$HOST" "mkdir -p $DIR"
scp -q hub.py collector.py "$HOST:$DIR/"

printf '%s' "$TOKEN" | ssh "$HOST" "umask 077; T=\$(cat); cat > $DIR/ecosystem.config.cjs <<EOC
module.exports = {
  apps: [{
    name: 'claude-hub',
    script: './hub.py',
    interpreter: 'python3',
    cwd: '$DIR',
    args: '--host 127.0.0.1 --port 8788 --data $DIR/hub-data',
    instances: 1, autorestart: true, watch: false, exec_mode: 'fork',
    env: { CLAUDE_HUB_TOKEN: '\$T' },
  }],
};
EOC
chmod 600 $DIR/ecosystem.config.cjs"

ssh "$HOST" "CONF=$NGINX bash -s" <<'REMOTE'
set -euo pipefail
# OJO: no llamar NGINX a la variable (nginx la usa para sockets heredados) y el
# backup va FUERA de sites-enabled (nginx incluye todo lo que haya ahi).
if grep -q 'location /claude-hub/' "$CONF"; then echo "nginx: location ya presente"; exit 0; fi
mkdir -p /root/nginx-backups
BAK="/root/nginx-backups/default.bak-claude-hub-$(date +%Y%m%d%H%M%S)"
cp "$CONF" "$BAK"
python3 - "$CONF" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
block = """    # -- Claude Hub (telemetria Claude Code multi-maquina) --
    location = /claude-hub { return 404; }
    location /claude-hub/ {
        limit_except GET POST { deny all; }
        client_max_body_size 9m;
        proxy_pass         http://127.0.0.1:8788/;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

"""
marker = "    listen [::]:443 ssl ipv6only=on;"
assert s.count(marker) == 1, "bloque 443 no encontrado de forma unica"
open(p, "w").write(s.replace(marker, block + marker))
PY
if nginx -t; then systemctl reload nginx && echo "nginx recargado"; else cp "$BAK" "$CONF"; echo "nginx -t fallo: backup restaurado"; exit 1; fi
REMOTE

ssh "$HOST" "cd $DIR && (pm2 describe claude-hub >/dev/null 2>&1 && pm2 restart claude-hub --update-env || pm2 start ecosystem.config.cjs) && pm2 save >/dev/null"
sleep 2
URL=$(python -c "import json;print(json.load(open('config.json'))['url'])")
curl -fsS "$URL/healthz" && echo && echo "hub OK en $URL"
