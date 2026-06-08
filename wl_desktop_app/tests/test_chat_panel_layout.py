# -*- coding: utf-8 -*-
"""chat_panel の配置ロジック (重なり判定) のユニットテスト。"""
import unittest


def _rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
    return not (x1 + w1 <= x2 or x1 >= x2 + w2 or y1 + h1 <= y2 or y1 >= y2 + h2)


class TestChatPanelLayout(unittest.TestCase):
    def test_rects_overlap(self):
        self.assertTrue(_rects_overlap(0, 0, 100, 100, 50, 50, 100, 100))
        self.assertFalse(_rects_overlap(0, 0, 100, 100, 0, 101, 100, 100))
        self.assertFalse(_rects_overlap(0, 0, 100, 50, 0, 51, 100, 50))

    def test_above_miniport_does_not_overlap(self):
        mx, my, mw, mh = 1600, 800, 264, 224
        pw, ph = 420, 560
        gap = 8
        x = mx + mw - pw
        y = my - ph - gap
        self.assertFalse(_rects_overlap(x, y, pw, ph, mx, my, mw, mh))


if __name__ == "__main__":
    unittest.main()
