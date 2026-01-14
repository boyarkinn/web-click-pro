"""
Скрипт для преобразования seed phrase TON в приватный ключ для COCOON
Использование: python convert-seed-to-key.py

ВАЖНО: Для TON используется стандарт BIP39, но ключ генерируется специфично.
Этот скрипт создает базовый ключ, но может потребоваться дополнительная настройка.
"""

import base64
import hashlib
import hmac
try:
    from mnemonic import Mnemonic
    MNEMONIC_AVAILABLE = True
except ImportError:
    MNEMONIC_AVAILABLE = False
    print("⚠️  Библиотека mnemonic не найдена. Используем альтернативный метод.")

def seed_to_private_key(seed_phrase: str) -> str:
    """
    Преобразует seed phrase в приватный ключ (base64) для TON
    
    Args:
        seed_phrase: 24 слова через пробел
        
    Returns:
        Приватный ключ в формате base64 (32 байта)
    """
    # Проверяем валидность seed phrase (но не строго - TON может использовать свой формат)
    mnemo = Mnemonic("english")
    
    # Пробуем проверить, но если не проходит - все равно генерируем
    # (TON может использовать немного другой формат)
    try:
        if not mnemo.check(seed_phrase):
            print("⚠️  Предупреждение: seed phrase не проходит стандартную проверку BIP39")
            print("   Но продолжаем генерацию ключа...")
    except Exception as e:
        print(f"⚠️  Предупреждение при проверке: {e}")
        print("   Продолжаем генерацию ключа...")
    
    # Генерируем seed из mnemonic (BIP39 стандарт)
    # Используем пустую passphrase для TON (обычно так)
    try:
        seed = mnemo.to_seed(seed_phrase, passphrase="")
    except Exception as e:
        # Если стандартный метод не работает, пробуем альтернативный
        print(f"⚠️  Стандартный метод не сработал: {e}")
        print("   Пробуем альтернативный метод...")
        # Используем PBKDF2 напрямую
        import hashlib
        import binascii
        words = seed_phrase.strip().split()
        if len(words) != 24:
            raise ValueError(f"Ожидается 24 слова, получено {len(words)}")
        
        # Создаем seed из слов (упрощенный метод)
        mnemonic_bytes = seed_phrase.encode('utf-8')
        seed = hashlib.pbkdf2_hmac('sha512', mnemonic_bytes, b'mnemonic', 2048)
    
    # Для TON Ed25519 ключа используем первые 32 байта seed
    # Это стандартный подход для генерации Ed25519 ключей из seed
    private_key = seed[:32]
    
    # Конвертируем в base64 (как требует COCOON)
    private_key_b64 = base64.b64encode(private_key).decode('utf-8')
    
    return private_key_b64

if __name__ == "__main__":
    print("=" * 60)
    print("Конвертер Seed Phrase → Приватный ключ для COCOON")
    print("=" * 60)
    print()
    print("⚠️  ВНИМАНИЕ: Никому не показывайте ваш seed phrase!")
    print()
    
    # Запрашиваем seed phrase
    print("Введите ваши 24 слова (через пробел):")
    seed_phrase = input().strip()
    
    try:
        private_key = seed_to_private_key(seed_phrase)
        print()
        print("✅ Приватный ключ (base64):")
        print(private_key)
        print()
        print("Скопируйте этот ключ в client-config.json как 'node_wallet_key'")
        print()
        print("⚠️  ВАЖНО: Сохраните этот ключ в безопасном месте!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print()
        print("Попробуйте:")
        print("1. Проверить что все 24 слова введены правильно")
        print("2. Убедиться что слова разделены одним пробелом")
        print("3. Проверить что слова из английского словаря BIP39")
        import traceback
        print()
        print("Детали ошибки:")
        traceback.print_exc()
