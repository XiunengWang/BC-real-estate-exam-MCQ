import csv, re, unicodedata


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", (s or "")).strip()


_ANS_NUM_RE = re.compile(r"(\d+)")
_ANS_LET_RE = re.compile(r"\b([A-D])\b", re.I)


def parse_correct_index(answer_text: str, num_choices: int):
    s = _norm(answer_text)
    if not s:
        return None
    m = _ANS_NUM_RE.search(s)
    if m:
        idx = int(m.group(1)) - 1
        return idx if 0 <= idx < num_choices else None
    m = _ANS_LET_RE.search(s)
    if m:
        idx = ord(m.group(1).upper()) - ord("A")
        return idx if 0 <= idx < num_choices else None
    return None


# def parse_choices(choices_text: str):
#     # return [c.strip() for c in (choices_text or "").split("|") if c.strip()]
#     return [(c.lstrip() if c else "") for c in (choices_text or "").split("|")]
def parse_choices(choices_text: str):
    raw = choices_text or ""
    parts = raw.split("|")

    cleaned = []
    for c in parts:
        # Remove a leading apostrophe Excel uses to force Text
        if c.startswith("'"):
            c = c[1:]

        # Normalize invisible / nonbreaking spaces to normal space
        c = c.translate(
            {
                ord("\u00a0"): " ",
                ord("\u202f"): " ",
                ord("\u2009"): " ",
                ord("\u2007"): " ",
                ord("\u200a"): " ",
                ord("\u200b"): " ",
            }
        )

        # Keep inner spacing; only trim *left* so separators can be “ | …”
        c = c.lstrip()

        cleaned.append(c)

    # Drop empty choices
    return [x for x in cleaned if x.strip() != ""]


def row_to_question(row: dict) -> dict:
    qid = str(row.get("Question_int", "")).strip()
    prompt = _norm(row.get("question", ""))
    choices = parse_choices(row.get("choices", ""))
    explanation_html = row.get("back", "") or ""
    ans_raw = row.get("answer", "")
    correct_index = parse_correct_index(ans_raw, len(choices))
    if correct_index is None:
        raise ValueError(f"Invalid or empty answer field: {ans_raw!r}")
    raw_calc = (row.get("calc", "") or "").strip().lower()
    is_calc = raw_calc in {"1", "y", "yes", "true", "t"}
    return {
        "id": qid,
        "prompt": prompt,
        "choices": choices,
        "correct_index": correct_index,
        "explanation_html": explanation_html,
        "type": "mc_single",
        "deck_id": "default",
        "is_calc": is_calc,
    }


def load_questions_from_csv(path: str):
    questions, problems = [], []
    with open(csv_path, mode="r", newline="", encoding="latin1") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            try:
                questions.append(row_to_question(row))
            except Exception as e:
                problems.append(
                    {
                        "row_num": i,
                        "error": str(e),
                        "row": {
                            k: row.get(k, "")
                            for k in [
                                "Question_int",
                                "question",
                                "choices",
                                "answer",
                                "calc",
                            ]
                        },
                    }
                )
    return questions, problems
