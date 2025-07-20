#!/usr/bin/env python3
"""
Script simples para iniciar o servidor Marag
"""

import uvicorn
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from server import main
    
    print("🚀 Iniciando servidor Marag...")
    print("📊 Porta: 10031")
    print("🌐 URL: http://localhost:10031")
    print()
    
    # Executar o servidor
    main()
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("💡 Verifique se todas as dependências estão instaladas")
    
except Exception as e:
    print(f"❌ Erro ao iniciar servidor: {e}")
    print("💡 Verifique a configuração do servidor") 