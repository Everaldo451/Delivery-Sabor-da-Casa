# Delivery-Sabor-da-Casa

## Backend

Instale as dependências com uv:

```powershell
cd backend
python -m uv sync --group dev
python -m uv run uvicorn app.main:app --reload
```