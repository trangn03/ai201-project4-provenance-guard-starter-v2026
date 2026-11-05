"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

# Calibration texts, shared by criteria 2 and 3. Scored offline against the
# current config (0.35 / 0.65 bands) when chosen, so each one's expected label
# is written next to it — if a later change moves one, that's a finding.
CLEARLY_AI = (  # combined ~0.74 -> ai
    "Artificial intelligence is transforming the way organizations operate in "
    "the modern world. By leveraging advanced algorithms, businesses can "
    "streamline their processes, enhance productivity, and deliver more "
    "personalized experiences to their customers. Furthermore, the integration "
    "of machine learning into everyday workflows enables teams to make "
    "data-driven decisions with greater confidence. It is important to note "
    "that responsible adoption requires careful consideration of ethical "
    "implications, transparency, and accountability. Ultimately, organizations "
    "that embrace these technologies thoughtfully will be well positioned to "
    "thrive in an increasingly competitive landscape."
)
CLEARLY_HUMAN = (  # combined ~0.32 -> human
    "ok so the bus was late AGAIN and i'm standing there in the drizzle like "
    "an idiot, no umbrella, phone at 3%. a woman next to me offers to share "
    "hers and we end up talking about her dog (Biscuit, a deaf spaniel, "
    "apparently he steals socks?). anyway the 47 finally shows up forty "
    "minutes late and she gets off two stops before me. never got her name. "
    "wish i had."
)
PLAIN_HUMAN = (  # combined ~0.61 -> unsure (signal one's blind spot)
    "We got to the campsite about four. The pitch was fine, a bit sloped, but "
    "there was a tap nearby and the toilets were clean enough. Putting the "
    "tent up took longer than it should have because I had forgotten how the "
    "poles went. The weather held until Saturday night. Then it rained hard "
    "and kept raining. We stayed in the tent and played cards and ate most of "
    "the food we had brought for Sunday. On Sunday we packed up wet and drove "
    "home early. It was not the weekend we planned but the kids enjoyed it "
    "and we would go back."
)
EDITED_AI = (  # combined ~0.51 -> unsure
    "Artificial intelligence is changing how organizations operate. By using "
    "better algorithms, businesses can speed up their processes and give "
    "customers a more personal experience. Machine learning in everyday "
    "workflows helps teams make decisions with more confidence, though my own "
    "team still argues about the numbers every Friday. Responsible adoption "
    "needs careful thought about ethics, transparency and accountability. "
    "Organizations that take these tools seriously will be well placed to do "
    "well in a crowded market."
)

SCENARIOS = [
    # Criterion 1 — false positives: at most 1 of 10 plainly-written human
    # paragraphs scores high-confidence AI, in every one of 3 trials.
    # Ten paragraphs from my own coursework (Music Appreciation written
    # assignments, June 2021), typos and all. Left out: the answers that read
    # as encyclopedia definitions, and the one that names me and my school.
    {
        "name": "my own writing",
        "criterion": 1,
        "texts": [
        (
            "I decided to take Music Appreciation online because I am curious about"
            " the history of music and the development of music. I have always been"
            " passionate about music, especially Hamilton the musical since the "
            "beats are very innovative and catchy. By the end of this class, I "
            "would love to have more knowledge about different kinds of music and "
            "recognize the emotion of composers. Second, I want to sing better such"
            " as clearly showing the high or low melody."
        ),
        (
            "Baa Baa Black Sheep is written by a Swedish music teacher named Alice "
            "Tegner. The original song is Bä, bä, vita lamm. I think it is ternary "
            "form because the phrase is repeated the same melody and it extends the"
            " idea of tax on wool during thirteen century and departure by bringing"
            " back the first section"
        ),
        (
            "On Monday, I had dinner at my uncle’s house and we got a chance to "
            "watch a basketball competition on TV. The music was so aggressive and "
            "intense when the players were coming out of the basketball court. As "
            "they scored a point to the basket, the cheering sound, or music from "
            "the speaker played. There was not so much percussion or brass sound "
            "and I noticed that it was a random pattern because the players "
            "performed differently when they got a score or they missed."
        ),
        (
            "During the Middle Ages, Catholic Church started to make systematic use"
            " of musical notation. Church music was the highest type of music, and "
            "those who composed it were the most accomplished musicians, and they "
            "have frequently sung about religious topics. Secular music was "
            "distinct in that it incorporated elements such as dance or witty "
            "lyrics, and the church attempted to outlaw it on the grounds that it "
            "was blasphemous. Based on the text, it concludes that reformers "
            "believed that monophonic congregational singing in the vernacular "
            "should define Christian worship, while Catholic prefered trained "
            "singer and polyphony."
        ),
        (
            "Sacred music is associated with religious or expanded approaches to "
            "sung spiritual worship. Sacred music only focuses on religious aspects"
            " with more lines of crusades, dancing but it had few limited theme "
            "songs. Secular music is everything else including social music-making "
            "for entertainment and personal expression. Medieval and Renaissance "
            "instruments, used primarily for secular music, were categorized as "
            "loud such as drums, harps, bagpipes, etc. So, it is clear that secular"
            " music had a lot of use of instruments when compared to sacred music."
        ),
        (
            "Music was a basic piece of city, strict, and dignified life in the "
            "Renaissance. With the rise of Renaissance polyphony, composers "
            "concentrated their musical settings on the ordinary. In the matter of "
            "harmony, composers of the Renaissance leaned toward fuller chords. One"
            " of the most popular genres was the motet, it is the ability to "
            "combine newly written texts of praise with prescribed prayers."
        ),
        (
            "Basse danse was a popular court dance that took place in Burgundian "
            "Courts, where people glided slowly and gracefully without having their"
            " feet leave the floor. Dancers usually follow the melody 6/4 and 3/2 "
            "time. There were four types of steps: pas simple, pas double, "
            "demarche, and branle."
        ),
        (
            "The lute, harpsichord, and contrabassoon are among the strange and "
            "fantastic instruments that frequently appear in a baroque ensemble. "
            "Baroque opera's plots range from heartbreaking drama to hysterical "
            "comedy, and are frequently based on Greek and Roman mythology. "
            "Musicians were familiar with the basic harmonies, the composer put a "
            "numeral above or below the bass note, indicating the chord required (a"
            " kind of notation called figured bass), and the performer filled in "
            "the necessary harmony. This system, known as basso continuo, provided "
            "a foundation over which a vocal or instrumental melody could unfold. "
            "It led to one of the most significant changes in all music history: "
            "the establishment of major minor tonality. Dramatic elements of "
            "baroque opera combined various elements of poetry and drama.Visual "
            "elements are generally incorporated scenery and costumes, and even "
            "dance through valleys. Opera is a hybrid of various art forms. Opera's"
            " usage of numerous art forms contributes significantly to its appeal. "
            "Opera is a unique art form that blends singing, acting, symphonic "
            "music, poetry, dance, mime, theatrical scenery, costumes, and "
            "lighting."
        ),
        (
            "King George II attended the London premier and allegedly rose to his "
            'feet during the "Hallelujah Chorus" during a royal performance of '
            "Messiah in March of 1743. When the king stood up, everyone else in the"
            " room had to stand up as well. In 1770, the Hallelujah Chorus was "
            "introduced to America, and it quickly spread over the Eastern United "
            "States. The chorus had already become the most popular finishing piece"
            " for choral concerts in America's musical cities by the time the whole"
            " oratorio arrived in Boston in 1818. A shift in Christmas celebrations"
            " occurred shortly after the premiere of Messiah. These revisions aided"
            " the popularity of Messiah's seasonal performances, quickly "
            "transforming it into a Christmas oratorio."
        ),
        (
            "Guitar belongs to string family instruments. They are usually made "
            "from wood and the strings are made of steel or nylon. The sound is "
            "produced from hollow wood and six strings. The players play guitar by "
            "plucking the strings with the fingers and fingernails of the right "
            "hand or left hand (if they are left hand players), or a small pick "
            "(called plectrum). Guitars are used for many types of music such as "
            "pop, rock, country, jazz, blues, etc."
        ),
        ],
    },

    # Criterion 2 — score spread: clearly-AI and clearly-human calibration
    # texts land >= 0.4 apart on combined_score in all 3 trials. The response
    # has no combined_score, so read it from the audit log (creator_ids are
    # eval_score spread_1 / _2) — the report only shows model/style scores.
    {
        "name": "score spread",
        "criterion": 2,
        "texts": [CLEARLY_AI, CLEARLY_HUMAN],
    },

    # Criterion 3 — label coverage: human, unsure and AI each produced by at
    # least one of the four calibration inputs in at least 2 of 3 trials.
    {
        "name": "label coverage",
        "criterion": 3,
        "texts": [CLEARLY_AI, CLEARLY_HUMAN, PLAIN_HUMAN, EDITED_AI],
    },

    # Criterion 4 — the appeal path (10 of 10 appeals move status to
    # under_review and sit beside the original entry) is NOT here: it needs a
    # submission and then an appeal against the content_id that came back,
    # which neither "texts" nor "bodies" can express. Tested by hand / with a
    # separate script, and the README says so.

    # Criterion 5 — bad input: missing, empty and oversized text each return a
    # 4xx, never a 5xx, in every trial.
    {
        "name": "bad input",
        "criterion": 5,
        "bodies": [
            {"creator_id": "eval_bad_missing"},                    # no text field
            {"text": "", "creator_id": "eval_bad_empty"},
            {"text": "word " * 50000, "creator_id": "eval_bad_huge"},  # 50,000 words
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
