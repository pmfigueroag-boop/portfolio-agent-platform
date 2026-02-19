# Plataforma Agéntica de Gestión de Portafolios – Enfoque 365

![CI Status](https://github.com/tu-usuario/portfolio-agent-platform/actions/workflows/ci.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.9-blue)
![Docker](https://img.shields.io/badge/docker-compose-green)

Plataforma de análisis financiero institucional basada en una arquitectura de microservicios y agentes autónomos (Value, Quant, Macro, Risk, Consensus). Diseñada con énfasis en la estabilidad operativa, reproducibilidad y escalabilidad.

---

## 🚀 Quick Start (Inicio Rápido)

La forma más segura y robusta de iniciar la plataforma es utilizando los scripts de automatización incluidos.

### Windows (PowerShell)
```powershell
.\setup.ps1
```

### Linux / Mac (Bash)
```bash
chmod +x setup.sh
./setup.sh
```

### Ejecución Manual (Docker Compose)
Si prefieres control manual:
```bash
# Construir y levantar servicios en segundo plano
docker-compose up -d --build
```

---

## 📋 Requisitos Previos

*   **Docker Desktop** (con soporte para Linux Containers en Windows).
*   **Python 3.9+** (Recomendado para desarrollo local y ejecución de scripts de orquestación).
*   **Git** (Control de versiones).

---

## 🏗 Arquitectura del Sistema

La plataforma orquesta 8 servicios contenerizados, comunicados a través de una red interna `bridge`.

| Servicio | Puerto Host | Descripción | Recursos (Límite) |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `5432` | Base de datos relacional (Activos, Precios, Señales). | 0.5 CPU / 512MB RAM |
| **MinIO** | `9000/9001` | Object Storage compatible con S3 (Data Lake). | 0.5 CPU / 512MB RAM |
| **Metabase** | `3000` | Dashboard de BI y Visualización. | 1.0 CPU / 1GB RAM |
| **Value Agent** | `8001` | Análisis Fundamental (DCF, Ratios). | 0.5 CPU / 256MB RAM |
| **Quant Agent** | `8002` | Análisis Técnico y Momentum. | 0.5 CPU / 512MB RAM |
| **Macro Agent** | `8003` | Análisis Macroeconómico Global. | 0.5 CPU / 256MB RAM |
| **Risk Agent** | `8004` | Gestión de Riesgo y Volatilidad. | 0.5 CPU / 512MB RAM |
| **Consensus Agent**| `8005` | Agregación de señales y Toma de Decisión. | 0.5 CPU / 256MB RAM |

---

## � Guía de Desarrollo

El proyecto sigue estándares estrictos de calidad de código definidos en `pyproject.toml`.

### Configuración del Entorno Local
Se recomienda crear un entorno virtual para desarrollo:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias de desarrollo
pip install ruff black mypy pytest httpx requests pandas sqlalchemy types-requests types-ujson
```

### Calidad de Código (Linting & Formatting)
Antes de hacer commit, asegúrate de que el código cumpla con los estándares:

```bash
# Verificar estilo y errores (Linter)
ruff check .

# Formatear código automáticamente
black .

# Chequeo estático de tipos
mypy services/
```

### Pruebas (Testing)
Ejecutar la suite de pruebas unitarias con cobertura:
```bash
pytest
```

---

## 🛠 Operación y Orquestación

### 1. Sembrado de Datos (Data Seeding)
Genera datos sintéticos para validar la lógica de los agentes:
```bash
python orchestration/seeder.py
```

### 2. Ejecutar Pipeline de Análisis
Dispara el proceso de análisis completo (Macro -> Agentes -> Consenso):
```bash
python orchestration/pipeline.py
```
*Nota: El pipeline incluye lógica de reintentos automáticos (backoff exponencial) para robustez.*

### 3. Visualización (Metabase)
Accede a `http://localhost:3000` para configurar los dashboards.
*   **Database Host:** `db`
*   **User/Pass:** Ver `.env.example`

---

## 🔧 Troubleshooting

### Puertos Ocupados
Si obtienes un error `Bind for 0.0.0.0:5432 failed: port is already allocated`, significa que tienes otro servicio (como un Postgres local) usando el puerto.
*   **Solución:** Detén el servicio local o cambia el puerto en `docker-compose.yml`.

### Error de Permisos en Docker (Linux)
Si ves errores de acceso a volúmenes o sockets:
*   Asegúrate de que tu usuario esté en el grupo `docker`: `sudo usermod -aG docker $USER`.

### Reconstrucción Limpia
Si las dependencias parecen desactualizadas o hay errores extraños de caché:
### Verificación de BD
El usuario por defecto NO es `postgres`, sino `admin`. Usa este comando:
```bash
docker exec -it portfolio_db psql -U admin -d portfolio_db -c "\dt"
```
