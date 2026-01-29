from sqlalchemy import create_engine
from src.domain.ledger.models import Base
from src.domain.ledger import models 
import traceback

def create_tables_sync():
    print("🚀 Modo Hardcoded (Driver PG8000) iniciado...")
    
    # MUDANÇA: Usando o driver '+pg8000' que não trava com acentos do Windows
    sync_url = "postgresql+pg8000://admin:admin_password@127.0.0.1:5455/ledger_core"
    
    print(f"Connecting to: {sync_url}")

    try:
        engine = create_engine(sync_url, echo=True) 
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ SUCESSO! Tabelas criadas: Accounts, Transactions, Postings.")
        
    except Exception as e:
        print("\n🚨 ERRO DE CONEXÃO 🚨")
        print(f"O driver PG8000 conseguiu capturar o erro real:")
        print(e)
        print("-" * 30)
        traceback.print_exc() 

if __name__ == "__main__":
    create_tables_sync()