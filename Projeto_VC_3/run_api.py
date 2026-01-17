"""
Script para executar a API de OCR de Notas Fiscais.

Uso:
    python run_api.py

A API estará disponível em http://localhost:8000
Documentação interativa: http://localhost:8000/docs
"""

import os
import uvicorn
from src.config import API_CONFIG

if __name__ == "__main__":
    # Detectar se está em produção (Railway/Render definem PORT)
    is_production = os.getenv("PORT") is not None or os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    print("=" * 60)
    print("API OCR Notas Fiscais")
    print("=" * 60)
    print(f"Iniciando servidor em {API_CONFIG['host']}:{API_CONFIG['port']}")
    print(f"Documentação: http://{API_CONFIG['host']}:{API_CONFIG['port']}/docs")
    print(f"Ambiente: {'Produção' if is_production else 'Desenvolvimento'}")
    print("=" * 60)

    uvicorn.run(
        "src.api.main:app",
        host=API_CONFIG.get("host", "0.0.0.0"),
        port=API_CONFIG.get("port", 8000),
        reload=not is_production,  # Desabilita reload em produção
        log_level="info"
    )
