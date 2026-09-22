"""Negative checks: a heading-only or stale lesson must never pass clarity gate."""
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_retrofit_v4 import check_lesson, ROADMAP

class ClarityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module=ROADMAP/'01-nen-tang-lap-trinh'
        cls.original=next(cls.module.glob('01-*.md')).read_text()

    def check(self,text):
        with tempfile.NamedTemporaryFile(mode='w',suffix='.md',dir=self.module,encoding='utf-8') as tmp:
            tmp.write(text); tmp.flush()
            check_lesson(Path(tmp.name),today=date(2026,9,22))

    def test_original_passes(self):
        self.check(self.original)

    def test_inline_lambda_is_not_a_link(self):
        self.check(self.original+'\nLambda syntax: `[capture](parameters) { body }`.\n')

    def test_missing_baseline_fails(self):
        with self.assertRaisesRegex(ValueError,'Baseline'):
            self.check(self.original.replace('**Baseline:**','**Old baseline:**'))

    def test_future_verification_fails(self):
        with self.assertRaisesRegex(ValueError,'stale/future'):
            self.check(self.original.replace('2026-09-22','2099-01-01'))

    def test_pending_verification_fails(self):
        with self.assertRaisesRegex(ValueError,'unverified'):
            self.check(self.original.replace('2026-09-22','pending'))

    def test_missing_comparison_not_saved_by_vocabulary(self):
        with self.assertRaisesRegex(ValueError,'So sánh'):
            self.check(self.original.replace('### So sánh để chọn đúng','### Notes'))

    def test_empty_intuition_fails(self):
        import re
        changed=re.sub(r'(### Trực giác 60 giây\n).*?(?=### Từ vựng)',r'\1\n',self.original,flags=re.S)
        with self.assertRaisesRegex(ValueError,'empty clarity'):
            self.check(changed)

    def test_broken_diff_link_fails(self):
        with self.assertRaisesRegex(ValueError,'broken local link'):
            self.check(self.original+'\n[patch](./missing.diff)\n')

    def test_broken_fragment_fails(self):
        with self.assertRaisesRegex(ValueError,'unknown fragment'):
            self.check(self.original+'\n[anchor](./index.md#missing-section)\n')

    def test_heading_inside_fence_cannot_pass(self):
        changed=self.original.replace('### Mini-check','### Not-a-mini-check')+'\n```text\n### Mini-check\nFake content\n```\n'
        with self.assertRaisesRegex(ValueError,'Mini-check'):
            self.check(changed)

if __name__=='__main__':
    unittest.main()
