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
    "TimesNewRomanPSMT": {
        "family": "Times New Roman",
        "style": "Regular",
        "weight": 80.0,
    },
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
    "HelveticaNeue-Bold": {
        "family": "Helvetica Neue",
        "style": "Bold",
        "weight": 200.0,
    },
    "HelveticaNeue-Italic": {
        "family": "Helvetica Neue",
        "style": "Italic",
        "weight": 80.0,
    },
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
    "CourierNewPS-ItalicMT": {
        "family": "Courier New",
        "style": "Italic",
        "weight": 80.0,
    },
    "CourierNewPS-BoldItalicMT": {
        "family": "Courier New",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Verdana family
    "Verdana": {"family": "Verdana", "style": "Regular", "weight": 80.0},
    "Verdana-Bold": {"family": "Verdana", "style": "Bold", "weight": 200.0},
    "Verdana-Italic": {"family": "Verdana", "style": "Italic", "weight": 80.0},
    "Verdana-BoldItalic": {
        "family": "Verdana",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Georgia family
    "Georgia": {"family": "Georgia", "style": "Regular", "weight": 80.0},
    "Georgia-Bold": {"family": "Georgia", "style": "Bold", "weight": 200.0},
    "Georgia-Italic": {"family": "Georgia", "style": "Italic", "weight": 80.0},
    "Georgia-BoldItalic": {
        "family": "Georgia",
        "style": "Bold Italic",
        "weight": 200.0,
    },
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
    "NotoSans-BoldItalic": {
        "family": "Noto Sans",
        "style": "Bold Italic",
        "weight": 200.0,
    },
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
    "NotoSansJP-Regular": {
        "family": "Noto Sans JP",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansJP-Medium": {"family": "Noto Sans JP", "style": "Medium", "weight": 100.0},
    "NotoSansJP-Bold": {"family": "Noto Sans JP", "style": "Bold", "weight": 200.0},
    "NotoSansJP-Black": {"family": "Noto Sans JP", "style": "Black", "weight": 210.0},
    # Noto Sans CJK KR family
    "NotoSansKR-Thin": {"family": "Noto Sans KR", "style": "Thin", "weight": 0.0},
    "NotoSansKR-Light": {"family": "Noto Sans KR", "style": "Light", "weight": 50.0},
    "NotoSansKR-Regular": {
        "family": "Noto Sans KR",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansKR-Medium": {"family": "Noto Sans KR", "style": "Medium", "weight": 100.0},
    "NotoSansKR-Bold": {"family": "Noto Sans KR", "style": "Bold", "weight": 200.0},
    "NotoSansKR-Black": {"family": "Noto Sans KR", "style": "Black", "weight": 210.0},
    # Noto Sans CJK SC (Simplified Chinese) family
    "NotoSansSC-Thin": {"family": "Noto Sans SC", "style": "Thin", "weight": 0.0},
    "NotoSansSC-Light": {"family": "Noto Sans SC", "style": "Light", "weight": 50.0},
    "NotoSansSC-Regular": {
        "family": "Noto Sans SC",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansSC-Medium": {"family": "Noto Sans SC", "style": "Medium", "weight": 100.0},
    "NotoSansSC-Bold": {"family": "Noto Sans SC", "style": "Bold", "weight": 200.0},
    "NotoSansSC-Black": {"family": "Noto Sans SC", "style": "Black", "weight": 210.0},
    # Noto Sans CJK TC (Traditional Chinese) family
    "NotoSansTC-Thin": {"family": "Noto Sans TC", "style": "Thin", "weight": 0.0},
    "NotoSansTC-Light": {"family": "Noto Sans TC", "style": "Light", "weight": 50.0},
    "NotoSansTC-Regular": {
        "family": "Noto Sans TC",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansTC-Medium": {"family": "Noto Sans TC", "style": "Medium", "weight": 100.0},
    "NotoSansTC-Bold": {"family": "Noto Sans TC", "style": "Bold", "weight": 200.0},
    "NotoSansTC-Black": {"family": "Noto Sans TC", "style": "Black", "weight": 210.0},
    # Noto Sans Arabic family
    "NotoSansArabic-Thin": {
        "family": "Noto Sans Arabic",
        "style": "Thin",
        "weight": 0.0,
    },
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
    "NotoSansArabic-Bold": {
        "family": "Noto Sans Arabic",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSansArabic-Black": {
        "family": "Noto Sans Arabic",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans Thai family
    "NotoSansThai-Thin": {"family": "Noto Sans Thai", "style": "Thin", "weight": 0.0},
    "NotoSansThai-Light": {
        "family": "Noto Sans Thai",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansThai-Regular": {
        "family": "Noto Sans Thai",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansThai-Medium": {
        "family": "Noto Sans Thai",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansThai-Bold": {"family": "Noto Sans Thai", "style": "Bold", "weight": 200.0},
    "NotoSansThai-Black": {
        "family": "Noto Sans Thai",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans Hebrew family
    "NotoSansHebrew-Thin": {
        "family": "Noto Sans Hebrew",
        "style": "Thin",
        "weight": 0.0,
    },
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
    "NotoSansHebrew-Bold": {
        "family": "Noto Sans Hebrew",
        "style": "Bold",
        "weight": 200.0,
    },
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
    "NotoSansCJK-Regular": {
        "family": "Noto Sans CJK",
        "style": "Regular",
        "weight": 80.0,
    },
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
    # Adobe Photoshop standard fonts
    # Minion Pro family (Adobe's serif font, common default in Photoshop)
    "MinionPro-Regular": {"family": "Minion Pro", "style": "Regular", "weight": 80.0},
    "MinionPro-Bold": {"family": "Minion Pro", "style": "Bold", "weight": 200.0},
    "MinionPro-It": {"family": "Minion Pro", "style": "Italic", "weight": 80.0},
    "MinionPro-BoldIt": {
        "family": "Minion Pro",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "MinionPro-Medium": {"family": "Minion Pro", "style": "Medium", "weight": 100.0},
    "MinionPro-Semibold": {
        "family": "Minion Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Myriad Pro family (Adobe's sans-serif font, common in UI/web design)
    "MyriadPro-Regular": {"family": "Myriad Pro", "style": "Regular", "weight": 80.0},
    "MyriadPro-Bold": {"family": "Myriad Pro", "style": "Bold", "weight": 200.0},
    "MyriadPro-It": {"family": "Myriad Pro", "style": "Italic", "weight": 80.0},
    "MyriadPro-BoldIt": {
        "family": "Myriad Pro",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "MyriadPro-Light": {"family": "Myriad Pro", "style": "Light", "weight": 50.0},
    "MyriadPro-Semibold": {
        "family": "Myriad Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    "MyriadPro-Black": {"family": "Myriad Pro", "style": "Black", "weight": 210.0},
    # Avenir family (popular geometric sans-serif)
    "Avenir-Book": {"family": "Avenir", "style": "Book", "weight": 80.0},
    "Avenir-Roman": {"family": "Avenir", "style": "Roman", "weight": 80.0},
    "Avenir-Heavy": {"family": "Avenir", "style": "Heavy", "weight": 200.0},
    "Avenir-Black": {"family": "Avenir", "style": "Black", "weight": 210.0},
    "Avenir-Light": {"family": "Avenir", "style": "Light", "weight": 50.0},
    "Avenir-Medium": {"family": "Avenir", "style": "Medium", "weight": 100.0},
    "Avenir-Oblique": {"family": "Avenir", "style": "Oblique", "weight": 80.0},
    "Avenir-BookOblique": {"family": "Avenir", "style": "Book Oblique", "weight": 80.0},
    "AvenirNext-Regular": {"family": "Avenir Next", "style": "Regular", "weight": 80.0},
    "AvenirNext-Bold": {"family": "Avenir Next", "style": "Bold", "weight": 200.0},
    "AvenirNext-Medium": {"family": "Avenir Next", "style": "Medium", "weight": 100.0},
    "AvenirNext-DemiBold": {
        "family": "Avenir Next",
        "style": "DemiBold",
        "weight": 180.0,
    },
    # Kozuka Gothic Pr6N family (Japanese font for CJK support)
    "KozGoPr6N-Regular": {
        "family": "Kozuka Gothic Pr6N",
        "style": "Regular",
        "weight": 80.0,
    },
    "KozGoPr6N-Bold": {
        "family": "Kozuka Gothic Pr6N",
        "style": "Bold",
        "weight": 200.0,
    },
    "KozGoPr6N-Light": {
        "family": "Kozuka Gothic Pr6N",
        "style": "Light",
        "weight": 50.0,
    },
    "KozGoPr6N-Medium": {
        "family": "Kozuka Gothic Pr6N",
        "style": "Medium",
        "weight": 100.0,
    },
    "KozGoPr6N-Heavy": {
        "family": "Kozuka Gothic Pr6N",
        "style": "Heavy",
        "weight": 200.0,
    },
    "KozGoPro-Regular": {
        "family": "Kozuka Gothic Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "KozGoPro-Bold": {"family": "Kozuka Gothic Pro", "style": "Bold", "weight": 200.0},
    "KozGoPro-Light": {"family": "Kozuka Gothic Pro", "style": "Light", "weight": 50.0},
    "KozGoPro-Medium": {
        "family": "Kozuka Gothic Pro",
        "style": "Medium",
        "weight": 100.0,
    },
    # Kozuka Mincho Pr6N family (Japanese serif font)
    "KozMinPr6N-Regular": {
        "family": "Kozuka Mincho Pr6N",
        "style": "Regular",
        "weight": 80.0,
    },
    "KozMinPr6N-Bold": {
        "family": "Kozuka Mincho Pr6N",
        "style": "Bold",
        "weight": 200.0,
    },
    "KozMinPr6N-Light": {
        "family": "Kozuka Mincho Pr6N",
        "style": "Light",
        "weight": 50.0,
    },
    "KozMinPro-Regular": {
        "family": "Kozuka Mincho Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    # Source Han Sans family (Adobe/Google CJK font, also known as Noto Sans CJK)
    "SourceHanSans-Regular": {
        "family": "Source Han Sans",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceHanSans-Bold": {
        "family": "Source Han Sans",
        "style": "Bold",
        "weight": 200.0,
    },
    "SourceHanSans-Light": {
        "family": "Source Han Sans",
        "style": "Light",
        "weight": 50.0,
    },
    "SourceHanSans-Medium": {
        "family": "Source Han Sans",
        "style": "Medium",
        "weight": 100.0,
    },
    "SourceHanSans-Heavy": {
        "family": "Source Han Sans",
        "style": "Heavy",
        "weight": 200.0,
    },
    "SourceHanSansJP-Regular": {
        "family": "Source Han Sans JP",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceHanSansJP-Bold": {
        "family": "Source Han Sans JP",
        "style": "Bold",
        "weight": 200.0,
    },
    "SourceHanSansJP-Light": {
        "family": "Source Han Sans JP",
        "style": "Light",
        "weight": 50.0,
    },
    "SourceHanSansJP-Medium": {
        "family": "Source Han Sans JP",
        "style": "Medium",
        "weight": 100.0,
    },
    "SourceHanSansKR-Regular": {
        "family": "Source Han Sans KR",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceHanSansKR-Bold": {
        "family": "Source Han Sans KR",
        "style": "Bold",
        "weight": 200.0,
    },
    "SourceHanSansSC-Regular": {
        "family": "Source Han Sans SC",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceHanSansSC-Bold": {
        "family": "Source Han Sans SC",
        "style": "Bold",
        "weight": 200.0,
    },
    "SourceHanSansTC-Regular": {
        "family": "Source Han Sans TC",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceHanSansTC-Bold": {
        "family": "Source Han Sans TC",
        "style": "Bold",
        "weight": 200.0,
    },
    # Source Sans Pro family (Adobe's open-source sans-serif)
    "SourceSansPro-Regular": {
        "family": "Source Sans Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceSansPro-Bold": {
        "family": "Source Sans Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    "SourceSansPro-It": {
        "family": "Source Sans Pro",
        "style": "Italic",
        "weight": 80.0,
    },
    "SourceSansPro-BoldIt": {
        "family": "Source Sans Pro",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "SourceSansPro-Light": {
        "family": "Source Sans Pro",
        "style": "Light",
        "weight": 50.0,
    },
    "SourceSansPro-Semibold": {
        "family": "Source Sans Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    "SourceSansPro-Black": {
        "family": "Source Sans Pro",
        "style": "Black",
        "weight": 210.0,
    },
    # Source Serif Pro family (Adobe's open-source serif)
    "SourceSerifPro-Regular": {
        "family": "Source Serif Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "SourceSerifPro-Bold": {
        "family": "Source Serif Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    "SourceSerifPro-Light": {
        "family": "Source Serif Pro",
        "style": "Light",
        "weight": 50.0,
    },
    "SourceSerifPro-Semibold": {
        "family": "Source Serif Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    "SourceSerifPro-Black": {
        "family": "Source Serif Pro",
        "style": "Black",
        "weight": 210.0,
    },
    # Adobe Garamond Pro family (classic serif font)
    "AGaramondPro-Regular": {
        "family": "Adobe Garamond Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "AGaramondPro-Bold": {
        "family": "Adobe Garamond Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    "AGaramondPro-Italic": {
        "family": "Adobe Garamond Pro",
        "style": "Italic",
        "weight": 80.0,
    },
    "AGaramondPro-Semibold": {
        "family": "Adobe Garamond Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Adobe Caslon Pro family
    "ACaslonPro-Regular": {
        "family": "Adobe Caslon Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "ACaslonPro-Bold": {"family": "Adobe Caslon Pro", "style": "Bold", "weight": 200.0},
    "ACaslonPro-Italic": {
        "family": "Adobe Caslon Pro",
        "style": "Italic",
        "weight": 80.0,
    },
    "ACaslonPro-Semibold": {
        "family": "Adobe Caslon Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Acumin Pro family (modern sans-serif, bundled with Photoshop)
    "AcuminPro-Thin": {"family": "Acumin Pro", "style": "Thin", "weight": 0.0},
    "AcuminPro-ExtraLight": {
        "family": "Acumin Pro",
        "style": "ExtraLight",
        "weight": 40.0,
    },
    "AcuminPro-Light": {"family": "Acumin Pro", "style": "Light", "weight": 50.0},
    "AcuminPro-Regular": {"family": "Acumin Pro", "style": "Regular", "weight": 80.0},
    "AcuminPro-Medium": {"family": "Acumin Pro", "style": "Medium", "weight": 100.0},
    "AcuminPro-Semibold": {
        "family": "Acumin Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    "AcuminPro-Bold": {"family": "Acumin Pro", "style": "Bold", "weight": 200.0},
    "AcuminPro-Black": {"family": "Acumin Pro", "style": "Black", "weight": 210.0},
    "AcuminPro-Italic": {"family": "Acumin Pro", "style": "Italic", "weight": 80.0},
    "AcuminPro-BoldItalic": {
        "family": "Acumin Pro",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Adobe Heiti Std family (Simplified Chinese, bundled with Photoshop)
    "AdobeHeitiStd-Regular": {
        "family": "Adobe Heiti Std",
        "style": "Regular",
        "weight": 80.0,
    },
    # Adobe Gothic Std family (CJK font, bundled with Photoshop)
    "AdobeGothicStd-Bold": {
        "family": "Adobe Gothic Std",
        "style": "Bold",
        "weight": 200.0,
    },
    "AdobeGothicStd-Light": {
        "family": "Adobe Gothic Std",
        "style": "Light",
        "weight": 50.0,
    },
    # Adobe Kaiti Std family (Simplified Chinese, bundled with Photoshop CS4+)
    "AdobeKaitiStd-Regular": {
        "family": "Adobe Kaiti Std",
        "style": "Regular",
        "weight": 80.0,
    },
    # Adobe FangSong Std family (Simplified Chinese, bundled with Photoshop CS4+)
    "AdobeFangsongStd-Regular": {
        "family": "Adobe FangSong Std",
        "style": "Regular",
        "weight": 80.0,
    },
    # Adobe Song Std family (Simplified Chinese, bundled with Photoshop CS3+)
    "AdobeSongStd-Light": {
        "family": "Adobe Song Std",
        "style": "Light",
        "weight": 50.0,
    },
    # Adobe Ming Std family (Traditional Chinese)
    "AdobeMingStd-Light": {
        "family": "Adobe Ming Std",
        "style": "Light",
        "weight": 50.0,
    },
    # Adobe Myungjo Std family (Korean)
    "AdobeMyungjoStd-Medium": {
        "family": "Adobe Myungjo Std",
        "style": "Medium",
        "weight": 100.0,
    },
    # Chaparral Pro family (serif font, bundled with Creative Suite)
    "ChaparralPro-Regular": {
        "family": "Chaparral Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "ChaparralPro-Bold": {"family": "Chaparral Pro", "style": "Bold", "weight": 200.0},
    "ChaparralPro-Italic": {
        "family": "Chaparral Pro",
        "style": "Italic",
        "weight": 80.0,
    },
    "ChaparralPro-BoldIt": {
        "family": "Chaparral Pro",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "ChaparralPro-Light": {"family": "Chaparral Pro", "style": "Light", "weight": 50.0},
    "ChaparralPro-Semibold": {
        "family": "Chaparral Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Trajan Pro family (classic Roman serif, bundled with Creative Suite)
    "TrajanPro-Regular": {"family": "Trajan Pro", "style": "Regular", "weight": 80.0},
    "TrajanPro-Bold": {"family": "Trajan Pro", "style": "Bold", "weight": 200.0},
    # News Gothic Std family (sans-serif, bundled with Creative Suite)
    "NewsGothicStd": {"family": "News Gothic Std", "style": "Regular", "weight": 80.0},
    "NewsGothicStd-Bold": {
        "family": "News Gothic Std",
        "style": "Bold",
        "weight": 200.0,
    },
    "NewsGothicStd-Italic": {
        "family": "News Gothic Std",
        "style": "Italic",
        "weight": 80.0,
    },
    "NewsGothicStd-BoldItalic": {
        "family": "News Gothic Std",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Cooper Black Std family (decorative, bundled with Creative Suite)
    "CooperBlackStd": {
        "family": "Cooper Black Std",
        "style": "Regular",
        "weight": 80.0,
    },
    "CooperBlackStd-Italic": {
        "family": "Cooper Black Std",
        "style": "Italic",
        "weight": 80.0,
    },
    # Giddyup Std (decorative, bundled with Creative Suite)
    "GiddyupStd": {"family": "Giddyup Std", "style": "Regular", "weight": 80.0},
    # Adobe Pi Std (symbol font, bundled with Creative Suite)
    "AdobePiStd": {"family": "Adobe Pi Std", "style": "Regular", "weight": 80.0},
    # Warnock Pro family (serif font, bonus with Creative Suite)
    "WarnockPro-Regular": {"family": "Warnock Pro", "style": "Regular", "weight": 80.0},
    "WarnockPro-Bold": {"family": "Warnock Pro", "style": "Bold", "weight": 200.0},
    "WarnockPro-It": {"family": "Warnock Pro", "style": "Italic", "weight": 80.0},
    "WarnockPro-BoldIt": {
        "family": "Warnock Pro",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "WarnockPro-Light": {"family": "Warnock Pro", "style": "Light", "weight": 50.0},
    "WarnockPro-Semibold": {
        "family": "Warnock Pro",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Google Fonts (popular fonts used in Photoshop)
    # Roboto family (most popular Google Font)
    "Roboto-Thin": {"family": "Roboto", "style": "Thin", "weight": 0.0},
    "Roboto-Light": {"family": "Roboto", "style": "Light", "weight": 50.0},
    "Roboto-Regular": {"family": "Roboto", "style": "Regular", "weight": 80.0},
    "Roboto-Medium": {"family": "Roboto", "style": "Medium", "weight": 100.0},
    "Roboto-Bold": {"family": "Roboto", "style": "Bold", "weight": 200.0},
    "Roboto-Black": {"family": "Roboto", "style": "Black", "weight": 210.0},
    "Roboto-ThinItalic": {"family": "Roboto", "style": "Thin Italic", "weight": 0.0},
    "Roboto-LightItalic": {"family": "Roboto", "style": "Light Italic", "weight": 50.0},
    "Roboto-Italic": {"family": "Roboto", "style": "Italic", "weight": 80.0},
    "Roboto-MediumItalic": {
        "family": "Roboto",
        "style": "Medium Italic",
        "weight": 100.0,
    },
    "Roboto-BoldItalic": {"family": "Roboto", "style": "Bold Italic", "weight": 200.0},
    "Roboto-BlackItalic": {
        "family": "Roboto",
        "style": "Black Italic",
        "weight": 210.0,
    },
    # Open Sans family (highly readable Google Font)
    "OpenSans-Light": {"family": "Open Sans", "style": "Light", "weight": 50.0},
    "OpenSans-Regular": {"family": "Open Sans", "style": "Regular", "weight": 80.0},
    "OpenSans-Medium": {"family": "Open Sans", "style": "Medium", "weight": 100.0},
    "OpenSans-SemiBold": {"family": "Open Sans", "style": "SemiBold", "weight": 180.0},
    "OpenSans-Bold": {"family": "Open Sans", "style": "Bold", "weight": 200.0},
    "OpenSans-ExtraBold": {
        "family": "Open Sans",
        "style": "ExtraBold",
        "weight": 205.0,
    },
    "OpenSans-LightItalic": {
        "family": "Open Sans",
        "style": "Light Italic",
        "weight": 50.0,
    },
    "OpenSans-Italic": {"family": "Open Sans", "style": "Italic", "weight": 80.0},
    "OpenSans-MediumItalic": {
        "family": "Open Sans",
        "style": "Medium Italic",
        "weight": 100.0,
    },
    "OpenSans-SemiBoldItalic": {
        "family": "Open Sans",
        "style": "SemiBold Italic",
        "weight": 180.0,
    },
    "OpenSans-BoldItalic": {
        "family": "Open Sans",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "OpenSans-ExtraBoldItalic": {
        "family": "Open Sans",
        "style": "ExtraBold Italic",
        "weight": 205.0,
    },
    # Lato family (versatile Google Font)
    "Lato-Thin": {"family": "Lato", "style": "Thin", "weight": 0.0},
    "Lato-Light": {"family": "Lato", "style": "Light", "weight": 50.0},
    "Lato-Regular": {"family": "Lato", "style": "Regular", "weight": 80.0},
    "Lato-Bold": {"family": "Lato", "style": "Bold", "weight": 200.0},
    "Lato-Black": {"family": "Lato", "style": "Black", "weight": 210.0},
    "Lato-ThinItalic": {"family": "Lato", "style": "Thin Italic", "weight": 0.0},
    "Lato-LightItalic": {"family": "Lato", "style": "Light Italic", "weight": 50.0},
    "Lato-Italic": {"family": "Lato", "style": "Italic", "weight": 80.0},
    "Lato-BoldItalic": {"family": "Lato", "style": "Bold Italic", "weight": 200.0},
    "Lato-BlackItalic": {"family": "Lato", "style": "Black Italic", "weight": 210.0},
    # Montserrat family (geometric Google Font)
    "Montserrat-Thin": {"family": "Montserrat", "style": "Thin", "weight": 0.0},
    "Montserrat-ExtraLight": {
        "family": "Montserrat",
        "style": "ExtraLight",
        "weight": 40.0,
    },
    "Montserrat-Light": {"family": "Montserrat", "style": "Light", "weight": 50.0},
    "Montserrat-Regular": {"family": "Montserrat", "style": "Regular", "weight": 80.0},
    "Montserrat-Medium": {"family": "Montserrat", "style": "Medium", "weight": 100.0},
    "Montserrat-SemiBold": {
        "family": "Montserrat",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "Montserrat-Bold": {"family": "Montserrat", "style": "Bold", "weight": 200.0},
    "Montserrat-ExtraBold": {
        "family": "Montserrat",
        "style": "ExtraBold",
        "weight": 205.0,
    },
    "Montserrat-Black": {"family": "Montserrat", "style": "Black", "weight": 210.0},
    "Montserrat-ThinItalic": {
        "family": "Montserrat",
        "style": "Thin Italic",
        "weight": 0.0,
    },
    "Montserrat-ExtraLightItalic": {
        "family": "Montserrat",
        "style": "ExtraLight Italic",
        "weight": 40.0,
    },
    "Montserrat-LightItalic": {
        "family": "Montserrat",
        "style": "Light Italic",
        "weight": 50.0,
    },
    "Montserrat-Italic": {"family": "Montserrat", "style": "Italic", "weight": 80.0},
    "Montserrat-MediumItalic": {
        "family": "Montserrat",
        "style": "Medium Italic",
        "weight": 100.0,
    },
    "Montserrat-SemiBoldItalic": {
        "family": "Montserrat",
        "style": "SemiBold Italic",
        "weight": 180.0,
    },
    "Montserrat-BoldItalic": {
        "family": "Montserrat",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "Montserrat-ExtraBoldItalic": {
        "family": "Montserrat",
        "style": "ExtraBold Italic",
        "weight": 205.0,
    },
    "Montserrat-BlackItalic": {
        "family": "Montserrat",
        "style": "Black Italic",
        "weight": 210.0,
    },
    # Poppins family (modern geometric Google Font)
    "Poppins-Thin": {"family": "Poppins", "style": "Thin", "weight": 0.0},
    "Poppins-ExtraLight": {"family": "Poppins", "style": "ExtraLight", "weight": 40.0},
    "Poppins-Light": {"family": "Poppins", "style": "Light", "weight": 50.0},
    "Poppins-Regular": {"family": "Poppins", "style": "Regular", "weight": 80.0},
    "Poppins-Medium": {"family": "Poppins", "style": "Medium", "weight": 100.0},
    "Poppins-SemiBold": {"family": "Poppins", "style": "SemiBold", "weight": 180.0},
    "Poppins-Bold": {"family": "Poppins", "style": "Bold", "weight": 200.0},
    "Poppins-ExtraBold": {"family": "Poppins", "style": "ExtraBold", "weight": 205.0},
    "Poppins-Black": {"family": "Poppins", "style": "Black", "weight": 210.0},
    # Inter family (popular UI design font)
    "Inter-Thin": {"family": "Inter", "style": "Thin", "weight": 0.0},
    "Inter-ExtraLight": {"family": "Inter", "style": "ExtraLight", "weight": 40.0},
    "Inter-Light": {"family": "Inter", "style": "Light", "weight": 50.0},
    "Inter-Regular": {"family": "Inter", "style": "Regular", "weight": 80.0},
    "Inter-Medium": {"family": "Inter", "style": "Medium", "weight": 100.0},
    "Inter-SemiBold": {"family": "Inter", "style": "SemiBold", "weight": 180.0},
    "Inter-Bold": {"family": "Inter", "style": "Bold", "weight": 200.0},
    "Inter-ExtraBold": {"family": "Inter", "style": "ExtraBold", "weight": 205.0},
    "Inter-Black": {"family": "Inter", "style": "Black", "weight": 210.0},
    # Microsoft Office fonts
    # Calibri family (default Office font 2007-2019)
    "Calibri": {"family": "Calibri", "style": "Regular", "weight": 80.0},
    "Calibri-Bold": {"family": "Calibri", "style": "Bold", "weight": 200.0},
    "Calibri-Italic": {"family": "Calibri", "style": "Italic", "weight": 80.0},
    "Calibri-BoldItalic": {
        "family": "Calibri",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "Calibri-Light": {"family": "Calibri", "style": "Light", "weight": 50.0},
    "Calibri-LightItalic": {
        "family": "Calibri",
        "style": "Light Italic",
        "weight": 50.0,
    },
    # Cambria family (serif font for on-screen reading)
    "Cambria": {"family": "Cambria", "style": "Regular", "weight": 80.0},
    "Cambria-Bold": {"family": "Cambria", "style": "Bold", "weight": 200.0},
    "Cambria-Italic": {"family": "Cambria", "style": "Italic", "weight": 80.0},
    "Cambria-BoldItalic": {
        "family": "Cambria",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # Segoe UI family (Windows system font)
    "SegoeUI": {"family": "Segoe UI", "style": "Regular", "weight": 80.0},
    "SegoeUI-Bold": {"family": "Segoe UI", "style": "Bold", "weight": 200.0},
    "SegoeUI-Italic": {"family": "Segoe UI", "style": "Italic", "weight": 80.0},
    "SegoeUI-BoldItalic": {
        "family": "Segoe UI",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "SegoeUI-Light": {"family": "Segoe UI", "style": "Light", "weight": 50.0},
    "SegoeUI-Semibold": {"family": "Segoe UI", "style": "Semibold", "weight": 180.0},
    "SegoeUI-Black": {"family": "Segoe UI", "style": "Black", "weight": 210.0},
    # macOS system fonts
    # San Francisco family (Apple's system font)
    "SFProDisplay-Regular": {
        "family": "SF Pro Display",
        "style": "Regular",
        "weight": 80.0,
    },
    "SFProDisplay-Bold": {"family": "SF Pro Display", "style": "Bold", "weight": 200.0},
    "SFProDisplay-Light": {
        "family": "SF Pro Display",
        "style": "Light",
        "weight": 50.0,
    },
    "SFProDisplay-Medium": {
        "family": "SF Pro Display",
        "style": "Medium",
        "weight": 100.0,
    },
    "SFProDisplay-Semibold": {
        "family": "SF Pro Display",
        "style": "Semibold",
        "weight": 180.0,
    },
    "SFProText-Regular": {"family": "SF Pro Text", "style": "Regular", "weight": 80.0},
    "SFProText-Bold": {"family": "SF Pro Text", "style": "Bold", "weight": 200.0},
    "SFProText-Light": {"family": "SF Pro Text", "style": "Light", "weight": 50.0},
    "SFProText-Medium": {"family": "SF Pro Text", "style": "Medium", "weight": 100.0},
    "SFProText-Semibold": {
        "family": "SF Pro Text",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Lucida Grande family (former macOS system font)
    "LucidaGrande": {"family": "Lucida Grande", "style": "Regular", "weight": 80.0},
    "LucidaGrande-Bold": {"family": "Lucida Grande", "style": "Bold", "weight": 200.0},
    # CJK System Fonts
    # Japanese fonts (Windows)
    # MS Gothic family (Windows Japanese sans-serif)
    "MS-Gothic": {"family": "MS Gothic", "style": "Regular", "weight": 80.0},
    "MS-PGothic": {"family": "MS PGothic", "style": "Regular", "weight": 80.0},
    "MS-UIGothic": {"family": "MS UI Gothic", "style": "Regular", "weight": 80.0},
    # MS Mincho family (Windows Japanese serif)
    "MS-Mincho": {"family": "MS Mincho", "style": "Regular", "weight": 80.0},
    "MS-PMincho": {"family": "MS PMincho", "style": "Regular", "weight": 80.0},
    # Yu Gothic family (Windows 8.1+ Japanese sans-serif)
    "YuGothic-Regular": {"family": "Yu Gothic", "style": "Regular", "weight": 80.0},
    "YuGothic-Bold": {"family": "Yu Gothic", "style": "Bold", "weight": 200.0},
    "YuGothic-Light": {"family": "Yu Gothic", "style": "Light", "weight": 50.0},
    "YuGothic-Medium": {"family": "Yu Gothic", "style": "Medium", "weight": 100.0},
    # Yu Mincho family (Windows 8.1+ Japanese serif)
    "YuMincho-Regular": {"family": "Yu Mincho", "style": "Regular", "weight": 80.0},
    "YuMincho-Demibold": {"family": "Yu Mincho", "style": "Demibold", "weight": 180.0},
    "YuMincho-Light": {"family": "Yu Mincho", "style": "Light", "weight": 50.0},
    # Meiryo family (Windows Vista+ Japanese sans-serif)
    "Meiryo": {"family": "Meiryo", "style": "Regular", "weight": 80.0},
    "Meiryo-Bold": {"family": "Meiryo", "style": "Bold", "weight": 200.0},
    "Meiryo-Italic": {"family": "Meiryo", "style": "Italic", "weight": 80.0},
    "Meiryo-BoldItalic": {"family": "Meiryo", "style": "Bold Italic", "weight": 200.0},
    "MeiryoUI": {"family": "Meiryo UI", "style": "Regular", "weight": 80.0},
    "MeiryoUI-Bold": {"family": "Meiryo UI", "style": "Bold", "weight": 200.0},
    # Chinese fonts (Windows Simplified Chinese)
    # SimSun family (Windows Simplified Chinese serif)
    "SimSun": {"family": "SimSun", "style": "Regular", "weight": 80.0},
    "SimSun-ExtB": {"family": "SimSun-ExtB", "style": "Regular", "weight": 80.0},
    "NSimSun": {"family": "NSimSun", "style": "Regular", "weight": 80.0},
    # SimHei family (Windows Simplified Chinese sans-serif)
    "SimHei": {"family": "SimHei", "style": "Regular", "weight": 80.0},
    # Microsoft YaHei family (Windows Vista+ Simplified Chinese sans-serif)
    "MicrosoftYaHei": {"family": "Microsoft YaHei", "style": "Regular", "weight": 80.0},
    "MicrosoftYaHei-Bold": {
        "family": "Microsoft YaHei",
        "style": "Bold",
        "weight": 200.0,
    },
    "MicrosoftYaHeiUI": {
        "family": "Microsoft YaHei UI",
        "style": "Regular",
        "weight": 80.0,
    },
    "MicrosoftYaHeiUI-Bold": {
        "family": "Microsoft YaHei UI",
        "style": "Bold",
        "weight": 200.0,
    },
    # FangSong and KaiTi (Windows Simplified Chinese traditional styles)
    "FangSong": {"family": "FangSong", "style": "Regular", "weight": 80.0},
    "KaiTi": {"family": "KaiTi", "style": "Regular", "weight": 80.0},
    # Chinese fonts (Windows Traditional Chinese)
    # MingLiU family (Windows Traditional Chinese serif)
    "MingLiU": {"family": "MingLiU", "style": "Regular", "weight": 80.0},
    "PMingLiU": {"family": "PMingLiU", "style": "Regular", "weight": 80.0},
    "MingLiU-ExtB": {"family": "MingLiU-ExtB", "style": "Regular", "weight": 80.0},
    "PMingLiU-ExtB": {"family": "PMingLiU-ExtB", "style": "Regular", "weight": 80.0},
    "MingLiU_HKSCS": {"family": "MingLiU_HKSCS", "style": "Regular", "weight": 80.0},
    "MingLiU_HKSCS-ExtB": {
        "family": "MingLiU_HKSCS-ExtB",
        "style": "Regular",
        "weight": 80.0,
    },
    # Microsoft JhengHei family (Windows Vista+ Traditional Chinese sans-serif)
    "MicrosoftJhengHei": {
        "family": "Microsoft JhengHei",
        "style": "Regular",
        "weight": 80.0,
    },
    "MicrosoftJhengHei-Bold": {
        "family": "Microsoft JhengHei",
        "style": "Bold",
        "weight": 200.0,
    },
    "MicrosoftJhengHeiUI": {
        "family": "Microsoft JhengHei UI",
        "style": "Regular",
        "weight": 80.0,
    },
    "MicrosoftJhengHeiUI-Bold": {
        "family": "Microsoft JhengHei UI",
        "style": "Bold",
        "weight": 200.0,
    },
    # DFKai-SB (Windows Traditional Chinese calligraphic)
    "DFKai-SB": {"family": "DFKai-SB", "style": "Regular", "weight": 80.0},
    # Korean fonts (Windows)
    # Gulim family (Windows Korean sans-serif)
    "Gulim": {"family": "Gulim", "style": "Regular", "weight": 80.0},
    "GulimChe": {"family": "GulimChe", "style": "Regular", "weight": 80.0},
    # Dotum family (Windows Korean sans-serif)
    "Dotum": {"family": "Dotum", "style": "Regular", "weight": 80.0},
    "DotumChe": {"family": "DotumChe", "style": "Regular", "weight": 80.0},
    # Batang family (Windows Korean serif)
    "Batang": {"family": "Batang", "style": "Regular", "weight": 80.0},
    "BatangChe": {"family": "BatangChe", "style": "Regular", "weight": 80.0},
    "Gungsuh": {"family": "Gungsuh", "style": "Regular", "weight": 80.0},
    "GungsuhChe": {"family": "GungsuhChe", "style": "Regular", "weight": 80.0},
    # Malgun Gothic family (Windows Vista+ Korean sans-serif)
    "MalgunGothic": {"family": "Malgun Gothic", "style": "Regular", "weight": 80.0},
    "MalgunGothic-Bold": {"family": "Malgun Gothic", "style": "Bold", "weight": 200.0},
    "MalgunGothicSemilight": {
        "family": "Malgun Gothic Semilight",
        "style": "Regular",
        "weight": 50.0,
    },
    # macOS CJK fonts
    # Hiragino family (macOS Japanese)
    "HiraginoSans-W3": {"family": "Hiragino Sans", "style": "W3", "weight": 50.0},
    "HiraginoSans-W4": {"family": "Hiragino Sans", "style": "W4", "weight": 80.0},
    "HiraginoSans-W5": {"family": "Hiragino Sans", "style": "W5", "weight": 100.0},
    "HiraginoSans-W6": {"family": "Hiragino Sans", "style": "W6", "weight": 180.0},
    "HiraginoSans-W7": {"family": "Hiragino Sans", "style": "W7", "weight": 200.0},
    "HiraginoSans-W8": {"family": "Hiragino Sans", "style": "W8", "weight": 205.0},
    "HiraginoSerif-W3": {"family": "Hiragino Serif", "style": "W3", "weight": 50.0},
    "HiraginoSerif-W6": {"family": "Hiragino Serif", "style": "W6", "weight": 180.0},
    "HiraginoSansGB-W3": {"family": "Hiragino Sans GB", "style": "W3", "weight": 50.0},
    "HiraginoSansGB-W6": {"family": "Hiragino Sans GB", "style": "W6", "weight": 180.0},
    # STHeiti family (macOS Simplified Chinese, legacy)
    "STHeiti": {"family": "STHeiti", "style": "Regular", "weight": 80.0},
    "STHeitiSC-Light": {"family": "STHeiti SC", "style": "Light", "weight": 50.0},
    "STHeitiSC-Medium": {"family": "STHeiti SC", "style": "Medium", "weight": 100.0},
    "STHeitiTC-Light": {"family": "STHeiti TC", "style": "Light", "weight": 50.0},
    "STHeitiTC-Medium": {"family": "STHeiti TC", "style": "Medium", "weight": 100.0},
    # STSong family (macOS Chinese serif, legacy)
    "STSong": {"family": "STSong", "style": "Regular", "weight": 80.0},
    "STSongti-SC-Regular": {
        "family": "STSongti SC",
        "style": "Regular",
        "weight": 80.0,
    },
    "STSongti-SC-Light": {"family": "STSongti SC", "style": "Light", "weight": 50.0},
    "STSongti-SC-Bold": {"family": "STSongti SC", "style": "Bold", "weight": 200.0},
    "STSongti-TC-Regular": {
        "family": "STSongti TC",
        "style": "Regular",
        "weight": 80.0,
    },
    "STSongti-TC-Light": {"family": "STSongti TC", "style": "Light", "weight": 50.0},
    "STSongti-TC-Bold": {"family": "STSongti TC", "style": "Bold", "weight": 200.0},
    # STKaiti and STFangsong (macOS Chinese traditional styles, legacy)
    "STKaiti": {"family": "STKaiti", "style": "Regular", "weight": 80.0},
    "STKaiti-SC-Regular": {"family": "STKaiti SC", "style": "Regular", "weight": 80.0},
    "STKaiti-SC-Bold": {"family": "STKaiti SC", "style": "Bold", "weight": 200.0},
    "STKaiti-TC-Regular": {"family": "STKaiti TC", "style": "Regular", "weight": 80.0},
    "STKaiti-TC-Bold": {"family": "STKaiti TC", "style": "Bold", "weight": 200.0},
    "STFangsong": {"family": "STFangsong", "style": "Regular", "weight": 80.0},
    # PingFang family (macOS modern Chinese, OS X 10.11+)
    "PingFangSC-Ultralight": {
        "family": "PingFang SC",
        "style": "Ultralight",
        "weight": 0.0,
    },
    "PingFangSC-Thin": {"family": "PingFang SC", "style": "Thin", "weight": 0.0},
    "PingFangSC-Light": {"family": "PingFang SC", "style": "Light", "weight": 50.0},
    "PingFangSC-Regular": {"family": "PingFang SC", "style": "Regular", "weight": 80.0},
    "PingFangSC-Medium": {"family": "PingFang SC", "style": "Medium", "weight": 100.0},
    "PingFangSC-Semibold": {
        "family": "PingFang SC",
        "style": "Semibold",
        "weight": 180.0,
    },
    "PingFangTC-Ultralight": {
        "family": "PingFang TC",
        "style": "Ultralight",
        "weight": 0.0,
    },
    "PingFangTC-Thin": {"family": "PingFang TC", "style": "Thin", "weight": 0.0},
    "PingFangTC-Light": {"family": "PingFang TC", "style": "Light", "weight": 50.0},
    "PingFangTC-Regular": {"family": "PingFang TC", "style": "Regular", "weight": 80.0},
    "PingFangTC-Medium": {"family": "PingFang TC", "style": "Medium", "weight": 100.0},
    "PingFangTC-Semibold": {
        "family": "PingFang TC",
        "style": "Semibold",
        "weight": 180.0,
    },
    "PingFangHK-Ultralight": {
        "family": "PingFang HK",
        "style": "Ultralight",
        "weight": 0.0,
    },
    "PingFangHK-Thin": {"family": "PingFang HK", "style": "Thin", "weight": 0.0},
    "PingFangHK-Light": {"family": "PingFang HK", "style": "Light", "weight": 50.0},
    "PingFangHK-Regular": {"family": "PingFang HK", "style": "Regular", "weight": 80.0},
    "PingFangHK-Medium": {"family": "PingFang HK", "style": "Medium", "weight": 100.0},
    "PingFangHK-Semibold": {
        "family": "PingFang HK",
        "style": "Semibold",
        "weight": 180.0,
    },
    # Apple SD Gothic Neo (macOS Korean, OS X 10.8+)
    "AppleSDGothicNeo-Thin": {
        "family": "Apple SD Gothic Neo",
        "style": "Thin",
        "weight": 0.0,
    },
    "AppleSDGothicNeo-Light": {
        "family": "Apple SD Gothic Neo",
        "style": "Light",
        "weight": 50.0,
    },
    "AppleSDGothicNeo-Regular": {
        "family": "Apple SD Gothic Neo",
        "style": "Regular",
        "weight": 80.0,
    },
    "AppleSDGothicNeo-Medium": {
        "family": "Apple SD Gothic Neo",
        "style": "Medium",
        "weight": 100.0,
    },
    "AppleSDGothicNeo-SemiBold": {
        "family": "Apple SD Gothic Neo",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "AppleSDGothicNeo-Bold": {
        "family": "Apple SD Gothic Neo",
        "style": "Bold",
        "weight": 200.0,
    },
    # ===== Monotype Fonts =====
    # Helvetica Neue - Additional variants (base variants already defined above)
    "HelveticaNeue-Light": {
        "family": "Helvetica Neue",
        "style": "Light",
        "weight": 50.0,
    },
    "HelveticaNeue-Medium": {
        "family": "Helvetica Neue",
        "style": "Medium",
        "weight": 100.0,
    },
    "HelveticaNeue-Thin": {
        "family": "Helvetica Neue",
        "style": "Thin",
        "weight": 0.0,
    },
    "HelveticaNeue-UltraLight": {
        "family": "Helvetica Neue",
        "style": "Ultra Light",
        "weight": 40.0,
    },
    "HelveticaNeue-CondensedBold": {
        "family": "Helvetica Neue",
        "style": "Condensed Bold",
        "weight": 200.0,
    },
    "HelveticaNeue-CondensedBlack": {
        "family": "Helvetica Neue",
        "style": "Condensed Black",
        "weight": 210.0,
    },
    # Frutiger (widely used in signage and corporate design)
    "Frutiger-Roman": {
        "family": "Frutiger",
        "style": "Roman",
        "weight": 80.0,
    },
    "Frutiger-Light": {
        "family": "Frutiger",
        "style": "Light",
        "weight": 50.0,
    },
    "Frutiger-Bold": {
        "family": "Frutiger",
        "style": "Bold",
        "weight": 200.0,
    },
    "Frutiger-Italic": {
        "family": "Frutiger",
        "style": "Italic",
        "weight": 80.0,
    },
    "Frutiger-BoldItalic": {
        "family": "Frutiger",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "Frutiger-Black": {
        "family": "Frutiger",
        "style": "Black",
        "weight": 210.0,
    },
    # Univers (classic Swiss typeface)
    "Univers-Roman": {
        "family": "Univers",
        "style": "Roman",
        "weight": 80.0,
    },
    "Univers-Light": {
        "family": "Univers",
        "style": "Light",
        "weight": 50.0,
    },
    "Univers-Bold": {
        "family": "Univers",
        "style": "Bold",
        "weight": 200.0,
    },
    "Univers-Oblique": {
        "family": "Univers",
        "style": "Oblique",
        "weight": 80.0,
    },
    "Univers-BoldOblique": {
        "family": "Univers",
        "style": "Bold Oblique",
        "weight": 200.0,
    },
    "Univers-Condensed": {
        "family": "Univers",
        "style": "Condensed",
        "weight": 80.0,
    },
    "Univers-CondensedBold": {
        "family": "Univers",
        "style": "Condensed Bold",
        "weight": 200.0,
    },
    # Gill Sans (British classic humanist sans-serif)
    "GillSans": {
        "family": "Gill Sans",
        "style": "Regular",
        "weight": 80.0,
    },
    "GillSans-Light": {
        "family": "Gill Sans",
        "style": "Light",
        "weight": 50.0,
    },
    "GillSans-Bold": {
        "family": "Gill Sans",
        "style": "Bold",
        "weight": 200.0,
    },
    "GillSans-Italic": {
        "family": "Gill Sans",
        "style": "Italic",
        "weight": 80.0,
    },
    "GillSans-BoldItalic": {
        "family": "Gill Sans",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "GillSans-SemiBold": {
        "family": "Gill Sans",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "GillSans-UltraBold": {
        "family": "Gill Sans",
        "style": "Ultra Bold",
        "weight": 205.0,
    },
    # Rockwell (popular geometric slab serif)
    "Rockwell": {
        "family": "Rockwell",
        "style": "Regular",
        "weight": 80.0,
    },
    "Rockwell-Light": {
        "family": "Rockwell",
        "style": "Light",
        "weight": 50.0,
    },
    "Rockwell-Bold": {
        "family": "Rockwell",
        "style": "Bold",
        "weight": 200.0,
    },
    "Rockwell-Italic": {
        "family": "Rockwell",
        "style": "Italic",
        "weight": 80.0,
    },
    "Rockwell-BoldItalic": {
        "family": "Rockwell",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "Rockwell-ExtraBold": {
        "family": "Rockwell",
        "style": "Extra Bold",
        "weight": 205.0,
    },
    # Optima (humanist sans-serif)
    "Optima-Regular": {
        "family": "Optima",
        "style": "Regular",
        "weight": 80.0,
    },
    "Optima-Bold": {
        "family": "Optima",
        "style": "Bold",
        "weight": 200.0,
    },
    "Optima-Italic": {
        "family": "Optima",
        "style": "Italic",
        "weight": 80.0,
    },
    "Optima-BoldItalic": {
        "family": "Optima",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    "Optima-Medium": {
        "family": "Optima",
        "style": "Medium",
        "weight": 100.0,
    },
    "Optima-ExtraBlack": {
        "family": "Optima",
        "style": "Extra Black",
        "weight": 210.0,
    },
    # Avenir Next - Additional variants (base variants already defined above)
    "AvenirNext-UltraLight": {
        "family": "Avenir Next",
        "style": "Ultra Light",
        "weight": 40.0,
    },
    "AvenirNext-Heavy": {
        "family": "Avenir Next",
        "style": "Heavy",
        "weight": 210.0,
    },
    "AvenirNext-Italic": {
        "family": "Avenir Next",
        "style": "Italic",
        "weight": 80.0,
    },
    # Franklin Gothic (American classic)
    "FranklinGothic-Book": {
        "family": "Franklin Gothic",
        "style": "Book",
        "weight": 80.0,
    },
    "FranklinGothic-Medium": {
        "family": "Franklin Gothic",
        "style": "Medium",
        "weight": 100.0,
    },
    "FranklinGothic-Demi": {
        "family": "Franklin Gothic",
        "style": "Demi",
        "weight": 180.0,
    },
    "FranklinGothic-Heavy": {
        "family": "Franklin Gothic",
        "style": "Heavy",
        "weight": 210.0,
    },
    "FranklinGothic-BookItalic": {
        "family": "Franklin Gothic",
        "style": "Book Italic",
        "weight": 80.0,
    },
    # Century Gothic (geometric sans-serif)
    "CenturyGothic": {
        "family": "Century Gothic",
        "style": "Regular",
        "weight": 80.0,
    },
    "CenturyGothic-Bold": {
        "family": "Century Gothic",
        "style": "Bold",
        "weight": 200.0,
    },
    "CenturyGothic-Italic": {
        "family": "Century Gothic",
        "style": "Italic",
        "weight": 80.0,
    },
    "CenturyGothic-BoldItalic": {
        "family": "Century Gothic",
        "style": "Bold Italic",
        "weight": 200.0,
    },
    # ===== Morisawa Fonts (Japanese) =====
    # Ryumin family (classic Japanese serif, first PostScript Japanese font)
    "RyuminPro-Light": {
        "family": "Ryumin Pro",
        "style": "Light",
        "weight": 50.0,
    },
    "RyuminPro-Regular": {
        "family": "Ryumin Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "RyuminPro-Medium": {
        "family": "Ryumin Pro",
        "style": "Medium",
        "weight": 100.0,
    },
    "RyuminPro-Bold": {
        "family": "Ryumin Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    "RyuminPro-Heavy": {
        "family": "Ryumin Pro",
        "style": "Heavy",
        "weight": 210.0,
    },
    "RyuminStd-Light": {
        "family": "Ryumin Std",
        "style": "Light",
        "weight": 50.0,
    },
    "RyuminStd-Regular": {
        "family": "Ryumin Std",
        "style": "Regular",
        "weight": 80.0,
    },
    "RyuminStd-Medium": {
        "family": "Ryumin Std",
        "style": "Medium",
        "weight": 100.0,
    },
    "RyuminStd-Bold": {
        "family": "Ryumin Std",
        "style": "Bold",
        "weight": 200.0,
    },
    # A1 Mincho family (elegant serif with French influence)
    "A1MinchoStd-Regular": {
        "family": "A1 Mincho Std",
        "style": "Regular",
        "weight": 80.0,
    },
    "A1MinchoStd-Bold": {
        "family": "A1 Mincho Std",
        "style": "Bold",
        "weight": 200.0,
    },
    "A1MinchoStd-Light": {
        "family": "A1 Mincho Std",
        "style": "Light",
        "weight": 50.0,
    },
    # A1 Gothic family (sans-serif companion to A1 Mincho)
    "A1GothicStd-Regular": {
        "family": "A1 Gothic Std",
        "style": "Regular",
        "weight": 80.0,
    },
    "A1GothicStd-Bold": {
        "family": "A1 Gothic Std",
        "style": "Bold",
        "weight": 200.0,
    },
    "A1GothicStd-Medium": {
        "family": "A1 Gothic Std",
        "style": "Medium",
        "weight": 100.0,
    },
    # Shin Go family (modern Gothic with high legibility)
    "ShinGoPro-Light": {
        "family": "Shin Go Pro",
        "style": "Light",
        "weight": 50.0,
    },
    "ShinGoPro-Regular": {
        "family": "Shin Go Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "ShinGoPro-Medium": {
        "family": "Shin Go Pro",
        "style": "Medium",
        "weight": 100.0,
    },
    "ShinGoPro-DeBold": {
        "family": "Shin Go Pro",
        "style": "DeBold",
        "weight": 180.0,
    },
    "ShinGoPro-Bold": {
        "family": "Shin Go Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    "ShinGoPro-Heavy": {
        "family": "Shin Go Pro",
        "style": "Heavy",
        "weight": 210.0,
    },
    "ShinGoPro-Ultra": {
        "family": "Shin Go Pro",
        "style": "Ultra",
        "weight": 210.0,
    },
    # Gothic MB101 family (classic sans-serif)
    "GothicMB101Pro-Light": {
        "family": "Gothic MB101 Pro",
        "style": "Light",
        "weight": 50.0,
    },
    "GothicMB101Pro-Regular": {
        "family": "Gothic MB101 Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "GothicMB101Pro-Bold": {
        "family": "Gothic MB101 Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    "GothicMB101Pro-Heavy": {
        "family": "Gothic MB101 Pro",
        "style": "Heavy",
        "weight": 210.0,
    },
    # Jun family (rounded Gothic for friendly designs)
    "Jun101Pro-Light": {
        "family": "Jun 101 Pro",
        "style": "Light",
        "weight": 50.0,
    },
    "Jun101Pro-Regular": {
        "family": "Jun 101 Pro",
        "style": "Regular",
        "weight": 80.0,
    },
    "Jun101Pro-Bold": {
        "family": "Jun 101 Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    # Tazugane Gothic family (modern sans-serif for UI/web)
    "TazuganeGothicStd-Regular": {
        "family": "Tazugane Gothic Std",
        "style": "Regular",
        "weight": 80.0,
    },
    "TazuganeGothicStd-Bold": {
        "family": "Tazugane Gothic Std",
        "style": "Bold",
        "weight": 200.0,
    },
    "TazuganeGothicStd-ExtraBold": {
        "family": "Tazugane Gothic Std",
        "style": "ExtraBold",
        "weight": 205.0,
    },
    # Futo Go family (extra bold Gothic)
    "FutoGoB101Pro-Bold": {
        "family": "Futo Go B101 Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    # Futo Min family (extra bold Mincho)
    "FutoMinA101Pro-Bold": {
        "family": "Futo Min A101 Pro",
        "style": "Bold",
        "weight": 200.0,
    },
    # Midashi Go family (headline Gothic)
    "MidashiGoMB31Pro-DeBold": {
        "family": "Midashi Go MB31 Pro",
        "style": "DeBold",
        "weight": 180.0,
    },
    # Midashi Min family (headline Mincho)
    "MidashiMinMA31Pro-DeBold": {
        "family": "Midashi Min MA31 Pro",
        "style": "DeBold",
        "weight": 180.0,
    },
    # ===== Google Fonts CJK =====
    # Noto Sans CJK Japanese (lowercase PostScript names)
    "NotoSansCJKjp-Thin": {
        "family": "Noto Sans CJK JP",
        "style": "Thin",
        "weight": 0.0,
    },
    "NotoSansCJKjp-Light": {
        "family": "Noto Sans CJK JP",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansCJKjp-DemiLight": {
        "family": "Noto Sans CJK JP",
        "style": "DemiLight",
        "weight": 50.0,
    },
    "NotoSansCJKjp-Regular": {
        "family": "Noto Sans CJK JP",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansCJKjp-Medium": {
        "family": "Noto Sans CJK JP",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansCJKjp-Bold": {
        "family": "Noto Sans CJK JP",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSansCJKjp-Black": {
        "family": "Noto Sans CJK JP",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans CJK Korean (lowercase PostScript names)
    "NotoSansCJKkr-Thin": {
        "family": "Noto Sans CJK KR",
        "style": "Thin",
        "weight": 0.0,
    },
    "NotoSansCJKkr-Light": {
        "family": "Noto Sans CJK KR",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansCJKkr-DemiLight": {
        "family": "Noto Sans CJK KR",
        "style": "DemiLight",
        "weight": 50.0,
    },
    "NotoSansCJKkr-Regular": {
        "family": "Noto Sans CJK KR",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansCJKkr-Medium": {
        "family": "Noto Sans CJK KR",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansCJKkr-Bold": {
        "family": "Noto Sans CJK KR",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSansCJKkr-Black": {
        "family": "Noto Sans CJK KR",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans CJK Simplified Chinese (lowercase PostScript names)
    "NotoSansCJKsc-Thin": {
        "family": "Noto Sans CJK SC",
        "style": "Thin",
        "weight": 0.0,
    },
    "NotoSansCJKsc-Light": {
        "family": "Noto Sans CJK SC",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansCJKsc-DemiLight": {
        "family": "Noto Sans CJK SC",
        "style": "DemiLight",
        "weight": 50.0,
    },
    "NotoSansCJKsc-Regular": {
        "family": "Noto Sans CJK SC",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansCJKsc-Medium": {
        "family": "Noto Sans CJK SC",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansCJKsc-Bold": {
        "family": "Noto Sans CJK SC",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSansCJKsc-Black": {
        "family": "Noto Sans CJK SC",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Sans CJK Traditional Chinese (lowercase PostScript names)
    "NotoSansCJKtc-Thin": {
        "family": "Noto Sans CJK TC",
        "style": "Thin",
        "weight": 0.0,
    },
    "NotoSansCJKtc-Light": {
        "family": "Noto Sans CJK TC",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSansCJKtc-DemiLight": {
        "family": "Noto Sans CJK TC",
        "style": "DemiLight",
        "weight": 50.0,
    },
    "NotoSansCJKtc-Regular": {
        "family": "Noto Sans CJK TC",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSansCJKtc-Medium": {
        "family": "Noto Sans CJK TC",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSansCJKtc-Bold": {
        "family": "Noto Sans CJK TC",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSansCJKtc-Black": {
        "family": "Noto Sans CJK TC",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Serif CJK Japanese (7 weights)
    "NotoSerifCJKjp-ExtraLight": {
        "family": "Noto Serif CJK JP",
        "style": "ExtraLight",
        "weight": 40.0,
    },
    "NotoSerifCJKjp-Light": {
        "family": "Noto Serif CJK JP",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSerifCJKjp-Regular": {
        "family": "Noto Serif CJK JP",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSerifCJKjp-Medium": {
        "family": "Noto Serif CJK JP",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSerifCJKjp-SemiBold": {
        "family": "Noto Serif CJK JP",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "NotoSerifCJKjp-Bold": {
        "family": "Noto Serif CJK JP",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSerifCJKjp-Black": {
        "family": "Noto Serif CJK JP",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Serif CJK Korean (7 weights)
    "NotoSerifCJKkr-ExtraLight": {
        "family": "Noto Serif CJK KR",
        "style": "ExtraLight",
        "weight": 40.0,
    },
    "NotoSerifCJKkr-Light": {
        "family": "Noto Serif CJK KR",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSerifCJKkr-Regular": {
        "family": "Noto Serif CJK KR",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSerifCJKkr-Medium": {
        "family": "Noto Serif CJK KR",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSerifCJKkr-SemiBold": {
        "family": "Noto Serif CJK KR",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "NotoSerifCJKkr-Bold": {
        "family": "Noto Serif CJK KR",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSerifCJKkr-Black": {
        "family": "Noto Serif CJK KR",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Serif CJK Simplified Chinese (7 weights)
    "NotoSerifCJKsc-ExtraLight": {
        "family": "Noto Serif CJK SC",
        "style": "ExtraLight",
        "weight": 40.0,
    },
    "NotoSerifCJKsc-Light": {
        "family": "Noto Serif CJK SC",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSerifCJKsc-Regular": {
        "family": "Noto Serif CJK SC",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSerifCJKsc-Medium": {
        "family": "Noto Serif CJK SC",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSerifCJKsc-SemiBold": {
        "family": "Noto Serif CJK SC",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "NotoSerifCJKsc-Bold": {
        "family": "Noto Serif CJK SC",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSerifCJKsc-Black": {
        "family": "Noto Serif CJK SC",
        "style": "Black",
        "weight": 210.0,
    },
    # Noto Serif CJK Traditional Chinese (7 weights)
    "NotoSerifCJKtc-ExtraLight": {
        "family": "Noto Serif CJK TC",
        "style": "ExtraLight",
        "weight": 40.0,
    },
    "NotoSerifCJKtc-Light": {
        "family": "Noto Serif CJK TC",
        "style": "Light",
        "weight": 50.0,
    },
    "NotoSerifCJKtc-Regular": {
        "family": "Noto Serif CJK TC",
        "style": "Regular",
        "weight": 80.0,
    },
    "NotoSerifCJKtc-Medium": {
        "family": "Noto Serif CJK TC",
        "style": "Medium",
        "weight": 100.0,
    },
    "NotoSerifCJKtc-SemiBold": {
        "family": "Noto Serif CJK TC",
        "style": "SemiBold",
        "weight": 180.0,
    },
    "NotoSerifCJKtc-Bold": {
        "family": "Noto Serif CJK TC",
        "style": "Bold",
        "weight": 200.0,
    },
    "NotoSerifCJKtc-Black": {
        "family": "Noto Serif CJK TC",
        "style": "Black",
        "weight": 210.0,
    },
}
