"""In the Bleak Midwinter — converted from 'In the Bleak Midwinter (SAB).pdf'.

The SAB score (Soprano/Alto on one staff, Baritone in bass clef) is re-laid out in the
choir's usual format: Melody (= Soprano), Harmony (= Alto), Low (= Baritone, treble-8 clef).

'~1,3' = tie that applies only in verses 1 and 3 (drawn dashed).
'{' ... '}' = dashed slur (melisma in some verses only).
The Low line is entered at sounding pitch (as in the bass-clef original).
"""

_DYN = [
    dict(kind="dynam", m=1, tstamp=1, text="mp"),
    dict(kind="hairpin", form="cres", m=9, tstamp=1, m2=9, tstamp2=4.8),
    dict(kind="dynam", m=10, tstamp=1, text="mf"),
    dict(kind="hairpin", form="dim", m=10, tstamp=2.2, m2=11, tstamp2=4.8),
    dict(kind="dynam", m=12, tstamp=1, text="mp"),
    dict(kind="dynam", m=13, tstamp=1, text="p"),
]

SONG = dict(
    id="bleak-midwinter",
    short="Bleak Midwinter",
    title="In the Bleak Midwinter",
    subtitle=None,
    credits_left=["Words: Christina Rossetti (1872)", "verses 1, 4 and 5"],
    credits_right=["Music: CRANHAM, Gustav Holst (1906)", "SAB arrangement after Holst's harmony"],
    meter=(4, 4),
    meter_sym="common",
    key=-1,
    tempo=66,
    tempo_text="Gently",
    systems=[4, 4, 4, 4],
    # Whole song three times (three verses); ritardando the third time from bar 15.
    repeat=dict(start=1, end=16, times=3, rit=dict(pass_=3, from_m=15, factor=0.68)),
    directions=[dict(kind="dir", m=15, tstamp=1, text="rit. 3rd time", staff="melody")],
    voices=dict(
        melody=dict(
            dynamics=_DYN,
            music="""
            a4/4.{ bb4/8} c5/4 a4/4 | g4/2 f4/2 | g4/4.{ a4/8} g4/4 d4/4 | g4/1 |
            a4/4. bb4/8 c5/4 a4/4 | g4/4~1,3 g4/4 f4/2 | g4/4{ a4/4 g4/4.} f4/8 | f4/1 |
            bb4/4. a4/8 bb4/4 c5/4 | d5/2 a4/2 | c5/4{ a4/4} g4/4 f4/4 | e4/1 |
            a4/4. bb4/8 c5/4 a4/4 | g4/4~1,2 g4/4 f4/2 | g4/4( a4/4 g4/4.) f4/8 | f4/2. r/4
            """,
            lyrics=[
                """
                [1.] In the bleak mid- | win- ter, | frost- y wind made | moan, |
                Earth stood hard as | i- ron, | wa- ter like a | stone; |
                Snow had fal- len, | snow on | snow, _ snow on | snow, |
                In the bleak mid- | win- ter, | long _ _ a- | go.
                """,
                """
                [2.] An- gels and arch- | an- gels | may have gath- ered | there, |
                Cher- u- bim and | ser- a- phim | thronged _ _ the | air; |
                But on- ly his | moth- er | in her maid- en | bliss |
                wor- shipped the be- | lov- ed | with _ _ a | kiss.
                """,
                """
                [3.] What _ can I | give him, | poor _ as I | am? |
                If I were a | shep- herd | I would bring a | lamb; |
                If I were a | wise man | I would do my | part; |
                Yet what I can | I give him: | give _ _ my | heart.
                """,
            ],
        ),
        harmony=dict(
            dynamics=_DYN,
            music="""
            f4/4.~3 f4/8 f4/4 c4/4 | d4/2 d4/2 | d4/4.~3 d4/8 d4/4 c4/4 | bb3/1 |
            c4/4. f4/8 f4/4 c4/4 | d4/4~1,3 d4/4 d4/2 | f4/4{ f4/4 e4/4.} c4/8 | a3/1 |
            f4/4. f4/8 f4/4 eb4/4 | d4/2 f4/2 | f4/4{ c4/4} d4/4 d4/4 | c4/1 |
            c4/4. f4/8 f4/4 c4/4 | d4/4~1,2 d4/4 d4/2 | f4/2( e4/4.) c4/8 | a3/2. r/4
            """,
            lyrics=[
                """
                [1.] In the bleak mid- | win- ter, | frost- y wind made | moan, |
                Earth stood hard as | i- ron, | wa- ter like a | stone; |
                Snow had fal- len, | snow on | snow, _ snow on | snow, |
                In the bleak mid- | win- ter, | long _ a- | go.
                """,
                """
                [2.] An- gels and arch- | an- gels | may have gath- ered | there, |
                Cher- u- bim and | ser- a- phim | thronged _ _ the | air; |
                But on- ly his | moth- er | in her maid- en | bliss |
                wor- shipped the be- | lov- ed | with _ a | kiss.
                """,
                """
                [3.] What can I | give him, | poor as I | am? |
                If I were a | shep- herd | I would bring a | lamb; |
                If I were a | wise man | I would do my | part; |
                Yet what I can | I give him: | give _ my | heart.
                """,
            ],
        ),
        low=dict(
            dynamics=_DYN,
            input="sounding",
            music="""
            f3/4.{ g3/8} a3/4 f3/4 | d3/2 d3/2 | bb2/4.{ c3/8} bb2/4 f3/4 | f3/2( e3/2) |
            f3/4. g3/8 a3/4 f3/4 | d3/4~1,3 d3/4 d3/2 | bb2/4{ bb2/4 c3/4.} f3/8 | f3/1 |
            d3/4. f3/8 d3/4 a2/4 | bb2/2 d3/2 | a2/4~1 a2/4 bb2/4 bb2/4 | c3/1 |
            f3/4. g3/8 a3/4 f3/4 | d3/4~1,2 d3/4 d3/2 | bb2/2( c3/4.) f3/8 | f3/2. r/4
            """,
            lyrics=[
                """
                [1.] In the bleak mid- | win- ter, | frost- y wind made | moan, _ |
                Earth stood hard as | i- ron, | wa- ter like a | stone; |
                Snow had fal- len, | snow on | snow, snow on | snow, |
                In the bleak mid- | win- ter, | long _ a- | go.
                """,
                """
                [2.] An- gels and arch- | an- gels | may have gath- ered | there, _ |
                Cher- u- bim and | ser- a- phim | thronged _ _ the | air; |
                But on- ly his | moth- er | in her maid- en | bliss |
                wor- shipped the be- | lov- ed | with _ a | kiss.
                """,
                """
                [3.] What _ can I | give him, | poor _ as I | am? _ |
                If I were a | shep- herd | I would bring a | lamb; |
                If I were a | wise man | I would do my | part; |
                Yet what I can | I give him: | give _ my | heart.
                """,
            ],
        ),
    ),
)
