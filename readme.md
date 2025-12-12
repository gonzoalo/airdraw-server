# AirDraw Server

FastAPI server that provides Airflow operators discovery and DAG management capabilities.

## Features

- **Operator Discovery** - Automatically detects all available Airflow operators without importing
- **Fast Startup** - AST-based parsing for quick initialization
- **Operator Status** - Track available and unavailable operators
- **Airflow Integration** - Query DAGs and runs from Airflow instances
- **CORS Support** - Ready for frontend integration
- **Structured Logging** - Built-in logging infrastructure

## Requirements

- Python 3.8+
- Apache Airflow 2.7+
- FastAPI 0.104+

## Installation

1. **Clone the repository:**
```bash
git clone <repo-url>
cd airdraw-server
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create `.env` file:**
```bash
cp .env.example .env
```

## Configuration

Edit `.env` with your settings:

```env
# App
APP_NAME=AirDraw Server
DEBUG=True
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# Airflow
AIRFLOW_HOME=~/airflow
AIRFLOW__CORE__SQL_ALCHEMY_CONN=sqlite:///~/airflow/airflow.db
AIRFLOW__CORE__DAGS_FOLDER=~/airflow/dags
AIRFLOW__WEBSERVER__BASE_URL=http://localhost:8080
```

## Running the Server

**Development with auto-reload:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Or using the script:**
```bash
chmod +x run.sh
./run.sh
```

**Production:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Visit: `http://localhost:8000/docs` for interactive API docs

## API Endpoints

### Operators

- `GET /operators/all` - Get all available operators
- `GET /operators/status` - Get operator availability status

### Health

- `GET /health` - Server health check
- `GET /` - Root endpoint

### Files

- `GET /listFiles` - List files in current directory
- `GET /path` - Show Airflow providers path

## Project Structure

```
airdraw-server/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env                 # Environment variables
├── README.md            # This file
│
├── app/
│   ├── config.py        # Settings & configuration
│   ├── core/
│   │   └── operators.py # Operator loading logic
│   ├── api/
│   │   └── routes/
│   │       ├── operators.py
│   │       ├── files.py
│   │       └── health.py
│   └── models/
│       └── schemas.py   # Pydantic models
│
└── tests/
    └── test_operators.py
```

## How It Works

### Operator Discovery

The server uses **AST (Abstract Syntax Tree) parsing** to discover operators without importing them:

1. Walks through `airflow.providers` packages
2. Locates operator modules
3. Parses Python files with AST
4. Extracts class names containing "Operator"
5. Filters out base classes (BaseOperator, BaseBranchOperator, etc.)
6. Caches results at startup

**Benefits:**
- ⚡ Fast startup (50-80% faster than imports)
- 🔒 Safe (no side effects from imports)
- 📦 Detects unavailable operators

### Example Response

```json
{
    "available": {
        "airflow.providers.smtp.operators.smtp": ["EmailOperator"],
        "airflow.providers.standard.operators.bash": ["BashOperator"],
        "airflow.providers.standard.operators.python": [
            "PythonOperator",
            "BranchPythonOperator"
        ]
    },
    "unavailable": {
        "airflow.providers.standard.operators.hitl": "Human in the loop needs Airflow 3.1+"
    },
    "summary": {
        "total_available_modules": 9,
        "total_unavailable_modules": 1,
        "total_operators": 25
    }
}
```

## Development

### Running Tests

```bash
pytest
pytest -v  # Verbose
pytest --cov=app  # With coverage
```

### Code Formatting

```bash
black app/  # Format code
flake8 app/  # Check style
```

### Debugging

VS Code users can press `F5` to start with debugger (uses `.vscode/launch.json`).

## Logging

Logs are configured in `app/config.py`. Default level is `INFO`.

View logs:
```bash
tail -f logs/airdraw.log
```

## Troubleshooting

**Issue: Operators not loading**
- Check Airflow installation: `python -c "import airflow; print(airflow.__version__)"`
- Verify `AIRFLOW_HOME` environment variable
- Check logs for import errors

**Issue: Slow startup**
- Make sure you're using the AST-based approach (not importing)
- Check `LOG_LEVEL=DEBUG` for details

**Issue: CORS errors**
- Verify `CORS_ORIGINS` in `.env` matches your frontend URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests & linting
5. Submit a pull request

## License

MIT

## Support

For issues or questions, open an issue on GitHub or contact the maintainers.