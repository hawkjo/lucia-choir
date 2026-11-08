"""Jul, jul, strålande jul — transcribed from '3. Jul, Jul Strålande Jul.pdf' (Flat).

'<f4 a4>/16' = chord (divisi). The empty final bar of the Flat score is dropped.
"""

SONG = dict(
    id="jul-jul",
    short="Jul, jul",
    title="Jul, jul, strålande jul",
    subtitle="in C major",
    credits_left=["Edvard Evers"],
    credits_right=["Gustaf Nordqvist", "bearb. Hanna Norbäck"],
    meter=(6, 8),
    key=0,
    tempo=45,
    tempo_text=None,
    systems=[4, 3, 3, 4, 2],
    repeat=None,
    # Hanna Norbäck's sung pronunciation recording + a respelling for English speakers
    pronunciation=dict(
        audio="audio/jul-jul-pronunciation.mp3",
        credit="Sung by Hanna Norbäck",
        lines=[
            ("Jul, jul, strålande jul,", "yool, yool, STROH-lahn-deh yool,"),
            ("glans över vita skogar,", "glahns ÖÖ-ver VEE-tah SKOO-gar,"),
            ("himmelens kronor med gnistrande ljus,", "HIM-meh-lens KROO-nor mehd GNIST-rahn-deh yoos,"),
            ("glimmande bågar i alla Guds hus,", "GLIM-mahn-deh BOH-gar ee AH-lah gudds hoos,"),
            ("psalm, som är sjungen från tid till tid,", "sahlm, som air HWUNG-en frohn teed till teed,"),
            ("eviga längtan till ljus och frid!", "EH-vi-gah LENG-tahn till yoos ock freed!"),
            ("Jul, jul, strålande jul: glans över vita skogar!", "yool, yool, STROH-lahn-deh yool: glahns ÖÖ-ver VEE-tah SKOO-gar!"),
        ],
        note=None,
        tips=[
            ("j, lj", "sound like “y”, the l is silent: jul = yool, ljus = yoos"),
            ("å", "“oh”: strålande, bågar, från"),
            ("o", "“oo” in skogar and kronor: SKOO-gar, KROO-nor"),
            ("sj", "a soft, breathy sound between “sh” and “hw”: sjungen"),
            ("psalm", "the p is silent: sahlm"),
            ("gn", "say the g too: gnistrande = g-NIST-rahn-deh"),
            ("-nde", "the final e is sung: STROH-lahn-deh, GLIM-mahn-deh"),
        ],
    ),
    voices=dict(
        melody=dict(
            music="""
            e4/4. d4/4. | e4/8. f4/16 g4/8 d4/4. | e4/8 f4/8 g4/8 g4/4 f4/8 | f4/4. e4/4. |
            a4/8. a4/16 a4/8 g4/8 d4/8 g4/8 | a4/8. b4/16 a4/8 g4/4. | f4/8. f4/16 f4/8 e4/8 b3/8 e4/8 |
            f4/8. g4/16 f4/8 e4/4. | c4/8. c4/16 c4/8 g4/8. g4/16 g4/8 | e4/4 e4/8 c4/4. |
            d4/8. c4/16 d4/8 e4/8. d4/16 c4/8 | d4/8. c4/16 d4/8 e4/4. | e4/4. d4/4. | e4/8. f4/16 g4/8 d4/4. |
            e4/8 f4/8 g4/8 g4/4 f4/8 | d4/4. c4/4.
            """,
            lyrics=["""
            Jul, jul, | strå- lan- de jul, | glans ö- ver vi- ta | sko- gar. |
            him- me- lens kro- nor med | gnist- ran- de ljus | glim- man- de bå- gar i |
            al- la Guds hus, | psalm som är sjung- en från | tid till tid, |
            e- vi- ga läng- tan till | ljus _ och frid! | Jul, jul, | strå- lan- de jul: |
            glans ö- ver vi- ta | sko- gar!
            """],
        ),
        harmony=dict(
            music="""
            c4/4. c4/4. | c4/8. c4/16 c4/8 c4/4. | c4/8 c4/8 c4/8 c4/4 c4/8 | c4/4 b3/8 c4/4. |
            c4/8. c4/16 f4/8 d4/8 b3/8 d4/8 | f4/8. f4/16 f4/8 d4/4. | d4/8. d4/16 c4/8 b3/8 g#3/8 b3/8 |
            d4/8. d4/16 c4/8 b3/4. | c4/8. b3/16 a3/8 c4/8. b3/16 c4/8 | b3/4 b3/8 a3/4. |
            a3/8. a3/16 b3/8 c4/8. b3/16 a3/8 | a3/8.~ a3/16 b3/8 b3/4. | c4/4. c4/4. | c4/8. c4/16 c4/8 c4/4. |
            c4/8 c4/8 c4/8 c4/4 c4/8 | b3/4. <g3 c4>/4.
            """,
            lyrics=[],
        ),
        low=dict(
            octave_shift=-12,
            music="""
            g4/4. g#4/4. | g4/8. g4/16 g4/8 g#4/4. | g4/8 a4/8 b4/8 b4/4 a4/8 | a4/4 g#4/8 g4/4. |
            f4/8. f4/16 c5/8 b4/8 g4/8 b4/8 | c5/8. d5/16 c5/8 b4/4. | a4/8. b4/16 a4/8 g#4/8 e4/8 g#4/8 |
            a4/8. b4/16 a4/8 g#4/4. | a4/8. g4/16 f4/8 g4/8. f4/16 g4/8 | g4/4 g4/8 f4/4. |
            f4/8. f4/16 f4/8 a4/8. <f4 a4>/16 <e4 a4>/8 | a4/8.~ a4/16 a4/8 g#4/4. | g4/4. g#4/4. | g4/8. g4/16 g4/8 g#4/4. |
            g4/8 a4/8 b4/8 b4/4 a4/8 | a4/8 g4/8 f4/8 <e4 g4>/4.
            """,
            lyrics=["""
            Jul, jul, | strå- lan- de jul, | glans ö- ver vi- ta | sko- _ gar. |
            him- me- lens kro- nor med | gnist- ran- de ljus | glim- man- de bå- gar i |
            al- la Guds hus, | psalm som är sjung- en från | tid till tid, |
            e- vi- ga läng- tan till | ljus och frid! | Jul, jul, | strå- lan- de jul: |
            glans ö- ver vi- ta | sko- _ _ gar!
            """],
        ),
    ),
)
