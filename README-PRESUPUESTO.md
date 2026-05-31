# Presupuesto - App de Finanzas Personales

Aplicación completa de gestión de finanzas personales con React Native (iOS) y FastAPI backend.

## Características Principales

✅ **Sprints Quincenales:** Divide tu mes en 2 sprints (cada 15 días)
✅ **Gastos Fijos y Variables:** Crea plantillas de gastos reutilizables
✅ **Rastreo Dual:** Controla banco principal y efectivo por separado
✅ **Marcar Completados:** Toggle con checkbox o slide para marcar gastos
✅ **Cálculo de Disponible:** Recalcula automáticamente tu saldo disponible
✅ **Integración Gmail:** Lee estados de cuenta y detecta consumos (próximamente)
✅ **Temas Light/Dark:** Personaliza tu interfaz
✅ **Notificaciones:** Confirma consumos detectados antes de completarlos

## Tecnología

### Backend
- **FastAPI** (Python 3.10+)
- **SQLAlchemy** (ORM)
- **SQLite/PostgreSQL** (Base de datos)
- **Google OAuth 2.0** (Integración Gmail)

### Frontend
- **React Native** + **Expo** (iOS)
- **Redux Toolkit** (Estado global)
- **React Navigation** (Navegación)
- **Axios** (Cliente HTTP)

## Estructura del Proyecto

```
presupuesto/
├── backend/                  # Servidor FastAPI
│   ├── app/
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── routes/          # Endpoints API
│   │   ├── config.py        # Configuración
│   │   └── database.py      # Setup BD
│   ├── requirements.txt      # Dependencias Python
│   └── README.md
│
├── frontend/                 # App React Native
│   ├── src/
│   │   ├── screens/         # Pantallas (Auth, Dashboard, Sprint, Settings)
│   │   ├── navigation/      # Navegadores
│   │   ├── redux/           # Estado global
│   │   ├── config/          # Configuración
│   │   └── services/        # Servicios (API calls)
│   ├── package.json
│   ├── app.json            # Config Expo
│   └── README.md
│
└── README-PRESUPUESTO.md    # Este archivo
```

## Instalación y Setup

### 1. Backend

```bash
# Navegar a backend
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
cp .env.example .env

# Configurar Google OAuth
# 1. Ir a: https://console.cloud.google.com/
# 2. Crear proyecto
# 3. Habilitar Gmail API
# 4. Crear credenciales OAuth 2.0
# 5. Descargar JSON como client_secret.json en carpeta backend/

# Ejecutar servidor
cd app
python main.py
```

El servidor correrá en `http://localhost:8000`

Documentación API disponible en: `http://localhost:8000/docs`

### 2. Frontend

```bash
# Navegar a frontend
cd frontend

# Instalar dependencias
npm install

# Ejecutar en iOS Simulator
npm run ios

# O ejecutar con Expo Go en dispositivo real
npm start
```

## Guía de Uso Básico

### Crear un Sprint

1. El app crea automáticamente 2 sprints quincenales cada mes
2. Ve a Dashboard para ver el sprint activo
3. Duración: Día 1-15 y Día 16-último día del mes

### Agregar Gastos

1. Ve a la pantalla **Sprint**
2. Crea gastos nuevos o usa **plantillas fijas**
3. Define: concepto, monto, categoría, cuenta (Banco/Efectivo)

### Marcar Completados

1. En la lista de gastos, usa **checkbox** o **slide** (configurable)
2. El saldo disponible se recalcula automáticamente
3. Color gris indica completado

### Configuración

En la pantalla **Configuración** puedes:
- Cambiar tema (Light/Dark/Sistema)
- Elegir método de completación (Checkbox/Slide/Ambos)
- Activar/desactivar confirmación manual
- Crear categorías personalizadas

## Flujo Típico de Uso

### Inicio de Quincena (Día 1 o 15)

```
1. App crea sprint automático
2. Opción: Importar gastos fijos de mes anterior
3. Agrega gastos variables nuevos
4. Saldo disponible se calcula: saldo_actual - gastos_completados
```

### Durante el Sprint

```
1. Revisa emails de banco (próximamente: automático)
2. Si detecta consumo: notificación → confirma o descarta
3. Marca gastos en efectivo manualmente
4. Ve tu saldo disponible recalcularse en tiempo real
```

### Fin de Sprint (Día 15 o 30)

```
1. Completa todos los gastos
2. Calcula restante: saldo_actual - todos_gastos_completados
3. Sistema sugiere: "¿Mover $X a ahorros?"
4. Confirma → dinero pasa a ahorros
5. Nuevo sprint comienza
```

## API Endpoints (Fase 1)

### Autenticación
- `POST /auth/login` - Login simple
- `GET /auth/me` - Info usuario actual

### Sprints
- `POST /sprints` - Crear sprint
- `GET /sprints/{user_id}` - Listar sprints
- `GET /sprints/{user_id}/active` - Sprint activo
- `POST /sprints/{user_id}/auto-create` - Crear sprints mensuales
- `PATCH /sprints/{sprint_id}/complete` - Completar sprint

### Transacciones
- `POST /transactions` - Crear transacción
- `GET /transactions/{sprint_id}` - Listar del sprint
- `PATCH /transactions/{id}/complete` - Marcar completada
- `PATCH /transactions/{id}/uncomplete` - Desmarcar
- `DELETE /transactions/{id}` - Eliminar

### Categorías
- `POST /categories` - Crear categoría
- `GET /categories/{user_id}` - Listar
- `PATCH /categories/{id}` - Actualizar
- `DELETE /categories/{id}` - Eliminar

## Próximas Fases

### Fase 2: Integración Gmail
- [ ] OAuth completo con Google
- [ ] Lectura de emails de banco
- [ ] Parser de estados de cuenta
- [ ] Extracción de disponible de tarjetas

### Fase 3: Notificaciones
- [ ] Sistema de notificaciones
- [ ] Detectar consumos automáticamente
- [ ] Pedir confirmación antes de marcar

### Fase 4: Gastos Fijos Avanzados
- [ ] Crear y reutilizar plantillas
- [ ] Importar plantillas de meses anteriores
- [ ] Historial de cambios

### Fase 5: Reportes y Análisis
- [ ] Gráficos de gastos por categoría
- [ ] Comparativas: planeado vs real
- [ ] Exportar datos
- [ ] Historial trimestral/anual

### Fase 6: Sincronización
- [ ] Sincronización real-time app ↔ backend
- [ ] Offline-first capability
- [ ] Backup automático

### Fase 7: Movimiento a Ahorros
- [ ] Cuenta de ahorros
- [ ] Transferencias automáticas al completar sprint
- [ ] Historial de ahorros
- [ ] Proyecciones

## Variables de Entorno

### Backend (.env)

```
GOOGLE_CLIENT_ID=tu_client_id
GOOGLE_CLIENT_SECRET=tu_secret
DATABASE_URL=sqlite:///./presupuesto.db
SECRET_KEY=tu_secret_key_desarrollo
```

### Frontend (.env)

```
EXPO_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend

**Error: "module not found"**
```bash
pip install -r requirements.txt
```

**Error: "Port 8000 already in use"**
```bash
# Cambiar puerto en app/main.py
uvicorn.run(..., port=8001)
```

### Frontend

**Error: "npm install falla"**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Actualizar Expo CLI**
```bash
npm install -g expo-cli@latest
```

## Guía de Desarrollo

### Agregar nuevo endpoint

1. Crear modelo en `backend/app/models/`
2. Crear ruta en `backend/app/routes/`
3. Incluir ruta en `app/__init__.py`
4. Consumir en frontend con `apiClient`

### Agregar nueva pantalla

1. Crear archivo en `frontend/src/screens/`
2. Crear Redux slice si necesita estado global
3. Añadir a navegador en `frontend/src/navigation/`

### Cambios de BD

```bash
# Crear tabla nueva
# 1. Crear modelo en app/models/
# 2. Ejecutar main.py (crea tabla automáticamente)
```

## Licencia

MIT

## Contacto

Desarrollado por Guarrod Studio
Email: guarrodesign@gmail.com
