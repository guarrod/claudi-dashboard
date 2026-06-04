# Presupuesto - Interfaz de la Aplicación

## Estructura General

La aplicación tiene una **navegación con 4 tabs principales** en la parte inferior:

```
┌─────────────────────────────────────┐
│           Dashboard                 │
│  [Home] [Sprint] [Bell] [Settings] │
└─────────────────────────────────────┘
```

---

## 1. TAB: DASHBOARD

**Bienvenida y Resumen de Finanzas**

```
┌─────────────────────────────────────┐
│ Dashboard                           │
│ Bienvenido, guarrodesign@gmail.com  │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Sprint 1                     │   │
│  │ 15/05/2026 - 31/05/2026   │15  │
│  │ [████░░░░░░░░░░░░░░░░░░░] días│
│  └──────────────────────────────┘   │
│                                     │
│  ┌─────────────┐  ┌─────────────┐  │
│  │💰 Balance   │  │✓ Disponible │  │
│  │  $5,000.00  │  │  $2,500.00  │  │
│  └─────────────┘  └─────────────┘  │
│                                     │
│ Mis Cuentas                         │
│ ┌─────────────────────────────────┐ │
│ │🏦 Banco Principal          $2000│ │
│ │   Banco                     disp│ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │💵 Efectivo                 $500 │ │
│ │   Efectivo                      │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

**Componentes:**
- Sprint actual con fecha y días restantes
- Barra de progreso visual
- 2 cajas de totales (Balance Total, Disponible)
- Lista de cuentas con iconos y saldos

---

## 2. TAB: SPRINT

**Gestión de Gastos del Sprint Actual**

```
┌─────────────────────────────────────┐
│ Sprints                             │
│              [📑 Plantillas]        │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Sprint 1 (15 - 31 de Mayo)   │   │
│  │                              │   │
│  │ Presupuesto: $4,000          │   │
│  │ Gastado: $1,500 ████░░░░░    │   │
│  │ Disponible: $2,500           │   │
│  └──────────────────────────────┘   │
│                                     │
│ Transacciones del Sprint:           │
│                                     │
│  ┌─────────────────────────────┐    │
│  │☐ Netflix              $15.00│    │ (NO COMPLETADO)
│  │  Suscripción          Hoy    │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │☑ Supermercado       $150.00 │    │ (COMPLETADO - gris)
│  │  Comida             Ayer     │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │☐ Gasolina                  │    │
│  │  Transporte          $75.00│    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌──────────────────────────────┐   │
│  │  ✓ Completar Sprint          │   │
│  │  (botón verde con checkmark) │   │
│  └──────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Botón "Plantillas" para acceder a gastos fijos reutilizables
- Resumen visual del presupuesto
- Checkbox para marcar transacciones completadas
- Cada transacción muestra: concepto, monto, categoría, fecha
- Botón "Completar Sprint" para cerrar el período

**Al presionar "Completar Sprint":**

```
┌─────────────────────────────────────┐
│ Completar Sprint                    │
│                                     │
├─────────────────────────────────────┤
│ Sprint:                             │
│ Sprint 1 (15 - 31 de Mayo)         │
│                                     │
│ Cuenta:                             │
│ Banco Principal                     │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Saldo Disponible        $2,500   │ │ (Verde)
│ │ Este es el dinero que quedó      │ │
│ │ después de los compromisos       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 💡 Sugerencia de Ahorros           │ │
│ Te sugerimos guardar $2,500        │ │
│ en tu cuenta de ahorros            │ │
│                                     │
│ Monto a Ahorrar:                    │
│ $ [2500.00                        ]│ │
│ Dejar en blanco para completar    │ │
│ sin ahorrar                         │ │
│                                     │
│ [Cancelar]  [Completar Sprint]     │
│                                     │
└─────────────────────────────────────┘
```

---

## 3. TAB: NOTIFICACIONES

**Gastos Detectados en Gmail (NUEVA - Phase 9)**

```
┌─────────────────────────────────────┐
│ Notificaciones              [🔄]    │
│ Gastos detectados en emails         │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ 💳 Netflix Charge       $15.99│   │
│  │ Detectado en: EMAIL            │   │
│  │ Hoy a las 10:30 AM             │   │
│  │                                │   │
│  │ [Descartar]  [Confirmar]       │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ 💳 Starbucks Coffee      $7.50│   │
│  │ Detectado en: EMAIL            │   │
│  │ Hoy a las 09:15 AM             │   │
│  │                                │   │
│  │ [Descartar]  [Confirmar]       │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ 💳 Amazon Purchase      $45.00│   │
│  │ Detectado en: EMAIL            │   │
│  │ Ayer a las 2:30 PM             │   │
│  │                                │   │
│  │ [Descartar]  [Confirmar]       │   │
│  └──────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Botón 🔄 para sincronizar emails de Gmail (manual trigger)
- Muestra gastos detectados automáticamente
- Para cada gasto: concepto, monto, fuente (email), fecha/hora
- Botón "Confirmar" - marca como completado y validado
- Botón "Descartar" - rechaza la notificación
- Pull-to-refresh para actualizar manualmente

**Estados posibles:**
- ✓ Con transacciones pendientes de validación → muestra la lista
- ✓ Sin notificaciones → "Todo al día" (checkmark verde + mensaje)

---

## 4. TAB: CONFIGURACIÓN

**Ajustes y Preferencias**

```
┌─────────────────────────────────────┐
│ Configuración                       │
│                                     │
├─────────────────────────────────────┤
│                                     │
│ Cuenta                              │
│ ┌─────────────────────────────────┐ │
│ │👤 Perfil                    >   │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │🔐 Cerrar Sesión             >   │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Preferencias                        │
│ ┌─────────────────────────────────┐ │
│ │🌓 Tema                 Sistema  │ │
│ │   (Light / Dark / System)       │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │📋 Plantillas                >   │ │
│ │   Gastos fijos reutilizables    │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │📱 Notificaciones            >   │ │
│ │   Configurar alertas            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Aplicación                          │
│ ┌─────────────────────────────────┐ │
│ │ℹ️ Versión                  1.0.0│ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

---

## PANTALLA: PLANTILLAS DE GASTOS

**Gastos Fijos Reutilizables**

```
┌─────────────────────────────────────┐
│ Plantillas de Gastos           [➕] │
│ Gastos fijos reutilizables          │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Netflix                 $15.99│   │ [✏️] [🗑️]
│  │ Mensual                        │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Renta                  $1200.00│   │ [✏️] [🗑️]
│  │ Mensual                        │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Gym                     $50.00│   │ [✏️] [🗑️]
│  │ Mensual                        │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Spotify                  $9.99│   │ [✏️] [🗑️]
│  │ Mensual                        │   │
│  └──────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Botón ➕ para crear nueva plantilla
- Listar todas las plantillas guardadas
- Botones para editar (✏️) y eliminar (🗑️)
- Al seleccionar un modo especial:

```
┌─────────────────────────────────────┐
│ Plantillas de Gastos    [Cancelar]  │
│                         (2)          │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ ☑ Netflix              $15.99│   │ (Seleccionada - azul)
│  │    Mensual                     │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ ☑ Renta                $1200.00  │ │ (Seleccionada - azul)
│  │    Mensual                     │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ ☐ Gym                   $50.00│   │ (No seleccionada)
│  │    Mensual                     │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────────┐ │
│  │ [Cancelar (2)]  [Aplicar]       │ │
│  └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

---

## PANTALLA: AHORROS

**Historial y Saldo de Ahorros**

```
┌─────────────────────────────────────┐
│ Ahorros                             │
│ Tu fondo de ahorros                 │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │ 🐷 Saldo Total      $5,250.00│   │
│  └──────────────────────────────┘   │
│                                     │
│ Historial de Movimientos            │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Finalización Sprint 1        │   │
│  │ + $2,500.00                  │   │ (VERDE - depósito)
│  │ 31 de Mayo, 2026             │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Retiro de Ahorros            │   │
│  │ - $500.00                    │   │ (ROJO - retiro)
│  │ 28 de Mayo, 2026             │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Finalización Sprint 0        │   │
│  │ + $3,250.00                  │   │
│  │ 15 de Mayo, 2026             │   │
│  └──────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Saldo total de ahorros en grande
- Historial completo de movimientos
- Cada movimiento muestra: tipo, monto, fecha
- Depósitos en verde (+)
- Retiros en rojo (-)

---

## MODAL: CREAR/EDITAR PLANTILLA

```
┌─────────────────────────────────────┐
│ Nueva Plantilla              [✕]    │
├─────────────────────────────────────┤
│                                     │
│ Nombre *                            │
│ [ej: Netflix, Renta, Gym         ] │
│                                     │
│ Monto *                             │
│ $ [0.00                           ] │
│                                     │
│ Frecuencia                          │
│ ┌─────────────────────────────────┐ │
│ │ Mensual          ▼               │ │
│ │ - Mensual                       │ │
│ │ - Quincenal                     │ │
│ │ - Otra                          │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Categoría                           │
│ ┌─────────────────────────────────┐ │
│ │ Sin categoría     ▼              │ │
│ │ - Sin categoría                 │ │
│ │ - Comida                        │ │
│ │ - Transporte                    │ │
│ │ - Entretenimiento               │ │
│ └─────────────────────────────────┘ │
│                                     │
│ * Campos requeridos.                │
│ Las plantillas se reutilizan.       │
│                                     │
│ [Cancelar]        [Crear]           │
│                                     │
└─────────────────────────────────────┘
```

---

## COLORES Y TEMAS

**Tema Light (Defecto):**
- Fondo: #f5f5f5 (gris muy claro)
- Texto principal: #333 (gris oscuro)
- Acentos: #007AFF (azul iOS)
- Éxito: #34C759 (verde)
- Error: #ff3b30 (rojo)
- Cards: #fff (blanco)

**Tema Dark:**
- Fondo: #1c1c1e (negro oscuro)
- Texto: #fff (blanco)
- Acentos: #0A84FF (azul más brillante)
- Éxito: #34C759 (verde igual)
- Error: #ff453a (rojo más brillante)
- Cards: #2c2c2e (gris oscuro)

---

## FLUJO DE USO TÍPICO

### Sprint Normal (Día a Día):

1. **Abres Dashboard** → ves sprint activo, saldos disponibles
2. **Vas a Sprint** → ves transacciones planeadas
3. **Durante el día:**
   - Se detectan consumos en tus emails
   - Recibes notificaciones en la app
   - Vas a Notificaciones → confirmas o descartas
4. **Marcas manualmente:** transacciones pagadas en efectivo
5. **Fin del sprint:**
   - Click "Completar Sprint"
   - Modal sugiere mover saldo restante a ahorros
   - Confirmas
   - Saldo se transfiere automáticamente

### Crear Plantilla:

1. Vas a **Plantillas** (desde Sprint o Settings)
2. Click ➕ **Nueva Plantilla**
3. Ingresas: Netflix, $15.99, Mensual, Entretenimiento
4. Click **Crear**
5. La plantilla queda guardada
6. Próximo sprint puedes aplicarla automáticamente

---

## CARACTERÍSTICAS IMPLEMENTADAS

✅ **Autenticación** - Login/Signup con Google OAuth
✅ **Dashboard** - Vista general de finanzas
✅ **Sprints** - Gestión de períodos (15 días)
✅ **Transacciones** - Crear, editar, marcar completas
✅ **Plantillas** - Gastos fijos reutilizables
✅ **Ahorros** - Saldo e historial de movimientos
✅ **Notificaciones** - Detección automática de gastos (Gmail)
✅ **Temas** - Light/Dark/System
✅ **Múltiples Cuentas** - Banco, Efectivo, Tarjetas
✅ **Validación Manual** - Confirmar/Descartar gastos detectados

---

## PARA EJECUTAR LOCALMENTE

```bash
# Backend (FastAPI)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# Servidor en http://localhost:8000

# Frontend (React Native + Expo)
cd frontend
npm install --legacy-peer-deps
npm start
# O para Web:
npm run web
# Abrirá http://localhost:19006
```

---

**Última actualización:** Phase 9 - Gmail Integration & Notifications
