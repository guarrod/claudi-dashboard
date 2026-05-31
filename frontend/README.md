# Personal Finance App - Frontend

Frontend React Native + Expo para la aplicación de finanzas personales.

## Requisitos

- Node.js 18+
- npm o yarn
- Expo CLI: `npm install -g expo-cli`

## Instalación

1. Instalar dependencias:

```bash
npm install
```

2. Crear archivo `.env` (opcional):

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000
```

## Ejecutar la app

### iOS Simulator

```bash
npm run ios
```

### Android Emulator

```bash
npm run android
```

### Web (desarrollo)

```bash
npm run web
```

### Expo Go (en dispositivo real)

```bash
npm start
```

Escanear código QR con Expo Go app en iOS o Android.

## Estructura

```
frontend/
├── App.js                    # Entry point
├── app.json                  # Expo config
├── package.json             # Dependencias
├── src/
│   ├── config/              # Configuración (API, etc)
│   ├── navigation/           # Navegadores
│   ├── screens/              # Pantallas
│   │   ├── auth/            # Login, auth
│   │   └── app/             # Dashboard, Sprint, Settings
│   ├── components/           # Componentes reutilizables
│   ├── redux/               # Estado global (Redux)
│   │   ├── slices/          # Redux slices
│   │   └── store.js         # Redux store
│   ├── services/            # Servicios (API calls)
│   └── utils/               # Utilidades
└── assets/                  # Imágenes, fuentes, etc
```

## Características implementadas (Fase 1)

- ✅ Navegación básica (Login → Dashboard → Sprint → Settings)
- ✅ Login simple (sin OAuth aún)
- ✅ Redux para estado global
- ✅ Conexión a backend (axios)
- ✅ Pantalla de Dashboard (muestra sprint activo)
- ✅ Pantalla de Sprint (lista transacciones)
- ✅ Pantalla de Configuración (tema, método de completación)

## Próximos pasos

- [ ] Fase 2: Pantalla de creación de transacciones
- [ ] Fase 3: Marcar transacciones (checkbox/slide)
- [ ] Fase 4: Integración de Google OAuth
- [ ] Fase 5: Notificaciones
- [ ] Fase 6: Temas Light/Dark
- [ ] Fase 7: Sincronización real-time

## Estilos y Temas

- Colores principales: `#007AFF` (azul iOS)
- Fondo: `#f5f5f5`
- Tarjetas: `#fff` con sombra ligera

## Testing

```bash
npm test
```

## Troubleshooting

### Puerto 19000 en uso

```bash
expo start --port 19001
```

### Limpiar cache

```bash
expo start -c
```

### Ver logs

```bash
expo start
# Presionar 'i' para iOS o 'a' para Android
```
