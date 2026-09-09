"""Regresiones del contenido visual progresivo de la Sesión 01."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SESSION_DIR = ROOT / "docs/sessions/01-introduccion-sdr"
ARTICLE = SESSION_DIR / "index.md"


class Session01VisualContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markdown = ARTICLE.read_text(encoding="utf-8")

    def test_progressive_diagrams_highlight_the_current_block_only(self):
        expected = ["ANT", "TUN", "ADC", "DDC", "LPF", "USB"]
        mermaid_blocks = re.findall(
            r"```mermaid\n(.*?)\n```",
            self.markdown,
            flags=re.DOTALL,
        )
        rtl_blocks = [block for block in mermaid_blocks if "TUN[Tuner R828D" in block]

        self.assertEqual(len(rtl_blocks), 7)
        overview, *stage_blocks = rtl_blocks
        self.assertNotIn("classDef activo", overview)

        for block, node in zip(stage_blocks, expected, strict=True):
            self.assertEqual(block.count("classDef activo"), 1)
            self.assertEqual(
                re.findall(r"class (ANT|TUN|ADC|DDC|LPF|USB) activo;", block),
                [node],
            )

    def test_original_architecture_figures_are_referenced_and_present(self):
        names = {
            "radio-convencional-vs-sdr.png",
            "arquitecturas-receptores-sdr.png",
            "rtl-sdr-v4-interior.png",
        }
        for name in names:
            self.assertIn(f"figures/{name}", self.markdown)
            self.assertTrue((SESSION_DIR / "figures" / name).is_file())


if __name__ == "__main__":
    unittest.main()
