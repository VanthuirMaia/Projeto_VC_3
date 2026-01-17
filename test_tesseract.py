"""
Script de teste para verificar instalação e configuração do Tesseract OCR
==========================================================================

Uso:
    python test_tesseract.py

Este script verifica:
1. Se pytesseract está instalado
2. Se Tesseract OCR está instalado no sistema
3. Se o caminho está configurado corretamente (Windows)
4. Se o idioma português está disponível
"""

import sys
import platform
import os
from pathlib import Path

def test_pytesseract_installed():
    """Verifica se pytesseract está instalado."""
    print("=" * 60)
    print("1. Verificando instalação do pytesseract...")
    print("=" * 60)
    
    try:
        import pytesseract
        print("✅ pytesseract está instalado")
        return pytesseract
    except ImportError:
        print("❌ pytesseract NÃO está instalado")
        print("\nSolução:")
        print("  pip install pytesseract")
        return None


def test_tesseract_executable(pytesseract):
    """Verifica se Tesseract está instalado e acessível."""
    print("\n" + "=" * 60)
    print("2. Verificando instalação do Tesseract OCR...")
    print("=" * 60)
    
    if not pytesseract:
        print("⚠️  Pulando teste (pytesseract não instalado)")
        return False
    
    try:
        # Tenta obter versão
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract encontrado (versão: {version})")
        return True
    except Exception as e:
        print(f"❌ Tesseract NÃO encontrado: {e}")
        
        # Tenta detectar caminho no Windows
        if platform.system() == "Windows":
            print("\n" + "-" * 60)
            print("🔍 Tentando detectar Tesseract no Windows...")
            print("-" * 60)
            
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\tesseract\tesseract.exe",
            ]
            
            username = os.getenv('USERNAME', '')
            if username:
                common_paths.insert(0, 
                    rf"C:\Users\{username}\AppData\Local\Tesseract-OCR\tesseract.exe"
                )
            
            found = False
            for path in common_paths:
                if os.path.exists(path):
                    print(f"✅ Tesseract encontrado em: {path}")
                    print(f"\n💡 Configure em src/config.py:")
                    print(f'   "tesseract_cmd": r"{path}",')
                    pytesseract.pytesseract.tesseract_cmd = path
                    found = True
                    
                    # Testa novamente
                    try:
                        version = pytesseract.get_tesseract_version()
                        print(f"✅ Configuração funcionando! Versão: {version}")
                        return True
                    except:
                        print("⚠️  Caminho encontrado, mas ainda não funciona")
                    break
            
            if not found:
                print("❌ Tesseract não encontrado nos caminhos comuns")
                print("\nSolução:")
                print("  1. Baixe e instale Tesseract:")
                print("     https://github.com/UB-Mannheim/tesseract/wiki")
                print("  2. Configure manualmente em src/config.py:")
                print('     "tesseract_cmd": r"C:\\...\\tesseract.exe",')
        
        elif platform.system() == "Linux":
            print("\nSolução:")
            print("  sudo apt-get install tesseract-ocr")
            print("  sudo apt-get install tesseract-ocr-por")
        
        elif platform.system() == "Darwin":  # macOS
            print("\nSolução:")
            print("  brew install tesseract")
            print("  brew install tesseract-lang")
        
        return False


def test_portuguese_language(pytesseract):
    """Verifica se o idioma português está disponível."""
    print("\n" + "=" * 60)
    print("3. Verificando idioma português...")
    print("=" * 60)
    
    if not pytesseract:
        print("⚠️  Pulando teste (pytesseract não instalado)")
        return False
    
    try:
        # Lista idiomas disponíveis
        languages = pytesseract.get_languages(config='')
        
        if 'por' in languages:
            print("✅ Português (por) está disponível")
            return True
        elif 'eng' in languages:
            print("⚠️  Português (por) NÃO está disponível")
            print(f"   Idiomas disponíveis: {', '.join(languages)}")
            print("\nSolução:")
            if platform.system() == "Windows":
                print("  Baixe o pacote de idiomas durante a instalação,")
                print("  ou baixe de: https://github.com/tesseract-ocr/tessdata")
                print("  Copie por.traineddata para:")
                print("  C:\\Program Files\\Tesseract-OCR\\tessdata\\")
            elif platform.system() == "Linux":
                print("  sudo apt-get install tesseract-ocr-por")
            elif platform.system() == "Darwin":
                print("  brew install tesseract-lang")
            return False
        else:
            print(f"⚠️  Idiomas encontrados: {', '.join(languages)}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar idiomas: {e}")
        return False


def test_ocr_functionality(pytesseract):
    """Testa funcionalidade básica de OCR."""
    print("\n" + "=" * 60)
    print("4. Testando funcionalidade de OCR...")
    print("=" * 60)
    
    if not pytesseract:
        print("⚠️  Pulando teste (pytesseract não instalado)")
        return False
    
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # Cria imagem de teste com texto
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        # Tenta usar fonte padrão, senão desenha simples
        try:
            # Tenta usar fonte Arial (Windows) ou DejaVu Sans (Linux)
            if platform.system() == "Windows":
                font = ImageFont.truetype("arial.ttf", 20)
            else:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 10), "TESTE OCR 123", fill='black', font=font)
        
        # Converte para numpy array (formato esperado pelo código)
        img_array = np.array(img)
        
        # Testa OCR
        text = pytesseract.image_to_string(img_array, lang='por', config='--psm 6')
        
        print("✅ OCR funcionando corretamente!")
        print(f"   Texto reconhecido: '{text.strip()}'")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar OCR: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "TESTE DE INSTALAÇÃO DO TESSERACT OCR" + " " * 10 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Testa instalação do pytesseract
    pytesseract = test_pytesseract_installed()
    
    # Testa Tesseract executável
    tesseract_ok = test_tesseract_executable(pytesseract)
    
    # Testa idioma português
    language_ok = test_portuguese_language(pytesseract)
    
    # Testa funcionalidade
    ocr_ok = test_ocr_functionality(pytesseract) if pytesseract else False
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"pytesseract instalado:     {'✅' if pytesseract else '❌'}")
    print(f"Tesseract encontrado:       {'✅' if tesseract_ok else '❌'}")
    print(f"Idioma português:           {'✅' if language_ok else '❌'}")
    print(f"OCR funcionando:            {'✅' if ocr_ok else '❌'}")
    print("=" * 60)
    
    if pytesseract and tesseract_ok and language_ok and ocr_ok:
        print("\n🎉 Tudo funcionando perfeitamente!")
        print("   O Tesseract está pronto para uso na API.")
        return 0
    else:
        print("\n⚠️  Alguns problemas foram encontrados.")
        print("   Siga as instruções acima para corrigir.")
        return 1


if __name__ == "__main__":
    sys.exit(main())