# Orders Service

Servicio de gestión de órdenes construido con Python 3.12, FastAPI y arquitectura hexagonal.

Proyecto final del curso Python Complete.

## Arquitectura

El proyecto sigue arquitectura hexagonal (puertos y adaptadores) con tres capas:

```
src/
├── domain/            # Entidades, reglas de negocio, puertos
│   ├── entities.py    # Order, OrderItem con validaciones
│   ├── events.py      # OrderCreated, OrderCompleted, OrderCancelled
│   ├── exceptions.py  # Errores de dominio tipados
│   └── ports.py       # Protocols: OrderRepository, UnitOfWork, EventPublisher
│
├── application/       # Casos de uso y orquestación
│   ├── use_cases.py   # CreateOrder, CompleteOrder, CancelOrder, etc.
│   ├── dtos.py        # Modelos Pydantic de entrada/salida
│   ├── event_handlers.py  # EventBus para despachar eventos
│   └── handlers/      # Handlers concretos por evento
│
└── infrastructure/    # Frameworks y adaptadores
    ├── config.py      # pydantic-settings con variables de entorno
    ├── adapters/
    │   ├── sql_models.py   # Modelos SQLAlchemy
    │   ├── sql_repo.py     # Adaptador SQL del repositorio
    │   ├── sql_uow.py      # Unit of Work con transacciones reales
    │   ├── memory_repo.py  # Adaptador en memoria (tests)
    │   ├── memory_uow.py   # UoW en memoria (tests)
    │   ├── database.py     # Engine y session factory
    │   └── seed.py         # Datos de prueba iniciales
    └── api/
        ├── main.py         # App FastAPI, middlewares, routers
        ├── auth.py         # JWT, bcrypt, verificación de tokens
        ├── auth_router.py  # Endpoints de registro y login
        ├── orders_router.py # CRUD de órdenes
        ├── dependencies.py # Wiring de casos de uso
        ├── middleware.py   # Logging de requests con ID y tiempos
        └── retry.py        # Decorador de reintentos con backoff
```

### Regla de dependencia

Las dependencias siempre apuntan hacia adentro:

- **Dominio** no importa nada externo
- **Aplicación** depende solo del dominio
- **Infraestructura** depende de ambas y conecta con el mundo exterior

### Flujo de un request

1. FastAPI recibe el request y valida con Pydantic (DTOs)
2. El router delega al caso de uso correspondiente
3. El caso de uso abre una transacción con Unit of Work
4. La entidad de dominio valida reglas de negocio
5. El repositorio persiste los cambios
6. La entidad emite eventos de dominio
7. El UoW confirma la transacción
8. El EventBus despacha los eventos a los handlers

## Requisitos

- Python 3.12+
- Poetry 2.x

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd orders-service

# Instalar dependencias
poetry install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Crear base de datos y seed
poetry run alembic upgrade head
poetry run python -m src.infrastructure.adapters.seed
```

## Ejecución

```bash
# Desarrollo
poetry run uvicorn src.main:app --reload

# La API estará en http://localhost:8000
# Documentación interactiva en http://localhost:8000/docs
```

## Docker

```bash
# Build
docker build -t orders-service .

# Run
docker run -p 8000:8000 orders-service
```

## Tests

```bash
# Todos los tests
poetry run pytest tests/ -v

# Con cobertura
poetry run pytest tests/ --cov=src --cov-report=term-missing

# Solo unitarios
poetry run pytest tests/unit/ -v

# Solo contrato
poetry run pytest tests/contract/ -v

# Solo E2E
poetry run pytest tests/e2e/ -v
```

### Estructura de tests

| Nivel | Directorio | Qué prueba |
|-------|-----------|------------|
| Unitarios | `tests/unit/` | Entidades, casos de uso, event handlers (sin DB ni HTTP) |
| Contrato | `tests/contract/` | Verifican que InMemoryRepo y SqlRepo se comportan igual |
| E2E | `tests/e2e/` | Flujo completo: HTTP → caso de uso → DB → respuesta |

## API Endpoints

### Auth

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/auth/register` | Registrar usuario | No |
| POST | `/auth/login` | Iniciar sesión | No |

### Orders

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/orders/` | Listar órdenes | No |
| GET | `/orders/{id}` | Obtener orden por ID | No |
| POST | `/orders/` | Crear orden | Sí |
| PATCH | `/orders/{id}` | Cambiar status | Sí |
| DELETE | `/orders/{id}` | Eliminar orden | Sí |

### Filtros

```
GET /orders/?status=pending
GET /orders/?status=completed
GET /orders/?status=cancelled
```

## Calidad de código

```bash
# Linter
poetry run ruff check .

# Formateo
poetry run black --check .
poetry run isort --check .

# Tipado estático
poetry run mypy src/

# Auditoría de dependencias
poetry run pip-audit
```

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `APP_SECRET_KEY` | Clave para JWT | dev-secret-change-me |
| `APP_DATABASE_URL` | URL de la base de datos | sqlite:///orders.db |
| `APP_DEBUG` | Modo debug | false |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración del token | 30 |

## Tecnologías

- **FastAPI** — Framework web async
- **SQLAlchemy 2.0** — ORM con tipado nativo
- **Alembic** — Migraciones de base de datos
- **Pydantic v2** — Validación y serialización
- **pydantic-settings** — Configuración por entorno
- **PyJWT** — Autenticación con tokens
- **bcrypt** — Hashing de contraseñas
- **pytest** — Testing con fixtures y parametrización
- **Hypothesis** — Property-based testing
- **Docker** — Containerización multistage
- **GitHub Actions** — CI/CD pipeline
- **ruff** — Linter ultra rápido
- **black** — Formateador de código
- **mypy** — Verificación de tipos estática
- **pip-audit** — Auditoría de vulnerabilidades
