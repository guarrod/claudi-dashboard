module.exports = {
  apps: [
    {
      name: 'claude-hub',
      script: './hub.py',
      interpreter: 'python3',
      cwd: '/var/www/apps/claude-dashboard',
      instances: 1,
      autorestart: true,
      watch: false,
      exec_mode: 'fork',
      env: {
        // Generar con: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
        // Mejor definirlo fuera del repo: pm2 start ... --update-env con CLAUDE_HUB_TOKEN exportado.
        CLAUDE_HUB_TOKEN: 'cambia-este-token-de-al-menos-24-caracteres',
      },
      args: '--host 127.0.0.1 --port 8788 --data /var/www/apps/claude-dashboard/hub-data',
    },
  ],
};
