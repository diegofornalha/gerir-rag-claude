#!/usr/bin/env python3
"""
Servidor simples para testar se funciona
"""

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Marag Test Server")

@app.get("/")
async def root():
    return {"message": "Marag Server is running!", "port": 10031}

@app.get("/health")
async def health():
    return {"status": "healthy", "port": 10031}

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste Marag...")
    print("📊 Porta: 10031")
    print("🌐 URL: http://localhost:10031")
    print()
    
    uvicorn.run(app, host="localhost", port=10031) 