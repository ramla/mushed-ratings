import secrets
secret = secrets.token_hex(16)
with open("config.py","w") as f:
    f.write("secret_key = " + str(secret))