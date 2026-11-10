import hashlib,hmac,secrets,time

DEMO_PASSWORD='AtlasDemo-2026'
DEMO_USERS=('operations','people','leadership')

def digest(password,salt):return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()

def init(connection):
    connection.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,role TEXT NOT NULL,salt TEXT NOT NULL,password_hash TEXT NOT NULL,active INTEGER NOT NULL,revision INTEGER NOT NULL)')
    with connection:
        for name in DEMO_USERS:
            if not connection.execute('SELECT 1 FROM users WHERE username=?',(name,)).fetchone():
                salt=secrets.token_hex(16);connection.execute('INSERT INTO users VALUES(?,?,?,?,1,1)',(name,name,salt,digest(DEMO_PASSWORD,salt)))

def authenticate(connection,username,password):
    if not isinstance(username,str) or not isinstance(password,str) or len(username)>80 or len(password)>256:return None
    user=connection.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
    salt=user['salt'] if user else '00'*16
    candidate=digest(password,salt)
    if not user or not user['active'] or not hmac.compare_digest(candidate,user['password_hash']):return None
    return {'username':user['username'],'role':user['role'],'revision':user['revision']}

def identity(connection,username,revision):
    row=connection.execute('SELECT username,role,revision FROM users WHERE username=? AND active=1 AND revision=?',(username,revision)).fetchone()
    return dict(row) if row else None

def toggle(connection,username,active):
    if username not in DEMO_USERS or username=='leadership' or type(active) is not bool:raise ValueError('Tento účet nelze změnit.')
    with connection:connection.execute('UPDATE users SET active=?,revision=revision+1 WHERE username=?',(int(active),username))
