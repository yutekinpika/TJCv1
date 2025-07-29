# app/wallet.py

import hashlib
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

# --- 鍵ペアの生成 ---
def generate_keypair():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    priv_hex = sk.to_string().hex()
    pub_hex = vk.to_string("uncompressed").hex()
    return priv_hex, pub_hex

# --- メッセージに署名 ---
def sign_message(private_key_hex, message: str) -> str:
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    signature = sk.sign(message.encode('utf-8'))
    return signature.hex()

# --- 署名を検証 ---
def verify_signature(public_key_hex, message: str, signature_hex: str) -> bool:
    try:
        # ✅ 先頭の「04」を除いて VerifyingKey を生成
        key_bytes = bytes.fromhex(public_key_hex)
        if key_bytes[0] != 0x04:
            print("Invalid prefix byte for uncompressed key")
            return False
        vk = VerifyingKey.from_string(key_bytes[1:], curve=SECP256k1)

        return vk.verify(bytes.fromhex(signature_hex), message.encode('utf-8'))
    except Exception as e:
        print(f'検証失敗: {e}')
        return False

# --- 公開鍵からアドレス（公開鍵ハッシュ）を生成 ---
def pubkey_to_address(public_key_hex: str) -> str:
    # Step 1: SHA256
    sha = hashlib.sha256(bytes.fromhex(public_key_hex)).digest()
    # Step 2: RIPEMD160
    ripemd = hashlib.new('ripemd160')
    ripemd.update(sha)
    return ripemd.hexdigest()  # これが「アドレス」（公開鍵ハッシュ）

def verify_user_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    try:
        # 公開鍵はプレフィックス付き（例: 04xxxxxx...）を想定
        if public_key_hex.startswith("04"):
            public_key_hex = public_key_hex[2:]  # 先頭"04"を除去

        # 公開鍵からVerifyingKeyを生成（uncompressed keyを前提）
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        
        # 検証
        return vk.verify(bytes.fromhex(signature_hex), message.encode('utf-8'))
    
    except BadSignatureError:
        print("署名が無効です")
        return False
    except Exception as e:
        print(f"署名検証エラー: {e}")
        return False

if __name__ == "__main__":
    # 鍵ペア生成
    priv, pub = generate_keypair()
    print("Private:", priv)
    print("Public :", pub)
    print("Address:", pubkey_to_address(pub))

    # 署名と検証
    msg = "send 10 TJC to Alice"
    sig = sign_message(priv, msg)
    print("Signature:", sig)
    print("Verified :", verify_signature(pub, msg, sig))