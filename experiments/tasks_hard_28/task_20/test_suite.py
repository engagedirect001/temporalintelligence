import pytest
from buggy_code import mod_pow, extended_gcd, mod_inverse, generate_keypair, encrypt, decrypt, is_prime


def test_mod_pow_basic():
    assert mod_pow(2, 10, 1000) == 1024
    assert mod_pow(3, 5, 13) == 243 % 13


def test_mod_pow_large():
    # 7^256 mod 13
    result = mod_pow(7, 256, 13)
    assert result == pow(7, 256, 13)


def test_mod_pow_edge_cases():
    assert mod_pow(0, 5, 7) == 0
    assert mod_pow(5, 0, 7) == 1
    assert mod_pow(5, 1, 7) == 5


def test_extended_gcd():
    """Bug 2: wrong formula gives incorrect Bezout coefficients."""
    gcd, x, y = extended_gcd(35, 15)
    assert gcd == 5
    assert 35 * x + 15 * y == 5, f"35*{x} + 15*{y} = {35*x + 15*y}, expected 5"


def test_extended_gcd_coprime():
    gcd, x, y = extended_gcd(17, 13)
    assert gcd == 1
    assert 17 * x + 13 * y == 1


def test_mod_inverse():
    inv = mod_inverse(3, 7)
    assert (3 * inv) % 7 == 1


def test_mod_inverse_larger():
    inv = mod_inverse(17, 43)
    assert (17 * inv) % 43 == 1


def test_rsa_encrypt_decrypt():
    """Bug 3: wrong totient breaks RSA."""
    p, q = 61, 53
    keys = generate_keypair(p, q)
    
    message = 42
    ciphertext = encrypt(message, keys["public"])
    decrypted = decrypt(ciphertext, keys["private"])
    
    assert decrypted == message, \
        f"RSA decrypt failed: encrypted {message}, got back {decrypted}"


def test_rsa_different_messages():
    p, q = 101, 103
    keys = generate_keypair(p, q)
    
    for msg in [0, 1, 100, 1000, 5000]:
        ct = encrypt(msg, keys["public"])
        pt = decrypt(ct, keys["private"])
        assert pt == msg, f"Failed for message {msg}: got {pt}"


def test_is_prime():
    assert is_prime(2) is True
    assert is_prime(17) is True
    assert is_prime(15) is False
    assert is_prime(1) is False


def test_mod_inverse_no_inverse():
    with pytest.raises(ValueError):
        mod_inverse(4, 8)  # gcd(4,8) = 4 ≠ 1
