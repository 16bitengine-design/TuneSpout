"""Automatic titles, descriptions and hashtags for YouTube and TikTok.

Everything is built from the lesson itself (topic, kids' names, tags), so no
one writes captions by hand. Same lesson -> same text (crc32, not random).
"""
import json
import zlib
from pathlib import Path

TOPIC_INFO = {
    "counting": {"skill": "counting numbers in order", "ages": "ages 3 to 6",
                 "tags": ["counting", "learntocount", "numbers", "preschoolmath"],
                 "hooks": ["Can you count along with us?", "Let us count together!"]},
    "addition": {"skill": "adding two numbers together", "ages": "ages 5 to 8",
                 "tags": ["addition", "mathforkids", "learntoadd", "kidsmath"],
                 "hooks": ["Can you add them up before the answer?", "Adding is easy with friends!"]},
    "subtraction": {"skill": "taking away to find what is left", "ages": "ages 5 to 8",
                    "tags": ["subtraction", "mathforkids", "takeaway", "kidsmath"],
                    "hooks": ["How many are left? Count with us!", "Taking away made simple!"]},
    "multiplication": {"skill": "multiplying with groups and times tables", "ages": "ages 6 to 10",
                       "tags": ["multiplication", "timestables", "mathforkids", "kidsmath"],
                       "hooks": ["Groups make counting fast!", "Times tables with friends!"]},
    "division": {"skill": "dividing by sharing fairly", "ages": "ages 6 to 10",
                 "tags": ["division", "sharing", "mathforkids", "kidsmath"],
                 "hooks": ["Fair shares for everyone!", "Can you share them fairly?"]},
    "plurals": {"skill": "plural words: one and many", "ages": "ages 4 to 8",
                "tags": ["plurals", "englishforkids", "learnenglish", "grammarforkids"],
                "hooks": ["One or many? You decide!", "Add an s to make more!"]},
    "sports": {"skill": "the names of sports and how we play them", "ages": "ages 3 to 8",
               "tags": ["sportsforkids", "kidsexercise", "learnsports", "activekids"],
               "hooks": ["Which sport is your favorite?", "Let us move and learn!"]},
    "teamscore": {"skill": "adding team goals together", "ages": "ages 5 to 8",
                  "tags": ["sportsmath", "addition", "teamwork", "mathforkids"],
                  "hooks": ["Add up the goals with us!", "Teams count together!"]},
    "fairplay": {"skill": "playing fair, taking turns and cheering for friends", "ages": "ages 4 to 9",
                 "tags": ["fairplay", "teamwork", "kindness", "sportsforkids"],
                 "hooks": ["Fair play makes everyone smile!", "Take turns and cheer!"]},
    "animalsounds": {"skill": "animal names and the sounds they make", "ages": "ages 2 to 6",
                     "tags": ["animalsounds", "animalsforkids", "farmanimals", "learnanimals"],
                     "hooks": ["What does the cow say? Sing along!", "Can you make the animal sounds?"]},
    "babyanimals": {"skill": "the names of baby animals", "ages": "ages 3 to 7",
                    "tags": ["babyanimals", "animalsforkids", "youngones", "learnanimals"],
                    "hooks": ["Do you know what a baby cow is called?", "Meet the baby animals!"]},
    "phonics": {"skill": "letter sounds and the first sound of words", "ages": "ages 3 to 6",
                "tags": ["phonics", "lettersounds", "learntoread", "alphabetforkids"],
                "hooks": ["What sound does this letter make?", "Let us sound out letters together!"]},
    "spelling": {"skill": "spelling short words one letter at a time", "ages": "ages 4 to 7",
                 "tags": ["spelling", "spellingforkids", "learntoread", "sightwords"],
                 "hooks": ["Can you spell it with us?", "Letter by letter, we spell it!"]},
}
COMMON_TAGS = ["kidslearning", "educationalvideos", "cartoonsforkids", "kidssongs", "learningforkids"]
FALLBACK = {"skill": "learning something new", "ages": "ages 3 to 10",
            "tags": ["kidseducation"], "hooks": ["Learn with us!"]}


def _info(lesson):
    return TOPIC_INFO.get(lesson.get("topic"), FALLBACK)


def hashtags(lesson, n):
    seen, out = set(), []
    for tag in _info(lesson)["tags"] + COMMON_TAGS:
        if tag not in seen:
            seen.add(tag)
            out.append("#" + tag)
    return out[:n]


def kid_names(lesson):
    names = []
    for sc in lesson["scenes"]:
        for kid in sc.get("kids", []):
            if kid.get("name") and kid["name"] not in names:
                names.append(kid["name"])
    return names


def youtube(lesson):
    info = _info(lesson)
    names = " and ".join(kid_names(lesson)) or "our friends"
    tags = hashtags(lesson, 8)  # YouTube ignores hashtags if there are more than 15
    description = "\n".join([
        lesson.get("description", ""),
        "",
        "In this video:",
        f"• {names} practice {info['skill']}",
        f"• Short, gentle sentences made for kids {info['ages']}",
        "• Everyday things kids can count, add and share",
        "",
        "A new lesson every day. Subscribe so you never miss one!",
        "",
        " ".join(tags),
        "",
        "For parents: no violence or scary content. The voice is computer-generated.",
    ])
    keywords = list(lesson.get("tags", [])) + [t[1:] for t in tags]
    return {"title": lesson["title"][:100], "description": description,
            "tags": list(dict.fromkeys(keywords))}


def tiktok(lesson):
    info = _info(lesson)
    short_title = lesson["title"].split("|")[0].strip()
    hook = info["hooks"][zlib.crc32(lesson["title"].encode()) % len(info["hooks"])]
    caption = f"{short_title}! {hook}\n\n" + " ".join(hashtags(lesson, 5))
    return {"caption": caption[:2200], "is_aigc": True}  # voice is AI-generated: label it


def write_metadata(lesson, out_dir):
    out = Path(out_dir)
    (out / "meta.json").write_text(json.dumps(youtube(lesson), indent=2, ensure_ascii=False))
    (out / "tiktok.json").write_text(json.dumps(tiktok(lesson), indent=2, ensure_ascii=False))
