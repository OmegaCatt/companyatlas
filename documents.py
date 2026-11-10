import base64,hashlib,json,subprocess,sys,uuid,os
from pathlib import Path

def init(connection):
    connection.executescript('''CREATE TABLE IF NOT EXISTS document_meta(id TEXT PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,version INTEGER NOT NULL,source_type TEXT NOT NULL,sha256 TEXT NOT NULL,locators TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS catalog_revision(id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL);
      INSERT OR IGNORE INTO catalog_revision VALUES(1,1);''')

def revision(connection):return connection.execute('SELECT revision FROM catalog_revision WHERE id=1').fetchone()[0]

def decorate(connection,document):
    row=connection.execute('SELECT * FROM document_meta WHERE id=?',(document['id'],)).fetchone()
    document.update({'version':row['version'] if row else 1,'sourceType':row['source_type'] if row else document['kind'],'sha256':hashlib.sha256(document['content'].encode()).hexdigest(),'locators':json.loads(row['locators']) if row else [],'indexStatus':'ready'})
    return document

def import_document(connection,body):
    name=body.get('filename');encoded=body.get('data');title=body.get('title');group=body.get('group')
    if not isinstance(title,str) or not 1<=len(title.strip())<=150 or group not in ['shared','operations','people','leadership']:raise ValueError('Vyplňte název a povolenou oblast dokumentu.')
    if not isinstance(encoded,str) or len(encoded)>2_700_000:raise ValueError('Limit souboru je 2 MB.')
    data=base64.b64decode(encoded,validate=True)
    if len(data)>2_000_000:raise ValueError('Limit souboru je 2 MB.')
    environment=dict(os.environ);environment['PYTHONIOENCODING']='utf-8';environment.pop('OPENAI_API_KEY',None)
    process=subprocess.run([sys.executable,str(Path(__file__).with_name('document_text.py')),str(name)],input=data,capture_output=True,timeout=15,env=environment,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:parsed=json.loads(process.stdout.decode('utf-8'))
    except (ValueError,UnicodeError):raise ValueError('Čtení dokumentu selhalo.')
    if process.returncode:raise ValueError(parsed.get('error','Dokument nelze přečíst.'))
    key=body.get('id') or 'doc-'+uuid.uuid4().hex
    with connection:
        connection.execute('BEGIN IMMEDIATE')
        existing=connection.execute('SELECT * FROM documents WHERE id=?',(key,)).fetchone()
        if body.get('id') and not existing:raise ValueError('Nahrazovaný dokument již neexistuje.')
        if existing and existing['kind']=='csv':raise ValueError('Ukázkové datové CSV se tímto importem nemění.')
        old=connection.execute('SELECT version FROM document_meta WHERE id=?',(key,)).fetchone()
        version=(old['version'] if old else 1)+1 if existing else 1
        if existing and body.get('expectedVersion')!=(old['version'] if old else 1):raise ValueError('Verze se mezitím změnila. Načtěte dokument znovu.')
        if not existing and connection.execute("SELECT COUNT(*) FROM documents WHERE path LIKE 'import/%'").fetchone()[0]>=30:raise ValueError('Limit je 30 importovaných dokumentů.')
        connection.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,group_name=excluded.group_name,content=excluded.content,description=excluded.description',(key,existing['path'] if existing else 'import/'+key+'/'+name,title.strip(),group,'document',name+' · textový index',parsed['content']))
        connection.execute('INSERT INTO document_meta VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET version=excluded.version,source_type=excluded.source_type,sha256=excluded.sha256,locators=excluded.locators',(key,version,parsed['sourceType'],hashlib.sha256(parsed['content'].encode()).hexdigest(),json.dumps(parsed['locators'],ensure_ascii=False)))
        connection.execute('UPDATE catalog_revision SET revision=revision+1 WHERE id=1')
    return {'id':key,'version':version,'warnings':parsed['warnings'],'indexStatus':'ready'}

def remove_document(connection,key,expected):
    with connection:
        connection.execute('BEGIN IMMEDIATE')
        row=connection.execute('SELECT d.kind,COALESCE(m.version,1) version FROM documents d LEFT JOIN document_meta m USING(id) WHERE d.id=?',(key,)).fetchone()
        if not row or row['kind']=='csv' or row['version']!=expected:raise ValueError('Dokument nelze odebrat: chybí, je datové CSV nebo má jinou verzi.')
        connection.execute('DELETE FROM documents WHERE id=?',(key,));connection.execute('UPDATE catalog_revision SET revision=revision+1 WHERE id=1')

def locator(document,quote):
    start=document['content'].find(quote)
    return next((item['label'] for item in document.get('locators',[]) if item['start']<=start<item['end']),None)
