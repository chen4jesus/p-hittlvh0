# CCC Gen Jong Flask Web Application

A modern Flask web application following best practices.

## Project Structure

- `app/`: Main application package
  - `routes/`: Blueprint-based routing
  - `models/`: Database models
  - `static/`: Frontend assets (CSS, JS, Images)
  - `templates/`: Jinja2 templates
  - `config.py`: Configuration management
  - `extensions.py`: Flask extension initialization
- `instance/`: Instance-specific files (SQLite DB)
- `tests/`: Automated tests
- `wsgi.py`: WSGI entry point for the application factory

## Getting Started

### 1. Prerequisite

- Python 3.8+
- Virtual environment (recommended)

### 2. Installation

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Copy `.env.example` to `.env` and update the values.

```bash
cp .env.example .env
```

### 4. Database Setup

```bash
flask db upgrade
```

### 5. Running the Application

```bash
python wsgi.py
```

Or using Flask CLI:

```bash
flask run
```

## Best Practices Followed

- **Application Factory Pattern**: Better testability and scalability.
- **Blueprints**: Modular routing structure.
- **Configuration Management**: Environment-specific settings using `.env`.
- **Custom Error Handling**: Graceful error pages for 404, 500, etc.
- **Structured Static/Template folders**: Organized according to Flask standards.
