import secrets
secret = secrets.token_hex(16)
with open("config.py","w", encoding="utf-8") as f:
    f.write("SECRET_KEY = \"" + str(secret) + "\"\n")
