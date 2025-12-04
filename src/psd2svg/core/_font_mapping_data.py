"""Default font mapping data.

This module contains a comprehensive mapping of PostScript font names to their
family names, styles, and weights. This mapping is used as a fallback when
fontconfig is not available (e.g., on Windows).

The mappings are based on:
- Standard PostScript font names
- Common fonts used in Adobe Photoshop
- Fonts commonly available across platforms

Weight values follow fontconfig conventions:
- 0 = thin (CSS 100)
- 40 = extralight (CSS 200)
- 50 = light (CSS 300)
- 80 = regular/normal (CSS 400)
- 100 = medium (CSS 500)
- 180 = semibold (CSS 600)
- 200 = bold (CSS 700)
- 205 = extrabold (CSS 800)
- 210 = black (CSS 900)

Generated with knowledge of standard font naming conventions.
Can be regenerated/extended using scripts/generate_font_mapping.py.
"""

from typing import Any

FONT_MAPPING: dict[str, dict[str, Any]] = {
    # Arial family
    "ArialMT": {"family": "Arial", "style": "Regular", "weight": 80.0},
    "Arial-BoldMT": {"family": "Arial", "style": "Bold", "weight": 200.0},
    "Arial-ItalicMT": {"family": "Arial", "style": "Italic", "weight": 80.0},
    "Arial-BoldItalicMT": {"family": "Arial", "style": "Bold Italic", "weight": 200.0},
    "ArialNarrow": {"family": "Arial Narrow", "style": "Regular", "weight": 80.0},
    "ArialNarrow-Bold": {"family": "Arial Narrow", "style": "Bold", "weight": 200.0},
    "ArialNarrow-Italic": {"family": "Arial Narrow", "style": "Italic", "weight": 80.0},
    "ArialNarrow-BoldItalic": {
        "family": "Arial Narrow",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Times New Roman family
    "TimesNewRomanPSMT": {"family": "Times New Roman", "style": "Regular", "weight": 80.0},
    "TimesNewRomanPS-BoldMT": {
        "family": "Times New Roman",
        "style": "Bold",
        "weight": 200.0,
    },
    "TimesNewRomanPS-ItalicMT": {
        "family": "Times New Roman",
        "style": "Italic",
        "weight": 80.0,
    },
    "TimesNewRomanPS-BoldItalicMT": {
        "family": "Times New Roman",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Times family (standard PostScript)
    "Times-Roman": {"family": "Times", "style": "Roman", "weight": 80.0},
    "Times-Bold": {"family": "Times", "style": "Bold", "weight": 200.0},
    "Times-Italic": {"family": "Times", "style": "Italic", "weight": 80.0},
    "Times-BoldItalic": {"family": "Times", "style": "Bold Italic", "weight": 200.0},
    # Helvetica family (standard PostScript)
    "Helvetica": {"family": "Helvetica", "style": "Regular", "weight": 80.0},
    "Helvetica-Bold": {"family": "Helvetica", "style": "Bold", "weight": 200.0},
    "Helvetica-Oblique": {"family": "Helvetica", "style": "Oblique", "weight": 80.0},
    "Helvetica-BoldOblique": {
        "family": "Helvetica",
        "style": "Bold Oblique",
        "weight": 200.0,
    },
    "HelveticaNeue": {"family": "Helvetica Neue", "style": "Regular", "weight": 80.0},
    "HelveticaNeue-Bold": {"family": "Helvetica Neue", "style": "Bold", "weight": 200.0},
    "HelveticaNeue-Italic": {"family": "Helvetica Neue", "style": "Italic", "weight": 80.0},
    "HelveticaNeue-BoldItalic": {
        "family": "Helvetica Neue",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Courier family (standard PostScript)
    "Courier": {"family": "Courier", "style": "Regular", "weight": 80.0},
    "Courier-Bold": {"family": "Courier", "style": "Bold", "weight": 200.0},
    "Courier-Oblique": {"family": "Courier", "style": "Oblique", "weight": 80.0},
    "Courier-BoldOblique": {
        "family": "Courier",
        "style": "Bold Oblique",
        "weight": 200.0,
    },
    "CourierNewPSMT": {"family": "Courier New", "style": "Regular", "weight": 80.0},
    "CourierNewPS-BoldMT": {"family": "Courier New", "style": "Bold", "weight": 200.0},
    "CourierNewPS-ItalicMT": {"family": "Courier New", "style": "Italic", "weight": 80.0},
    "CourierNewPS-BoldItalicMT": {
        "family": "Courier New",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Verdana family
    "Verdana": {"family": "Verdana", "style": "Regular", "weight": 80.0},
    "Verdana-Bold": {"family": "Verdana", "style": "Bold", "weight": 200.0},
    "Verdana-Italic": {"family": "Verdana", "style": "Italic", "weight": 80.0},
    "Verdana-BoldItalic": {"family": "Verdana", "style": "Bold Italic", "weight": 200.0},
    # Georgia family
    "Georgia": {"family": "Georgia", "style": "Regular", "weight": 80.0},
    "Georgia-Bold": {"family": "Georgia", "style": "Bold", "weight": 200.0},
    "Georgia-Italic": {"family": "Georgia", "style": "Italic", "weight": 80.0},
    "Georgia-BoldItalic": {"family": "Georgia", "style": "Bold Italic", "weight": 200.0},
    # Tahoma family
    "Tahoma": {"family": "Tahoma", "style": "Regular", "weight": 80.0},
    "Tahoma-Bold": {"family": "Tahoma", "style": "Bold", "weight": 200.0},
    # Trebuchet MS family
    "TrebuchetMS": {"family": "Trebuchet MS", "style": "Regular", "weight": 80.0},
    "TrebuchetMS-Bold": {"family": "Trebuchet MS", "style": "Bold", "weight": 200.0},
    "TrebuchetMS-Italic": {"family": "Trebuchet MS", "style": "Italic", "weight": 80.0},
    "Trebuchet-BoldItalic": {
        "family": "Trebuchet MS",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Comic Sans MS family
    "ComicSansMS": {"family": "Comic Sans MS", "style": "Regular", "weight": 80.0},
    "ComicSansMS-Bold": {"family": "Comic Sans MS", "style": "Bold", "weight": 200.0},
    # Impact
    "Impact": {"family": "Impact", "style": "Regular", "weight": 80.0},
    # Noto Sans family
    "NotoSans": {"family": "Noto Sans", "style": "Regular", "weight": 80.0},
    "NotoSans-Bold": {"family": "Noto Sans", "style": "Bold", "weight": 200.0},
    "NotoSans-Italic": {"family": "Noto Sans", "style": "Italic", "weight": 80.0},
    "NotoSans-BoldItalic": {"family": "Noto Sans", "style": "Bold Italic", "weight": 200.0},
    # Noto Serif family
    "NotoSerif": {"family": "Noto Serif", "style": "Regular", "weight": 80.0},
    "NotoSerif-Bold": {"family": "Noto Serif", "style": "Bold", "weight": 200.0},
    "NotoSerif-Italic": {"family": "Noto Serif", "style": "Italic", "weight": 80.0},
    "NotoSerif-BoldItalic": {
        "family": "Noto Serif",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Noto Sans CJK JP family
    "NotoSansJP-Thin": {"family": "Noto Sans JP", "style": "Thin", "weight": 0.0},
    "NotoSansJP-Light": {"family": "Noto Sans JP", "style": "Light", "weight": 50.0},
    "NotoSansJP-Regular": {"family": "Noto Sans JP", "style": "Regular", "weight": 80.0},
    "NotoSansJP-Medium": {"family": "Noto Sans JP", "style": "Medium", "weight": 100.0},
    "NotoSansJP-Bold": {"family": "Noto Sans JP", "style": "Bold", "weight": 200.0},
    "NotoSansJP-Black": {"family": "Noto Sans JP", "style": "Black", "weight": 210.0},
    # Noto Sans CJK KR family
    "NotoSansKR-Thin": {"family": "Noto Sans KR", "style": "Thin", "weight": 0.0},
    "NotoSansKR-Light": {"family": "Noto Sans KR", "style": "Light", "weight": 50.0},
    "NotoSansKR-Regular": {"family": "Noto Sans KR", "style": "Regular", "weight": 80.0},
    "NotoSansKR-Medium": {"family": "Noto Sans KR", "style": "Medium", "weight": 100.0},
    "NotoSansKR-Bold": {"family": "Noto Sans KR", "style": "Bold", "weight": 200.0},
    "NotoSansKR-Black": {"family": "Noto Sans KR", "style": "Black", "weight": 210.0},
    # Noto Sans CJK SC (Simplified Chinese) family
    "NotoSansSC-Thin": {"family": "Noto Sans SC", "style": "Thin", "weight": 0.0},
    "NotoSansSC-Light": {"family": "Noto Sans SC", "style": "Light", "weight": 50.0},
    "NotoSansSC-Regular": {"family": "Noto Sans SC", "style": "Regular", "weight": 80.0},
    "NotoSansSC-Medium": {"family": "Noto Sans SC", "style": "Medium", "weight": 100.0},
    "NotoSansSC-Bold": {"family": "Noto Sans SC", "style": "Bold", "weight": 200.0},
    "NotoSansSC-Black": {"family": "Noto Sans SC", "style": "Black", "weight": 210.0},
    # Noto Sans CJK TC (Traditional Chinese) family
    "NotoSansTC-Thin": {"family": "Noto Sans TC", "style": "Thin", "weight": 0.0},
    "NotoSansTC-Light": {"family": "Noto Sans TC", "style": "Light", "weight": 50.0},
    "NotoSansTC-Regular": {"family": "Noto Sans TC", "style": "Regular", "weight": 80.0},
    "NotoSansTC-Medium": {"family": "Noto Sans TC", "style": "Medium", "weight": 100.0},
    "NotoSansTC-Bold": {"family": "Noto Sans TC", "style": "Bold", "weight": 200.0},
    "NotoSansTC-Black": {"family": "Noto Sans TC", "style": "Black", "weight": 210.0},
    # Noto Sans Arabic family
    "NotoSansArabic-Thin": {"family": "Noto Sans Arabic", "style": "Thin", "weight": 0.0},
    "NotoSansArabic-Light": {
        "family": "Noto Sans Arabic",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansArabic-Regular": {
        "family": "Noto Sans Arabic",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansArabic-Medium": {
        "family": "Noto Sans Arabic",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansArabic-Bold": {"family": "Noto Sans Arabic", "style": "Bold", "weight": 200.0},
    "NotoSansArabic-Black": {
        "family": "Noto Sans Arabic",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans Thai family
    "NotoSansThai-Thin": {"family": "Noto Sans Thai", "style": "Thin", "weight": 0.0},
    "NotoSansThai-Light": {"family": "Noto Sans Thai", "style": "Light", "weight": 50.0},
    "NotoSansThai-Regular": {
        "family": "Noto Sans Thai",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansThai-Medium": {"family": "Noto Sans Thai", "style": "Medium", "weight": 100.0},
    "NotoSansThai-Bold": {"family": "Noto Sans Thai", "style": "Bold", "weight": 200.0},
    "NotoSansThai-Black": {"family": "Noto Sans Thai", "style": "Black", "weight": 210.0},
    # Noto Sans Hebrew family
    "NotoSansHebrew-Thin": {"family": "Noto Sans Hebrew", "style": "Thin", "weight": 0.0},
    "NotoSansHebrew-Light": {
        "family": "Noto Sans Hebrew",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansHebrew-Regular": {
        "family": "Noto Sans Hebrew",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansHebrew-Medium": {
        "family": "Noto Sans Hebrew",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansHebrew-Bold": {"family": "Noto Sans Hebrew", "style": "Bold", "weight": 200.0},
    "NotoSansHebrew-Black": {
        "family": "Noto Sans Hebrew",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans Devanagari family
    "NotoSansDevanagari-Thin": {
        "family": "Noto Sans Devanagari",
        "style": "Thin",
        "weight": 0.0,
    },
    "NotoSansDevanagari-Light": {
        "family": "Noto Sans Devanagari",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansDevanagari-Regular": {
        "family": "Noto Sans Devanagari",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansDevanagari-Medium": {
        "family": "Noto Sans Devanagari",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansDevanagari-Bold": {
        "family": "Noto Sans Devanagari",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSansDevanagari-Black": {
        "family": "Noto Sans Devanagari",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans CJK (generic) family
    "NotoSansCJK-Regular": {"family": "Noto Sans CJK", "style": "Regular", "weight": 80.0},
    "NotoSansCJK-Bold": {"family": "Noto Sans CJK", "style": "Bold", "weight": 200.0},
    # Palatino family
    "Palatino-Roman": {"family": "Palatino", "style": "Roman", "weight": 80.0},
    "Palatino-Bold": {"family": "Palatino", "style": "Bold", "weight": 200.0},
    "Palatino-Italic": {"family": "Palatino", "style": "Italic", "weight": 80.0},
    "Palatino-BoldItalic": {
        "family": "Palatino",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Symbol font
    "Symbol": {"family": "Symbol", "style": "Regular", "weight": 80.0},
    # ZapfDingbats
    "ZapfDingbatsITC": {"family": "Zapf Dingbats", "style": "Regular", "weight": 80.0},
}
