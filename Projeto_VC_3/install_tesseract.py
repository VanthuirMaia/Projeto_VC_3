"""
Script de Instalação e Configuração do Tesseract OCR
=====================================================

Este script ajuda a instalar e configurar o Tesseract OCR no Windows.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import urllib.request
import json

# URLs e caminhos
TESSERACT_WINDOWS_URL = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240505.exe"
TESSERACT_INSTALL_DIR = r"C:\Program Files\Tesseract-OCR"
TESSERACT_DEFAULT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\tesseract\tesseract.exe",
]


def check_tesseract_installed() -> tuple[bool, str]:
    """
    Verifica se Tesseract está instalado e retorna o caminho.
    
    Returns:
        Tupla (is_installed, path)
    """
    # Verifica no PATH
    if shutil.which("tesseract"):
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "tesseract"  # No PATH
        except:
            pass
    
    # Verifica caminhos comuns do Windows
    for path in TESSERACT_DEFAULT_PATHS:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True, path
            except:
                continue
    
    return False, ""


def check_portuguese_language(tesseract_path: str) -> bool:
    """Verifica se o idioma português está instalado."""
    try:
        if tesseract_path == "tesseract":
            cmd = ["tesseract", "--list-langs"]
        else:
            cmd = [tesseract_path, "--list-langs"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            langs = result.stdout.lower()
            return "por" in langs or "portuguese" in langs
    except:
        pass
    
    return False


def update_config_file(tesseract_path: str):
    """Atualiza o arquivo config.py com o caminho do Tesseract."""
    config_path = Path(__file__).parent / "src" / "config.py"
    
    if not config_path.exists():
        print(f"⚠️  Arquivo config.py não encontrado: {config_path}")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substitui ou adiciona tesseract_cmd
        if '"tesseract_cmd": None' in content or '"tesseract_cmd": None,' in content:
            content = content.replace(
                '"tesseract_cmd": None',
                f'"tesseract_cmd": r"{tesseract_path}"'
            )
            content = content.replace(
                '"tesseract_cmd": None,',
                f'"tesseract_cmd": r"{tesseract_path}",'
            )
        elif 'tesseract_cmd' not in content:
            # Adiciona se não existir
            content = content.replace(
                '"tesseract": {',
                f'"tesseract": {{\n        "tesseract_cmd": r"{tesseract_path}",'
            )
        else:
            # Substitui valor existente
            import re
            pattern = r'"tesseract_cmd":\s*r?["\'][^"\']+["\']'
            replacement = f'"tesseract_cmd": r"{tesseract_path}"'
            content = re.sub(pattern, replacement, content)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Arquivo config.py atualizado com caminho: {tesseract_path}")
    
    except Exception as e:
        print(f"⚠️  Erro ao atualizar config.py: {e}")


def download_tesseract_installer(download_path: Path) -> bool:
    """Baixa o instalador do Tesseract."""
    print(f"📥 Baixando instalador do Tesseract...")
    print(f"   URL: {TESSERACT_WINDOWS_URL}")
    print(f"   Destino: {download_path}")
    
    try:
        urllib.request.urlretrieve(
            TESSERACT_WINDOWS_URL,
            download_path,
            reporthook=lambda blocknum, blocksize, totalsize: print(
                f"   Progresso: {min(100, (blocknum * blocksize * 100) // totalsize) if totalsize > 0 else 0}%",
                end='\r'
            )
        )
        print("\n✅ Download concluído!")
        return True
    except Exception as e:
        print(f"\n❌ Erro ao baixar: {e}")
        return False


def install_tesseract_automatically():
    """Tenta instalar Tesseract automaticamente (Windows)."""
    if platform.system() != "Windows":
        print("❌ Instalação automática disponível apenas para Windows.")
        print("   Para Linux/Mac, use:")
        print("   Linux: sudo apt-get install tesseract-ocr tesseract-ocr-por")
        print("   Mac: brew install tesseract tesseract-lang")
        return False
    
    print("=" * 60)
    print("INSTALAÇÃO DO TESSERACT OCR")
    print("=" * 60)
    print()
    
    # Verifica se já está instalado
    is_installed, tesseract_path = check_tesseract_installed()
    if is_installed:
        print(f"✅ Tesseract já está instalado em: {tesseract_path}")
        
        if check_portuguese_language(tesseract_path):
            print("✅ Idioma português já está instalado")
        else:
            print("⚠️  Idioma português não encontrado")
            print("   Durante a instalação, certifique-se de marcar 'Portuguese'")
        
        update_config_file(tesseract_path)
        return True
    
    # Baixa instalador
    download_dir = Path.home() / "Downloads"
    download_dir.mkdir(exist_ok=True)
    installer_path = download_dir / "tesseract-ocr-installer.exe"
    
    print(f"📦 Tesseract não encontrado. Iniciando instalação...")
    print()
    
    # Pergunta se quer baixar
    response = input("Deseja baixar o instalador automaticamente? (s/n): ").strip().lower()
    
    if response == 's':
        if not installer_path.exists():
            if not download_tesseract_installer(installer_path):
                return False
        else:
            print(f"✅ Instalador já existe: {installer_path}")
        
        # Abre instalador
        print()
        print("🚀 Abrindo instalador...")
        print()
        print("⚠️  IMPORTANTE - Durante a instalação:")
        print("   1. Instale em: C:\\Program Files\\Tesseract-OCR")
        print("   2. Marque a opção: 'Add to PATH'")
        print("   3. Marque a opção: 'Portuguese' (idioma)")
        print()
        
        try:
            os.startfile(str(installer_path))
            print("✅ Instalador aberto!")
            print()
            input("Pressione ENTER após concluir a instalação...")
            
            # Verifica novamente
            is_installed, tesseract_path = check_tesseract_installed()
            if is_installed:
                print(f"✅ Tesseract instalado com sucesso em: {tesseract_path}")
                update_config_file(tesseract_path)
                return True
            else:
                print("⚠️  Tesseract ainda não foi detectado.")
                print("   Verifique se a instalação foi concluída.")
                return False
        
        except Exception as e:
            print(f"❌ Erro ao abrir instalador: {e}")
            return False
    else:
        print()
        print("📝 Instruções manuais:")
        print()
        print("1. Baixe o Tesseract:")
        print(f"   {TESSERACT_WINDOWS_URL}")
        print()
        print("2. Durante a instalação:")
        print("   - Instale em: C:\\Program Files\\Tesseract-OCR")
        print("   - Marque: 'Add to PATH'")
        print("   - Marque: 'Portuguese' (idioma)")
        print()
        print("3. Após instalar, execute este script novamente para configurar.")
        return False


def main():
    """Função principal."""
    print("=" * 60)
    print("CONFIGURAÇÃO DO TESSERACT OCR")
    print("=" * 60)
    print()
    
    # Verifica sistema
    if platform.system() != "Windows":
        print("⚠️  Este script é otimizado para Windows.")
        print("   Para outros sistemas, consulte o README.md")
        print()
    
    # Verifica instalação
    is_installed, tesseract_path = check_tesseract_installed()
    
    if is_installed:
        print(f"✅ Tesseract encontrado: {tesseract_path}")
        
        # Verifica idioma
        if check_portuguese_language(tesseract_path):
            print("✅ Idioma português instalado")
        else:
            print("⚠️  Idioma português não encontrado")
            print("   Você pode baixar manualmente: por.traineddata")
            print("   Coloque em: C:\\Program Files\\Tesseract-OCR\\tessdata\\")
        
        # Atualiza config
        update_config_file(tesseract_path)
        print()
        print("✅ Configuração concluída!")
        print()
        print("Próximos passos:")
        print("1. Reinicie a API: python run_api.py")
        print("2. O Tesseract estará disponível no ensemble")
        
        return 0
    else:
        print("❌ Tesseract não encontrado")
        print()
        
        if platform.system() == "Windows":
            print("Deseja instalar automaticamente? (s/n): ", end='')
            response = input().strip().lower()
            
            if response == 's':
                if install_tesseract_automatically():
                    return 0
            else:
                print()
                print("📝 Instruções manuais:")
                print()
                print("1. Baixe: https://github.com/UB-Mannheim/tesseract/wiki")
                print("2. Instale e marque 'Add to PATH' e 'Portuguese'")
                print("3. Execute este script novamente")
        
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
