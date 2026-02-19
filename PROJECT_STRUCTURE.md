# Estructura del Proyecto: Portfolio Agent Platform

Este documento detalla la organización de archivos y directorios del sistema tras la fase de estabilización y auditoría.

## 📂 Raíz del Proyecto
- `docker-compose.yml`: Orquestación de contenedores (Agentes, DB, MinIO, Metabase).
- `setup.ps1` / `setup.sh`: Scripts de automatización para inicio rápido.
- `readme.md`: Documentación principal y guías de uso.
- `pyproject.toml`: Configuración de herramientas de calidad (Ruff, Black, Mypy).
- `audit_report.md`: Informe técnico de auditoría y reparaciones.

## 📂 services/ (Microservicios)
Contiene el código fuente de los 5 agentes autónomos. Cada agente sigue una estructura idéntica:
- `Dockerfile`: Definición de la imagen del contenedor (optimizado, multi-stage).
- `requirements.txt`: Dependencias de Python con versiones fijadas (pinned).
- `main.py`: Punto de entrada de la aplicación FastAPI.
- `schema.py`: Modelos de datos Pydantic (Input/Output).
- `rules/`: Lógica de negocio específica del agente.
- `tests/`: Pruebas unitarias con Pytest.

### Agentes
- `value_agent/`: Análisis fundamental (DCF, Margin of Safety).
- `quant_agent/`: Análisis técnico y cuantitativo.
- `macro_agent/`: Análisis macroeconómico (Tasas, Inflación).
- `risk_agent/`: Evaluación de riesgo y volatilidad.
- `consensus_agent/`: Agregación de señales y toma de decisión final.

### 📂 services/shared/ (Librería Compartida)
Código reutilizable montado en todos los contenedores para evitar duplicación.
- `config.py`: Gestión centralizada de configuración (Pydantic Settings).
- `database.py`: Conexión a base de datos y sesión SQLAlchemy.
- `logger.py`: Configuración de logging estructurado.
- `middleware.py`: Seguridad (CORS) y middlewares HTTP.
- `models/`: Modelos ORM (SQLAlchemy) y Pydantic compartidos.

## 📂 orchestration/ (Workflow)
Scripts para la ejecución y coordinación del sistema.
- `pipeline.py`: Ejecuta el flujo de análisis (Datos -> Agentes -> Consenso -> DB). Implementa retries y manejo de errores.
- `seeder.py`: Generación de datos sintéticos de prueba.

## 📂 infrastructure/ (IaC & Config)
- `.env.example`: Plantilla de variables de entorno.
- `main.tf`: (Stub) Configuración de Terraform para despliegue en nube.
- `.github/workflows/ci.yml`: Pipeline de Integración Continua (CI).
