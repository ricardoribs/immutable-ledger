import redis
import sys

try:
    print("⏳ Tentando conectar no Redis (127.0.0.1:6379)...")
    # Tenta conectar com timeout curto (2 segundos) para não ficar travado
    r = redis.Redis(host='127.0.0.1', port=6379, socket_connect_timeout=2)
    
    # Manda um PING
    resposta = r.ping()
    
    if resposta:
        print("✅ SUCESSO! O Redis respondeu PONG.")
        print("   O problema não é conexão.")
    else:
        print("⚠️ O Redis conectou mas não respondeu.")

except Exception as e:
    print("\n🚨 ERRO DE CONEXÃO!")
    print(f"   O Python não consegue ver o Redis.")
    print(f"   Erro detalhado: {e}")
    print("\n   DICA: Verifique se o Docker está rodando e se a porta 6379 está exposta.")