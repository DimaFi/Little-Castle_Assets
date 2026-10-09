"""Protect complete catalog intake and preserve the historical 23-record handoff."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_portable_releases import audit_asset_book,AuditError

class CatalogIntakeTests(unittest.TestCase):
    def test_complete_cliff_intake_and_partial_rejection(self):
        actual=json.loads((Path(__file__).resolve().parents[2]/'AssetBook/AssetBook.json').read_text())
        ids=[a['id'] for a in actual['assets'] if a['id'].startswith('ENV_CliffKit_')]
        self.assertEqual(len(ids),14)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'AssetBook').mkdir();(root/'AssetsDatabase').mkdir();(root/'AssetsDatabase/AssetBook.json').write_text('{}');(root/'payload.txt').write_text('valid')
            records=[dict(id='historical_'+str(i),path='.',source_file='payload.txt') for i in range(23)]
            def check():
                (root/'AssetBook/AssetBook.json').write_text(json.dumps(dict(assets=records)))
                return audit_asset_book(root)
            self.assertEqual(check()['versioned_records'],23)
            records.extend(dict(id=i,path='.',source_file='payload.txt') for i in ids)
            self.assertEqual(check()['versioned_records'],37)
            records.pop()
            with self.assertRaisesRegex(AuditError,'Incomplete CliffKit'):check()
            records[:]=records[:23];records.append(dict(id='unexpected_new_id',path='.',source_file='payload.txt'))
            with self.assertRaisesRegex(AuditError,'preserved 23'):check()

if __name__=='__main__':unittest.main()
