import numpy as np
import hashlib
import cv2
from PIL import Image
import os

# ----------------- DNA Encoding Logic -----------------
DNA_MAP = {
    "00": "A", "01": "T", "10": "G", "11": "C",
    "A": [0, 0], "T": [0, 1], "G": [1, 0], "C": [1, 1],
    "AA": "A", "TT": "A", "GG": "A", "CC": "A",
    "AG": "G", "GA": "G", "TC": "G", "CT": "G",
    "AC": "C", "CA": "C", "GT": "C", "TG": "C",
    "AT": "T", "TA": "T", "CG": "T", "GC": "T"
}

DNA_SYMBOLS = np.array(["A", "T", "G", "C"])

def dna_encode(channel):
    bits = np.unpackbits(channel, axis=1)
    m, n = bits.shape
    dna_encoded = np.empty((m, n // 2), dtype='<U1')
    for i in range(0, n, 2):
        pair = bits[:, i] * 2 + bits[:, i + 1]
        dna_encoded[:, i // 2] = DNA_SYMBOLS[pair]
    return dna_encoded

def dna_decode(encoded):
    m, n = encoded.shape
    bits = np.zeros((m, n * 2), dtype=np.uint8)
    for j in range(m):
        for i in range(n):
            ch = encoded[j, i]
            bits[j, 2*i], bits[j, 2*i+1] = DNA_MAP[ch]
    return np.packbits(bits, axis=1).astype(np.uint8)

# ----------------- Key Matrix Generation -----------------
def get_sha256_key(image_array):
    sha = hashlib.sha256()
    sha.update(image_array.tobytes())
    return sha.hexdigest()

def generate_key_matrix(shape, hex_key):
    m, n = shape
    key_bin = bin(int(hex_key, 16))[2:].zfill(256)
    key_bits = np.array([int(b) for b in key_bin], dtype=np.uint8)
    total_bits = m * n * 2
    repeated = np.tile(key_bits, (total_bits // 256 + 1))[:total_bits]
    bits = repeated.reshape(m, n * 2)
    matrix = np.empty((m, n), dtype='<U1')
    for i in range(0, n * 2, 2):
        pair = bits[:, i] * 2 + bits[:, i+1]
        matrix[:, i // 2] = DNA_SYMBOLS[pair]
    return matrix

# ----------------- XOR Operation -----------------
def dna_xor(a, b):
    m, n = a.shape
    res = np.empty((m, n), dtype='<U1')
    for i in range(m):
        for j in range(n):
            res[i, j] = DNA_MAP[a[i, j] + b[i, j]]
    return res

# ----------------- Chaos: Chirikov + Chebyshev -----------------
def generate_combined_chaos(m, n, K=0.5):
    total = m * n
    p = np.zeros(total)
    theta = np.zeros(total)
    x_cheb = np.zeros(total)

    # Initial conditions
    p[0] = 0.3
    theta[0] = 0.4
    x_cheb[0] = 0.6

    for i in range(1, total):
        p[i] = (p[i - 1] + K * np.sin(theta[i - 1])) % (2 * np.pi)
        theta[i] = (theta[i - 1] + p[i]) % (2 * np.pi)
        x_cheb[i] = 1 - 2 * (x_cheb[i - 1] ** 2)

    # Normalize sequences
    x_norm = (theta % (2 * np.pi)) / (2 * np.pi)
    y_norm = (x_cheb + 1) / 2
    z_norm = (x_norm + y_norm) % 1

    fx = np.argsort(np.argsort(x_norm))
    fy = np.argsort(np.argsort(y_norm))
    fz = np.argsort(np.argsort(z_norm))
    return fx, fy, fz

# ----------------- Scrambling -----------------
def scramble(fx, fy, fz, r, g, b):
    flat_r, flat_g, flat_b = r.flatten(), g.flatten(), b.flatten()
    sr = flat_r[fx].reshape(r.shape)
    sg = flat_g[fy].reshape(g.shape)
    sb = flat_b[fz].reshape(b.shape)
    return sr, sg, sb

def unscramble(fx, fy, fz, sr, sg, sb):
    m, n = sr.shape
    total = m * n
    orig_r = np.empty(total, dtype='<U1')
    orig_g = np.empty(total, dtype='<U1')
    orig_b = np.empty(total, dtype='<U1')
    flat_sr, flat_sg, flat_sb = sr.flatten(), sg.flatten(), sb.flatten()
    orig_r[fx] = flat_sr
    orig_g[fy] = flat_sg
    orig_b[fz] = flat_sb
    return orig_r.reshape(m, n), orig_g.reshape(m, n), orig_b.reshape(m, n)

# ----------------- Encrypt / Decrypt -----------------
def encrypt(img_np, key_hex):
    r, g, b = img_np[:, :, 0], img_np[:, :, 1], img_np[:, :, 2]
    r_dna, g_dna, b_dna = dna_encode(r), dna_encode(g), dna_encode(b)
    key_matrix = generate_key_matrix(r_dna.shape, key_hex)
    r_xor = dna_xor(r_dna, key_matrix)
    g_xor = dna_xor(g_dna, key_matrix)
    b_xor = dna_xor(b_dna, key_matrix)
    fx, fy, fz = generate_combined_chaos(*r_dna.shape)
    sr, sg, sb = scramble(fx, fy, fz, r_xor, g_xor, b_xor)
    r_final, g_final, b_final = dna_decode(sr), dna_decode(sg), dna_decode(sb)
    return np.stack([r_final, g_final, b_final], axis=2), fx, fy, fz, key_matrix

def decrypt(enc_img_np, fx, fy, fz, key_matrix):
    r, g, b = enc_img_np[:, :, 0], enc_img_np[:, :, 1], enc_img_np[:, :, 2]
    r_dna, g_dna, b_dna = dna_encode(r), dna_encode(g), dna_encode(b)
    r_un, g_un, b_un = unscramble(fx, fy, fz, r_dna, g_dna, b_dna)
    r_xor = dna_xor(r_un, key_matrix)
    g_xor = dna_xor(g_un, key_matrix)
    b_xor = dna_xor(b_un, key_matrix)
    r_dec, g_dec, b_dec = dna_decode(r_xor), dna_decode(g_xor), dna_decode(b_xor)
    return np.stack([r_dec, g_dec, b_dec], axis=2)




# ----------------- Execution -----------------
if __name__ == "__main__":
    if not os.path.exists("test.png"):
        print("❗ Please place a test image named 'test.png' in the current folder.")
    else:
        img = Image.open("test.png").convert("RGB")
        img_np = np.array(img)
        key = get_sha256_key(img_np)

        enc_np, fx, fy, fz, key_matrix = encrypt(img_np, key)
        Image.fromarray(enc_np).save("enc1.png")
        print("✅ Encrypted image saved as enc.png")

        dec_np = decrypt(enc_np, fx, fy, fz, key_matrix)
        Image.fromarray(dec_np).save("dec1.png")
        print("✅ Decrypted image saved as dec.png")
