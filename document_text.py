"""Bounded text-only extraction. Worker reads bytes on stdin; no network or OCR."""
import io,json,sys,zipfile,xml.etree.ElementTree as ET

MAX_BYTES=2_000_000

def extract(name,data):
    if not isinstance(name,str) or not name or len(name)>100 or any(c in name for c in ['/', '\\', '\x00']):raise ValueError('Neplatný název souboru.')
    if not data or len(data)>MAX_BYTES:raise ValueError('Soubor musí mít nejvýše 2 MB.')
    fragments=[];warnings=[];kind=name.rsplit('.',1)[-1].lower()
    if kind=='pdf':
        import pypdf
        with pypdf.apply_configuration(maximum_declared_stream_length=8_000_000,zlib_maximum_output_length=8_000_000,array_based_stream_maximum_output_length=8_000_000,stream_decoding_work_maximum_length=32_000_000,page_tree_maximum_entries=1000,xform_maximum_invocations_per_extraction=200,dictionary_maximum_element_count=10000,array_maximum_element_count=10000):
            reader=pypdf.PdfReader(io.BytesIO(data),strict=True,xref_stream_maximum_entries=50000,root_object_recovery_limit=2000)
            if reader.is_encrypted:raise ValueError('Šifrované PDF není podporované.')
            if not 0<len(reader.pages)<=50:raise ValueError('PDF smí mít nejvýše 50 stran.')
            for number,page in enumerate(reader.pages,1):
                text=page.extract_text() or ''
                if text.strip():
                    if sum(len(f['text']) for f in fragments)+len(text)>100000:raise ValueError('Extrahovaný text překračuje 100 000 znaků.')
                    fragments.append({'locator':'Strana '+str(number),'text':text.strip()})
                else:warnings.append('Strana '+str(number)+' neobsahuje čitelný text; OCR není zapnuté.')
    elif kind=='docx':
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries=archive.infolist()
            if len(entries)>256 or len({e.filename for e in entries})!=len(entries) or sum(e.file_size for e in entries)>8_000_000:raise ValueError('DOCX překračuje limit archivu.')
            if any(e.flag_bits&1 or 'vbaproject' in e.filename.lower() or '/embeddings/' in e.filename.lower() for e in entries):raise ValueError('Šifrovaný obsah, makra a vložené objekty se odmítají.')
            with archive.open('word/document.xml') as stream:xml=stream.read(8_000_001)
            if len(xml)>8_000_000 or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():raise ValueError('Nepodporované XML dokumentu.')
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            for number,paragraph in enumerate(ET.fromstring(xml).findall('.//w:p',ns),1):
                text=''.join(node.text or '' for node in paragraph.findall('.//w:t',ns)).strip()
                if text:fragments.append({'locator':'Odstavec '+str(number),'text':text})
    elif kind in ['md','txt']:
        text=data.decode('utf-8-sig')
        fragments=[{'locator':'Odstavec '+str(i),'text':part.strip()} for i,part in enumerate(text.split('\n\n'),1) if part.strip()]
    else:raise ValueError('Podporované jsou PDF, DOCX, TXT a Markdown.')
    if not fragments:raise ValueError('Dokument neobsahuje čitelný text. Sken vyžaduje samostatné OCR.')
    if len(fragments)>2000 or sum(len(f['text']) for f in fragments)>100000:raise ValueError('Extrahovaný text překračuje 100 000 znaků nebo 2 000 úseků.')
    content='';locators=[]
    for fragment in fragments:
        content+='['+fragment['locator']+']\n';start=len(content);content+=fragment['text'];locators.append({'label':fragment['locator'],'start':start,'end':len(content)});content+='\n\n'
    return {'content':content,'locators':locators,'warnings':warnings,'sourceType':kind}

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:result=extract(sys.argv[1],sys.stdin.buffer.read(MAX_BYTES+1));print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        message=str(error) if isinstance(error,(ValueError,UnicodeError)) else 'Dokument nelze bezpečně přečíst; ověřte formát a instalaci pypdf.'
        print(json.dumps({'error':message},ensure_ascii=False));sys.exit(1)
