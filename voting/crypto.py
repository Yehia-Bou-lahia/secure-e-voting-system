import random
import hashlib
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
#======== دوال رياضية مساعدة=========
def gcd(a, b):
    """القاسم المشترك الأكبر """
    while b:
        a, b = b, a % b
    return a

def egcd(a,b):
    """حساب القاسم المشترك الأكبر بين عددين صحيحين"""
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    """باقي القسمة لـ a modulo m (يفترض أن gcd(a,m)=1)"""
    g, x, y = egcd(a, m)
    if g != 1:
        raise ValueError("No modular inverse")
    return x % m

#=============== إختبار الأعداد الأولية ==============
def is_prime(n, k=5):
    """Miller-Rabin primality test (k = عدد التكرارات)"""
    if n < 2:
        return False
    # الأعداد الصغيرة المعروفة
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    for p in small_primes:
        if n % p == 0:
            return n == p
    # كتابة n-1 = d * 2^r
    r = 0
    d = n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    # اختبار k مرة
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def generate_prime(bits=16):
    """توليد عدد أولي بحجم bits (bits >= 4)"""
    while True:
        p = random.getrandbits(bits)
        # التأكد أن العدد فردي وليس صغيراً جداً
        p |= (1 << bits - 1) | 1
        if is_prime(p):
            return p

# -------------------- توليد مفاتيح RSA --------------------
def generate_rsa_keypair(bits=16):
    """
    توليد زوج مفاتيح RSA (public, private)
    bits: عدد البتات لكل من p و q (أي أن n سيكون بحجم ~2*bits)
    الإرجاع: (public_key, private_key) حيث كل مفتاح عبارة عن (exponent, n)
    """
    p = generate_prime(bits)
    q = generate_prime(bits)
    while q == p:
        q = generate_prime(bits)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537  # قيمة ثابتة شائعة
    # إذا لم يكن e أولياً مع phi، نجد e آخر
    while gcd(e, phi) != 1:
        e = random.randrange(2, phi)
    d = modinv(e, phi)
    public_key = (e, n)
    private_key = (d, n)
    return public_key, private_key

# -------------------- تحويل النصوص إلى أعداد والعكس --------------------
def text_to_int(text):
    """تحويل نص UTF-8 إلى عدد صحيح (big-endian)"""
    return int.from_bytes(text.encode('utf-8'), 'big')

def int_to_text(num):
    """تحويل عدد صحيح إلى نص UTF-8"""
    # حساب عدد البايتات اللازمة
    length = (num.bit_length() + 7) // 8
    return num.to_bytes(length, 'big').decode('utf-8')

# -------------------- تشفير وفك تشفير الرسائل --------------------
def encrypt(message_int, public_key):
    """
    تشفير عدد صحيح باستخدام المفتاح العمومي (e, n)
    الإرجاع: العدد المشفر
    """
    e, n = public_key
    if message_int >= n:
        raise ValueError("الرسالة أكبر من n، قم بتقسيمها أو استخدم n أكبر")
    return pow(message_int, e, n)

def decrypt(cipher_int, private_key):
    """
    فك تشفير عدد صحيح باستخدام المفتاح الخاص (d, n)
    الإرجاع: العدد الأصلي
    """
    d, n = private_key
    return pow(cipher_int, d, n)

# -------------------- التوقيع الرقمي والتحقق --------------------
def hash_message(message):
    """حساب SHA-256 لرسالة نصية وإرجاع التجزئة كعدد صحيح"""
    h = hashlib.sha256(message.encode('utf-8')).hexdigest()
    return int(h, 16)

def sign(message, private_key):
    """
    توقيع رسالة نصية باستخدام المفتاح الخاص.
    الخطوات:
      1. حساب تجزئة الرسالة (SHA-256).
      2. تحويل التجزئة إلى عدد صحيح.
      3. تطبيق عملية RSA على التجزئة (raise to d mod n).
    الإرجاع: التوقيع كنص (base64)
    """
    h_int = hash_message(message)
    d, n = private_key
    signature_int = pow(h_int, d, n)
    # تحويل التوقيع إلى bytes ثم base64
    signature_bytes = signature_int.to_bytes((signature_int.bit_length() + 7) // 8, 'big')
    return base64.b64encode(signature_bytes).decode('utf-8')

def verify(message, signature_b64, public_key):
    """
    التحقق من توقيع رسالة نصية باستخدام المفتاح العمومي.
    الإرجاع: True إذا كان التوقيع صحيحاً، False خلاف ذلك.
    """
    e, n = public_key
    try:
        signature_bytes = base64.b64decode(signature_b64)
        signature_int = int.from_bytes(signature_bytes, 'big')
        # فك التوقيع باستخدام المفتاح العمومي (raise to e mod n)
        decrypted_hash = pow(signature_int, e, n)
        # حساب التجزئة الأصلية للرسالة
        original_hash = hash_message(message)
        return decrypted_hash == original_hash
    except Exception:
        return False

# -------------------- دوال مساعدة للتعامل مع النصوص الطويلة (اختياري) --------------------
def encrypt_long_text(plain_text, public_key):
    """تشفير نص طويل بتقسيمه إلى كتل (نظراً لمحدودية حجم n)"""
    e, n = public_key
    max_block_size = (n.bit_length() - 1) // 8  # أقصى عدد بايتات لكل كتلة
    plain_bytes = plain_text.encode('utf-8')
    cipher_blocks = []
    for i in range(0, len(plain_bytes), max_block_size):
        block = plain_bytes[i:i+max_block_size]
        block_int = int.from_bytes(block, 'big')
        encrypted_int = pow(block_int, e, n)
        cipher_blocks.append(encrypted_int)
    # تحويل القائمة إلى سلسلة base64 (للإرسال)
    return base64.b64encode(str(cipher_blocks).encode('utf-8')).decode('utf-8')

def decrypt_long_text(cipher_b64, private_key):
    """فك تشفير النص الطويل"""
    d, n = private_key
    cipher_str = base64.b64decode(cipher_b64).decode('utf-8')
    cipher_blocks = eval(cipher_str)  # آمن في بيئة محكومة
    plain_bytes = b''
    for block_int in cipher_blocks:
        decrypted_int = pow(block_int, d, n)
        block_bytes = decrypted_int.to_bytes((decrypted_int.bit_length() + 7) // 8, 'big')
        plain_bytes += block_bytes
    return plain_bytes.decode('utf-8')

def pem_to_public_numbers(pem_key: str):
    """
    تحويل مفتاح عمومي بصيغة PEM إلى (e, n)
    """
    public_key = serialization.load_pem_public_key(pem_key.encode(), backend=default_backend())
    numbers = public_key.public_numbers()
    return (numbers.e, numbers.n)

def pem_to_private_numbers(pem_key: str):
    """
    تحويل مفتاح خاص بصيغة PEM إلى (d, n)
    """
    private_key = serialization.load_pem_private_key(pem_key.encode(), password=None, backend=default_backend())
    private_numbers = private_key.private_numbers()
    public_numbers = private_numbers.public_numbers
    return (private_numbers.d, public_numbers.n)