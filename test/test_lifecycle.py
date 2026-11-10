import base64,io,json,tempfile,threading,unittest,zipfile
from pathlib import Path
from contextlib import closing
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from reportlab.pdfgen import canvas
from pypdf import PdfWriter
from server import create_server
from core import connect,answer_question,get_document
from document_text import extract

def pdf(text='Fiktivni servisni pozadavek do 6 hodin.'):
    stream=io.BytesIO();document=canvas.Canvas(stream);document.drawString(50,750,text);document.showPage();document.save();return stream.getvalue()
def docx(text='Fiktivní nákup schvaluje vedoucí.'):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'+text+'</w:t></w:r></w:p></w:body></w:document>')
    return stream.getvalue()

class DocumentParsingTests(unittest.TestCase):
    def test_later_page_retrieval_and_citation_location(self):
        from ai import build_payload
        from documents import locator
        content='Úvod bez odpovědi. '*250+'\nServisní eskalace má lhůtu šest hodin.'
        split=content.index('\nServisní')
        document={'id':'later','title':'Servis','content':content,'locators':[{'label':'Strana 1','start':0,'end':split},{'label':'Strana 2','start':split,'end':len(content)}]}
        payload=build_payload('Jaká je servisní eskalace?', [document])
        selected=json.loads(payload['input'][0]['content'][0]['text'])['documents'][0]['content']
        self.assertIn('lhůtu šest hodin',selected)
        self.assertEqual(locator(document,'Servisní eskalace má lhůtu šest hodin.'),'Strana 2')
    def test_actual_pdf_docx_and_locators(self):
        parsed=extract('demo.pdf',pdf());self.assertIn('6 hodin',parsed['content']);self.assertEqual(parsed['locators'][0]['label'],'Strana 1')
        parsed=extract('demo.docx',docx());self.assertIn('nákup',parsed['content']);self.assertEqual(parsed['locators'][0]['label'],'Odstavec 1')
    def test_blank_pdf_xml_entities_and_size_are_rejected(self):
        writer=PdfWriter();writer.add_blank_page(300,300);stream=io.BytesIO();writer.write(stream)
        with self.assertRaisesRegex(ValueError,'OCR'):extract('scan.pdf',stream.getvalue())
        with self.assertRaises(ValueError):extract('../bad.txt',b'text')
        with self.assertRaises(ValueError):extract('bad.txt',b'x'*2000001)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:archive.writestr('word/document.xml','<!DOCTYPE x [<!ENTITY a "bad">]><x/>')
        with self.assertRaises(ValueError):extract('bad.docx',stream.getvalue())

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.server=create_server(0,Path(self.temp.name)/'test.sqlite',api_key='');self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def call(self,path,body=None,cookie=None):
        headers={'Content-Type':'application/json'}
        if cookie:headers['Cookie']=cookie
        request=Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        try:
            with urlopen(request,timeout=25) as result:return result.status,json.load(result),result.headers
        except HTTPError as error:return error.code,json.load(error),error.headers
    def login(self,user):
        status,body,headers=self.call('/api/login',{'username':user,'password':'AtlasDemo-2026','role':'leadership'})
        self.assertEqual(status,200);self.assertEqual(body['role'],user);return headers['Set-Cookie'].split(';')[0]
    def test_identity_cannot_be_selected_via_role_and_revocation_cancels_sessions(self):
        self.assertEqual(self.call('/api/login',{'role':'leadership'})[0],400)
        self.assertEqual(self.call('/api/login',{'username':'operations','password':'wrong'})[0],401)
        operations=self.login('operations');owner=self.login('leadership')
        self.assertEqual(self.call('/api/users/toggle',{'username':'people','active':False},operations)[0],403)
        self.assertEqual(self.call('/api/users/toggle',{'username':'operations','active':False},owner)[0],200)
        self.assertEqual(self.call('/api/files/orders-2024',cookie=operations)[0],401)
        self.assertEqual(self.call('/api/login',{'username':'operations','password':'AtlasDemo-2026'})[0],401)
        self.assertEqual(self.call('/api/users/toggle',{'username':'leadership','active':False},owner)[0],400)
        self.assertEqual(self.call('/api/logout',{},owner)[0],200);self.assertEqual(self.call('/api/overview',cookie=owner)[0],401)
    def test_import_replace_delete_and_permissions(self):
        owner=self.login('leadership');ops=self.login('operations');people=self.login('people')
        body={'filename':'demo.pdf','data':base64.b64encode(pdf()).decode(),'title':'Servisní postup','group':'operations'}
        self.assertEqual(self.call('/api/documents/import',body,ops)[0],403)
        status,created,_=self.call('/api/documents/import',body,owner);self.assertEqual(status,200);key=created['id']
        status,document,_=self.call('/api/files/'+key,cookie=ops);self.assertEqual(status,200);self.assertEqual(document['version'],1);self.assertEqual(document['locators'][0]['label'],'Strana 1')
        self.assertEqual(self.call('/api/files/'+key,cookie=people)[0],404)
        replacement={**body,'id':key,'expectedVersion':1,'filename':'new.docx','data':base64.b64encode(docx('Nový nákup čeká na schválení vedoucím.')).decode()}
        self.assertEqual(self.call('/api/documents/import',replacement,owner)[1]['version'],2)
        self.assertIn('schválení',self.call('/api/files/'+key,cookie=ops)[1]['content'])
        self.assertEqual(self.call('/api/files/'+key+'?version=1',cookie=ops)[0],409)
        self.assertEqual(self.call('/api/documents/import',replacement,owner)[0],400)
        self.assertEqual(self.call('/api/documents/remove',{'id':key,'expectedVersion':2},owner)[0],200)
        self.assertEqual(self.call('/api/files/'+key,cookie=ops)[0],404)
        with closing(connect(self.server.state.database_path)) as connection:
            self.assertIsNone(connection.execute('SELECT 1 FROM document_meta WHERE id=?',(key,)).fetchone())
    def test_document_changed_during_ai_call_cannot_be_cited(self):
        with closing(connect(self.server.state.database_path)) as connection:
            def fake(question,docs):
                connection.execute("UPDATE documents SET content='Jiny obsah' WHERE id='purchase-policy'");connection.commit()
                return {'supported':True,'answer':'Stará odpověď','evidence':[{'source_id':'purchase-policy','quote':'Vyšší částky vyžadují dvě schválení: ředitelku a vlastníka společnosti.'}]}
            result=answer_question(connection,'operations','Kdo schvaluje nákup?',fake)
            self.assertEqual(result['kind'],'not_found');self.assertEqual(result['sources'],[])

    def test_revoked_identity_during_answer_does_not_receive_content(self):
        cookie=self.login('operations');self.server.state.api_key='test-only'
        def fake(question,docs):
            with closing(connect(self.server.state.database_path)) as connection:
                connection.execute("UPDATE users SET active=0,revision=revision+1 WHERE username='operations'");connection.commit()
            return {'supported':True,'answer':'Nepředat staré relaci','evidence':[{'source_id':'purchase-policy','quote':'Vyšší částky vyžadují dvě schválení: ředitelku a vlastníka společnosti.'}]}
        self.server.state.answer_ai=fake
        status,answer,_=self.call('/api/ask',{'question':'Kdo schvaluje nákup?'},cookie)
        self.assertEqual(status,401);self.assertNotIn('answer',answer);self.assertNotIn('sources',answer)
