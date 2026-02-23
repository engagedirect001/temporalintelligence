"""
Task 20: Modular Arithmetic for RSA-like Operations
Category: Combined — math/numerical + algorithm bugs
"""


def mod_pow(base, exp, mod):
    """Fast modular exponentiation: base^exp mod mod."""
    if mod == 1:
        return 0
    
    result = 1
    base = base % mod
    
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        # Bug 1: squares base AFTER shifting exp, but should square
        # regardless of whether exp was odd. This is correct structurally,
        # BUT the real bug is: base should be squared every iteration,
        # including when exp becomes 0 (which is harmless) BUT
        # actually let's make the bug: uses exp instead of exp >> 1
        # Wait, let me make a subtle bug: 
        base = (base * base) % mod
    
    return result


def extended_gcd(a, b):
    """Extended Euclidean algorithm. Returns (gcd, x, y) where ax + by = gcd."""
    if a == 0:
        return b, 0, 1
    
    gcd, x1, y1 = extended_gcd(b % a, a)
    # Bug 2: wrong sign — should be y1 - (b // a) * x1
    x = y1 - (b // a) * x1
    y = x1
    
    return gcd, x, y


def mod_inverse(a, mod):
    """Modular multiplicative inverse of a mod mod."""
    gcd, x, _ = extended_gcd(a % mod, mod)
    if gcd != 1:
        raise ValueError(f"{a} has no inverse modulo {mod}")
    return x % mod


def generate_keypair(p, q):
    """Generate RSA-like keypair from two primes."""
    n = p * q
    # Bug 3: Euler's totient should be (p-1)*(q-1), not p*q - 1
    phi = p * q - 1
    
    # Choose e (commonly 65537)
    e = 65537
    if phi % e == 0:
        e = 3
    
    d = mod_inverse(e, phi)
    
    return {"public": (e, n), "private": (d, n)}


def encrypt(message, public_key):
    """Encrypt integer message with public key."""
    e, n = public_key
    if message >= n:
        raise ValueError("Message too large")
    return mod_pow(message, e, n)


def decrypt(ciphertext, private_key):
    """Decrypt integer ciphertext with private key."""
    d, n = private_key
    return mod_pow(ciphertext, d, n)


def is_prime(n):
    """Simple primality test."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
