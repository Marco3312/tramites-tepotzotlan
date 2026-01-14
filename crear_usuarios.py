import bcrypt

# Genera hashes seguros
def hash_password(pwd):
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("=== GENERADOR DE CONTRASEÑAS SEGURAS ===")
print("MIGUELANGEL -> ayuntamiento123")
print(hash_password('ayuntamiento123'))

print("\nULISESRAQUEL -> ayuntamiento123")
print(hash_password('ayuntamiento123'))

print("\npasante -> escuela123")
print(hash_password('escuela123'))