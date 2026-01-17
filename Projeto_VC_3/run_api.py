"""
Script para executar a API de OCR de Notas Fiscais.

Uso:
    python run_api.py

A API estará disponível em http://localhost:8000
Documentação interativa: http://localhost:8000/docs
"""

import uvicorn
from src.config import API_CONFIG

if __name__ == "__main__":
    print("=" * 60)
    print("API OCR Notas Fiscais")
    print("=" * 60)
    print(f"Iniciando servidor em http://localhost:{API_CONFIG['port']}")
    print(f"Documentação: http://localhost:{API_CONFIG['port']}/docs")
    print("=" * 60)

    uvicorn.run(
        "src.api.main:app",
        host=API_CONFIG.get("host", "0.0.0.0"),
        port=API_CONFIG.get("port", 8000),
        reload=True,
        log_level="info"
    )
