import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_lifecycle import pdf,docx
target=Path(sys.argv[1]);target.mkdir(parents=True,exist_ok=True)
(target/'demo.pdf').write_bytes(pdf());(target/'demo.docx').write_bytes(docx())
