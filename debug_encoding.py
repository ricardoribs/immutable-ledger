import os

def check_files():
    print("🕵️  Iniciando varredura por arquivos com codificação inválida...")
    
    # Vamos olhar tudo, menos a pasta venv (que não é nossa) e git
    ignore_folders = {'venv', '.git', '__pycache__', '.pytest_cache'}
    
    found_error = False

    for root, dirs, files in os.walk("."):
        # Remove pastas ignoradas da busca
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        
        for file in files:
            if file.endswith(".py") or file.endswith(".env") or file.endswith(".txt"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        f.read()
                except UnicodeDecodeError as e:
                    print(f"\n🚨 ENCONTRADO! O arquivo culpado é: {filepath}")
                    print(f"   Erro: {e}")
                    print("   -> Abra este arquivo, apague o conteúdo e cole novamente (sem acentos) ou delete-o.")
                    found_error = True
                except Exception as e:
                    print(f"⚠️  Erro ao ler {filepath}: {e}")

    if not found_error:
        print("\n✅ Nenhum erro de codificação encontrado nos arquivos varridos.")
        print("   Se o erro persistir, pode ser um arquivo que eu não verifiquei (ex: cache).")

if __name__ == "__main__":
    check_files()