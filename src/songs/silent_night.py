"""Silent Night / Stille Nacht — transcribed from '2. Silent_night_3_voices_sheet.pdf' (Flat).

',' after a note = breath mark. '(' ... ')' = slur.
"""

SONG = dict(
    id="silent-night",
    short="Silent Night",
    title="Silent Night / Stille Nacht",
    subtitle="without solo",
    credits_left=["Franz Gruber"],
    credits_right=["arr. John Rutter", "bearb. Hanna Norbäck"],
    meter=(6, 8),
    key=3,
    tempo=50,
    tempo_text=None,
    systems=[3, 3, 3, 3],
    repeat=None,
    voices=dict(
        melody=dict(
            music="""
            e4/8. f#4/16 e4/8 c#4/4. , | e4/8. f#4/16 e4/8 c#4/4. , | b4/4 b4/8 g#4/4.( |
            a4/4) a4/8 e4/4. , | f#4/4 f#4/8 a4/8. g#4/16 f#4/8( | e4/8.) f#4/16 e4/8 c#4/4. |
            f#4/4 f#4/8 a4/8. g#4/16 f#4/8( | e4/8.) f#4/16 e4/8 c#4/4. | b4/4 b4/8 d5/8. b4/16 g#4/8 |
            a4/4.( c#5/4.) , | a4/8 e4/8 c#4/8 e4/8. d4/16 b3/8 | a3/2.
            """,
            lyrics=[
                """
                [1,3.] Si- _ lent night! | ho- _ ly night! | All is calm, |
                all is bright | Round yon vir- _ gin | mo- ther and child, |
                Ho- ly in- fant so | ten- der and mild, | Sleep in hea- ven- ly |
                peace, _ | Sleep _ in hea- ven- ly | peace.
                """,
                """
                [2.] Stil- _ le Nacht! | hei- li- ge Nacht! | Al- les schläft, |
                ein- sam wacht | Nur das trau- te hoch- | hei- li- ge Paar. |
                Hol- der Kna- be im | lock- i- gen Haar, | Schlaf in himm- li- scher |
                Ruh', _ | Schlaf _ in himm- li- scher | Ruh.
                """,
            ],
        ),
        harmony=dict(
            music="""
            c#4/8. d4/16 c#4/8 a3/4. , | c#4/8. d4/16 c#4/8 a3/4. , | d4/4 d4/8 b3/4.( |
            c#4/4) c#4/8 a3/4. , | d4/4 d4/8 f#4/8. e4/16 d4/8( | c#4/8.) d4/16 c#4/8 a3/4. |
            d4/4 d4/8 f#4/8. e4/16 d4/8( | c#4/8.) d4/16 c#4/8 a3/4. | d4/4 d4/8 b3/8. d4/16 b3/8 |
            c#4/4.( e4/4.) , | c#4/4 a3/8 g#3/8. b3/16 g#3/8 | a3/2.
            """,
            lyrics=[],
        ),
        low=dict(
            octave_shift=-12,
            music="""
            e4/4 e4/8 a4/4. , | e4/4 e4/8 a4/4. , | g#4/4 g#4/8 b4/4.( |
            a4/4) a4/8 a4/4. , | a4/4 a4/8 a4/8. a4/16 a4/8( | a4/8.) a4/16 a4/8 e4/4. |
            a4/4 a4/8 a4/8. a4/16 a4/8( | a4/8.) a4/16 a4/8 e4/4. | g#4/4 g#4/8 b4/8. g#4/16 b4/8 |
            a4/4.( e4/4.) , | a4/4 a4/8 b4/8. b4/16 b4/8 | a4/2.
            """,
            lyrics=[],
        ),
    ),
)
