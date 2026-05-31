# Personal Finance API - Backend

Backend FastAPI para la aplicación de finanzas personales.

## Requisitos

- Python 3.10+
- pip

## Instalación

1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

2. Crear archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

3. Configurar Google OAuth:
   - Ir a [Google Cloud Console](https://console.cloud.google.com/)
   - Crear un proyecto
   - Habilitar Gmail API
   - Crear credenciales (OAuth 2.0)
   - Descargar JSON y guardar como `client_secret.json` en la carpeta `backend/`

## Ejecutar el servidor

```bash
cd app
python main.py
```

El servidor correrá en `http://localhost:8000`

## Documentación API

Una vez el servidor esté corriendo, acceder a:
- `http://localhost:8000/docs` - Swagger UI
- `http://localhost:8000/redoc` - ReDoc

## Estructura

```
backend/
├── app/
│   ├── __init__.py       # App FastAPI
│   ├── config.py         # Configuración
│   ├── database.py       # Setup de BD
│   ├── main.py           # Entry point
│   ├── models/           # SQLAlchemy models
│   ├── routes/           # Endpoints
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic
├── requirements.txt      # Dependencias
└── README.md            # Este archivo
```

## Endpoints principales (Fase 1)

### Auth
- `GET /auth/google/login-url` - Obtener URL de login con Google
- `GET /auth/google/callback` - Callback de OAuth
- `POST /auth/login` - Login simple (desarrollo)

### Sprints
- `POST /sprints` - Crear sprint
- `GET /sprints/{user_id}` - Listar sprints del usuario
- `GET /sprints/{user_id}/active` - Obtener sprint activo

### Transactions
- `POST /transactions` - Crear transacción
- `GET /transactions/{sprint_id}` - Listar transacciones del sprint
- `PATCH /transactions/{transaction_id}/complete` - Completar transacción
- `PATCH /transactions/{transaction_id}/uncomplete` - Descompletar transacción

### Categories
- `POST /categories` - Crear categoría
- `GET /categories/{user_id}` - Listar categorías del usuario

## Próximas fases

- Fase 2: Integración con Gmail
- Fase 3: Detección de consumos
- Fase 4: Notificaciones
- Fase 5: Sincronización con app móvil
