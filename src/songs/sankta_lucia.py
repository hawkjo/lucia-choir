"""Sankta Lucia — transcribed from '1. Sankta_Lucia_3_voices_sheet.pdf' (Flat).

Notation: pitch + octave / duration (4 = quarter, 8. = dotted eighth ...).
Low is written as on the page (treble-8 clef; sounds an octave lower).
Lyrics: 'syl-' joins to the next syllable, '_' = melisma note (no syllable).
"""

SONG = dict(
    id="sankta-lucia",
    short="Sankta Lucia",
    title="Sankta Lucia",
    subtitle=None,
    credits_left=[],
    credits_right=[],
    meter=(3, 4),
    key=0,
    tempo=80,
    tempo_text=None,
    systems=[4, 4, 4, 4, 2],
    # m1-8, then 9-16 (1st ending 15-16), back to 9-14, 2nd ending 17-18.
    repeat=dict(start=9, end=16, endings={1: [15, 16], 2: [17, 18]}),
    # Hanna Norbäck's sung pronunciation recording + a respelling for English speakers
    pronunciation=dict(
        audio="audio/sankta-lucia-pronunciation.mp3",
        credit="Sung by Hanna Norbäck",
        lines=[
            ("Sankta Lucia, ljusklara hägring,", "SAHNK-tah loo-SEE-ah, YOOS-klah-rah HEHG-ring"),
            ("sprid i vår vinternatt glans av din fägring.", "spreed ee vohr VIN-ter-naht glahns ahv deen FEHG-ring"),
            ("Drömmar av vingesus under oss sia,", "DRÖM-mar ahv VING-eh-soos UN-der oss SEE-ah"),
            ("tänd dina vita ljus, Sankta Lucia.", "tend DEE-nah VEE-tah yoos, SAHNK-tah loo-SEE-ah"),
        ],
        note="The last two lines are sung twice.",
        tips=[
            ("lj", "sounds like “y”, the l is silent: ljus = yoos, ljusklara = YOOS-klah-rah"),
            ("å", "“oh”: vår = vohr"),
            ("ä", "“eh”: hägring, fägring, tänd"),
            ("ö", "the vowel in “bird”, with rounded lips: drömmar"),
            ("u", "“oo” with the lips pushed forward: Lucia, ljus, vingesus"),
            ("i", "always “ee”: sprid, i, din, vita, sia"),
        ],
    ),
    voices=dict(
        melody=dict(
            music="""
            g4/4 g4/4. c5/8 | c5/8 b4/8 b4/2( | f4/4) f4/4. a4/8 | a4/8 g4/8 g4/2 |
            e4/4 a4/4. g4/8 | g4/8 gb4/8 f4/2 | f4/8. g4/32 f4/32 e4/4 d4/4 | a4/4 g4/2 |
            e5/4 d5/4 c5/4 | b4/8 a4/8 d5/2 | d5/4 c5/4 a4/4 | f#4/8 g4/8 c5/2 |
            e5/8 c5/8 c5/8 g4/8 g4/8 e4/8 | f4/8 d5/8 d5/4 r/4 | d5/4 a4/4. b4/8 | d5/4 c5/2 |
            d5/4 e5/4. d5/8 | d5/4 c5/2
            """,
            lyrics=["""
            Sank- ta Lu- | ci- _ a | ljus- kla- ra | häg- _ ring. |
            Sprid i vår | vin- ter- natt | glans _ _ av din | fä- gring. |
            Drö- mar av | vin- ge- sus | un- der oss | si- _ a |
            tänd _ di- _ na _ | vi- ta ljus. | Sank- ta Lu- | ci- a! |
            Sank- ta Lu- | ci- a!
            """],
        ),
        harmony=dict(
            music="""
            g4/4 g4/4 e4/4 | f4/4 f4/4 e4/4 | d4/4 c4/4 b3/4 | c4/4 e4/4 d4/4 |
            c4/4 c#4/4 a3/4 | d4/4 d4/4 c4/4 | b3/4 g3/4 b3/4 | c4/8 d4/8 e4/2 |
            g4/4 f4/4 g4/4 | f4/4 a4/4 g4/4 | f4/4 e4/4 d4/4 | d#4/8 e4/8 g4/2 |
            c5/8 g4/8 g4/8 e4/8 e4/8 c4/8 | d4/8 f4/8 a4/4 g4/4 | a4/4 g4/4 f4/4 | f4/4 e4/2 |
            a4/4 g4/4 f4/4 | f4/4 e4/2
            """,
            lyrics=["""
            Sank- ta Lu- | ci- a _ | ljus- kla- ra | häg- ring _ |
            Sprid i vår | vin- ter- natt | glans av din | fä- _ gring |
            Drö- mar av | vin- ge- sus | un- der oss | si- _ a |
            tänd _ di- _ na _ | vi- ta ljus _ | Sank- ta Lu- | ci- a! |
            Sank- ta Lu- | ci- a!
            """],
        ),
        low=dict(
            octave_shift=-12,
            music="""
            c5/4 c5/4 c5/4 | a4/4 d5/4 c5/4 | b4/4 a4/4 f4/4 | e4/4 g4/2 |
            g4/4 f4/4 e4/4 | d4/4 d4/4 d4/4 | g4/4 g4/4 g4/4 | c5/4 c5/2 |
            c5/4 a4/4 g4/4 | a4/4 d5/4 a4/4 | g4/4 a4/4 f#4/4 | f#4/8 g4/8 c5/2 |
            e4/4 g4/4 g4/4 | a4/8 g4/8 f4/4 a4/4 | d4/4 g4/4 g4/4 | c5/4 c5/2 |
            d4/4 g4/4 g4/4 | c5/4 c5/2
            """,
            lyrics=["""
            Sank- ta Lu- | ci- a _ | ljus- kla- ra | häg- ring. |
            Sprid i vår | vin- ter- natt | glans av din | fä- gring. |
            Drö- mar av | vin- ge- sus | un- der oss | si- _ a |
            tänd di- na | vi- ta ljus. _ | Sank- ta Lu- | ci- a! |
            Sank- ta Lu- | ci- a!
            """],
        ),
    ),
)
