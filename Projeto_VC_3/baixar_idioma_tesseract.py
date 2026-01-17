"""
Script para Baixar Idioma Português do Tesseract
=================================================

Baixa automaticamente o arquivo por.traineddata e coloca no diretório correto.
"""

import os
import sys
import urllib.request
from pathlib import Path
import shutil

TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata"
TESSDATA_URL_ALT = "https://github.com/tesseract-ocr/tessdata/raw/5.0.0/por.traineddata"


def find_tesseract_tessdata_dir():
    """Encontra o diretório tessdata do Tesseract."""
    # Verifica variável de ambiente
    if "TESSDATA_PREFIX" in os.environ:
        tessdata_dir = os.environ["TESSDATA_PREFIX"]
        if os.path.exists(tessdata_dir):
            return tessdata_dir
    
    # Caminhos comuns do Windows
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tessdata",
        r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
        r"C:\tesseract\tessdata",
    ]
    
    # Verifica configuração do pytesseract
    try:
        import pytesseract
        if hasattr(pytesseract.pytesseract, 'tesseract_cmd') and pytesseract.pytesseract.tesseract_cmd:
            tesseract_dir = os.path.dirname(pytesseract.pytesseract.tesseract_cmd)
            tessdata_path = os.path.join(tesseract_dir, "tessdata")
            if os.path.exists(tesseract_dir):
                common_paths.insert(0, tessdata_path)
    except:
        pass
    
    # Verifica cada caminho
    for path in common_paths:
        if os.path.exists(os.path.dirname(path)):  # Verifica se diretório pai existe
            # Cria tessdata se não existir
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    return path
                except:
                    continue
            return path
    
    return None


def download_portuguese_language():
    """Baixa o arquivo por.traineddata."""
    print("=" * 60)
    print("DOWNLOAD DO IDIOMA PORTUGUÊS (TESSERACT)")
    print("=" * 60)
    print()
    
    # Encontra diretório tessdata
    tessdata_dir = find_tesseract_tessdata_dir()
    
    if not tessdata_dir:
        print("❌ Não foi possível encontrar o diretório tessdata do Tesseract.")
        print()
        print("Solução manual:")
        print("1. Localize o diretório tessdata (geralmente em C:\\Program Files\\Tesseract-OCR\\tessdata)")
        print("2. Baixe manualmente: https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata")
        print("3. Coloque o arquivo por.traineddata no diretório tessdata")
        return False
    
    print(f"✅ Diretório tessdata encontrado: {tessdata_dir}")
    
    target_file = os.path.join(tessdata_dir, "por.traineddata")
    
    # Verifica se já existe
    if os.path.exists(target_file):
        print(f"✅ Arquivo por.traineddata já existe: {target_file}")
        response = input("Deseja baixar novamente (sobrescrever)? (s/n): ").strip().lower()
        if response != 's':
            print("Cancelado.")
            return True
    
    print()
    print(f"📥 Baixando por.traineddata...")
    print(f"   URL: {TESSDATA_URL}")
    print(f"   Destino: {target_file}")
    print()
    
    try:
        # Baixa arquivo
        def show_progress(blocknum, blocksize, totalsize):
            if totalsize > 0:
                percent = min(100, (blocknum * blocksize * 100) // totalsize)
                print(f"   Progresso: {percent}%", end='\r')
        
        try:
            urllib.request.urlretrieve(TESSDATA_URL, target_file, reporthook=show_progress)
        except:
            # Tenta URL alternativa
            print("   Tentando URL alternativa...")
            urllib.request.urlretrieve(TESSDATA_URL_ALT, target_file, reporthook=show_progress)
        
        print()
        
        # Verifica se baixou corretamente
        if os.path.exists(target_file) and os.path.getsize(target_file) > 0:
            size_mb = os.path.getsize(target_file) / (1024 * 1024)
            print(f"✅ Download concluído! ({size_mb:.2f} MB)")
            print()
            print("✅ Idioma português instalado com sucesso!")
            print()
            print("Próximos passos:")
            print("1. Reinicie a API: python run_api.py")
            print("2. O Tesseract usará o idioma português")
            return True
        else:
            print("❌ Arquivo baixado está vazio ou corrompido")
            return False
    
    except PermissionError:
        print(f"❌ Erro: Sem permissão para escrever em {target_file}")
        print()
        print("Solução:")
        print("1. Execute este script como Administrador")
        print("   (Clique direito → Executar como administrador)")
        print()
        print("2. Ou baixe manualmente:")
        print(f"   {TESSDATA_URL}")
        print(f"   Coloque em: {tessdata_dir}")
        return False
    
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        print()
        print("Download manual:")
        print(f"1. Baixe: {TESSDATA_URL}")
        print(f"2. Coloque em: {tessdata_dir}")
        return False


if __name__ == "__main__":
    try:
        success = download_portuguese_language()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
