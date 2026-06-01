"""
Deterministic English grammar question engine.

Template-based question generation for 5 grammar topics.
Rule-based validation (exact + normalized match).
Rule-based diagnosis — no LLM calls.
"""

import uuid
import random
from typing import Optional, Callable

from app.tutor.core.subject_engine import (
    SubjectEngine,
    Question,
    ValidationResult,
    DiagnosisResult,
    RemediationPlan,
)
from app.tutor.subjects.english.knowledge import (
    TOPIC_TO_KNOWLEDGE,
    TOPIC_TO_OBJECTIVES,
)


# -- Validation helpers -------------------------------------------------------


def _normalize(s: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return " ".join(s.strip().lower().split())


def _exact_match(student: str, *acceptable: str) -> bool:
    """Check if student answer exactly or normalized-matches any acceptable answer."""
    if not student or not student.strip():
        return False
    for a in acceptable:
        if student.strip() == a:
            return True
        if _normalize(student) == _normalize(a):
            return True
    return False


# -- Constants for deterministic diagnosis ------------------------------------


KNOWN_VERB_STEMS: set[str] = {
    "go", "eat", "see", "take", "write", "drink", "sing", "begin", "give",
    "speak", "come", "run",
    "walk", "play", "read", "study", "live", "finish",
    "sleep", "bark", "want", "have", "do",
    "rain", "like", "watch", "work", "call", "start",
    "talk", "ask", "help", "move", "try", "use", "look", "need", "feel", "find",
    "know", "think", "tell", "show", "put", "let", "keep", "make", "get",
    "buy", "bring", "teach", "catch", "fly", "swim", "break", "fall", "grow",
    "throw", "ride", "drive",
}

IRREGULAR_VERB_FORMS: dict[str, dict[str, str]] = {
    "go":     {"past": "went",     "participle": "gone"},
    "eat":    {"past": "ate",      "participle": "eaten"},
    "see":    {"past": "saw",      "participle": "seen"},
    "take":   {"past": "took",     "participle": "taken"},
    "write":  {"past": "wrote",    "participle": "written"},
    "drink":  {"past": "drank",    "participle": "drunk"},
    "sing":   {"past": "sang",     "participle": "sung"},
    "begin":  {"past": "began",    "participle": "begun"},
    "give":   {"past": "gave",     "participle": "given"},
    "speak":  {"past": "spoke",    "participle": "spoken"},
    "come":   {"past": "came",     "participle": "come"},
    "run":    {"past": "ran",      "participle": "run"},
    "break":  {"past": "broke",    "participle": "broken"},
    "fall":   {"past": "fell",     "participle": "fallen"},
    "grow":   {"past": "grew",     "participle": "grown"},
    "throw":  {"past": "threw",    "participle": "thrown"},
    "ride":   {"past": "rode",     "participle": "ridden"},
    "drive":  {"past": "drove",    "participle": "driven"},
    "fly":    {"past": "flew",     "participle": "flown"},
    "swim":   {"past": "swam",     "participle": "swum"},
    "buy":    {"past": "bought",   "participle": "bought"},
    "bring":  {"past": "brought",  "participle": "brought"},
    "teach":  {"past": "taught",   "participle": "taught"},
    "catch":  {"past": "caught",   "participle": "caught"},
    "know":   {"past": "knew",     "participle": "known"},
    "make":   {"past": "made",     "participle": "made"},
    "tell":   {"past": "told",     "participle": "told"},
    "find":   {"past": "found",    "participle": "found"},
    "think":  {"past": "thought",  "participle": "thought"},
    "feel":   {"past": "felt",     "participle": "felt"},
    "keep":   {"past": "kept",     "participle": "kept"},
}

THIRD_PERSON_SINGULAR_PRONOUNS = {"he", "she", "it"}

SINGULAR_INDEFINITE_PRONOUNS = {
    "everyone", "everybody", "someone", "somebody",
    "each", "neither", "nobody", "anyone", "anybody",
}


# -- Diagnosis helpers --------------------------------------------------------


# Error patterns: (topic, pattern_check_fn) -> (error_type, diagnosis_label)

def _check_verb_tense_error(student: str, correct: str) -> Optional[tuple[str, str]]:
    """Check if the student used a bare infinitive instead of a tensed form."""
    s = _normalize(student)
    c = _normalize(correct)
    s_words = set(s.split())
    c_words = set(c.split())

    # Irregular verbs: base form instead of past/participle
    for base, past_forms in IRREGULAR_VERB_FORMS.items():
        pf_list = [past_forms["past"], past_forms["participle"]]
        if base in s_words and any(pf in c_words for pf in pf_list):
            return ("verb_tense_error", "base_form_instead_of_past")

    # Regular verbs: base form instead of -ed form
    for cw in c_words:
        if len(cw) < 4:
            continue
        # Regular -ed: played -> play
        if cw.endswith("ed") and not cw.endswith("eed"):
            base = cw[:-2]
            # Handle double consonant: stopped -> stop
            if len(base) >= 3 and base[-1] == base[-2] and base[-1] not in "aeiou":
                base_alt = base[:-1]
                if base_alt in s_words and base_alt in KNOWN_VERB_STEMS:
                    return ("verb_tense_error", "base_form_instead_of_past")
            if base in s_words and base in KNOWN_VERB_STEMS:
                return ("verb_tense_error", "base_form_instead_of_past")
        # y -> ied: studied -> study
        if cw.endswith("ied") and len(cw) > 4:
            base = cw[:-3] + "y"
            if base in s_words and base in KNOWN_VERB_STEMS:
                return ("verb_tense_error", "base_form_instead_of_past")

    return None


def _check_wrong_irregular_past(student: str, correct: str) -> Optional[tuple[str, str]]:
    """Detect overregularization, wrong participle, or missing continuous aspect."""
    s = _normalize(student)
    c = _normalize(correct)
    s_words = set(s.split())
    c_words = set(c.split())

    # 1. Overregularization: base + "ed" where verb is irregular
    for base, forms in IRREGULAR_VERB_FORMS.items():
        candidates = {base + "ed"}
        # e-drop: come -> comed, take -> taked
        if base.endswith("e") and len(base) > 2:
            candidates.add(base[:-1] + "ed")
        # double consonant: run -> runned, swim -> swimmed
        if base[-1] not in "aeiouwy":
            candidates.add(base + base[-1] + "ed")
        if candidates & s_words and forms["past"] in c_words:
            return ("verb_tense_error", "wrong_past_form")

    # 2. Wrong participle after auxiliary: "have went" instead of "have gone"
    for aux in ("have", "has", "had"):
        if aux in s_words and aux in c_words:
            for base, forms in IRREGULAR_VERB_FORMS.items():
                sp = forms["past"]
                pp = forms["participle"]
                if sp != pp and sp in s_words and pp in c_words:
                    return ("verb_tense_error", "wrong_past_form")

    # 3. Missing continuous: correct uses was/were/been + V-ing, student used simple past
    c_has_continuous = False
    c_words_list = c.split()
    for i, w in enumerate(c_words_list):
        if w in ("was", "were") and i + 1 < len(c_words_list):
            if c_words_list[i + 1].endswith("ing"):
                c_has_continuous = True
                break
        if w == "been" and i + 1 < len(c_words_list):
            if c_words_list[i + 1].endswith("ing"):
                c_has_continuous = True
                break

    if c_has_continuous:
        s_has_ing = any(w.endswith("ing") for w in s_words)
        s_has_simple_past = any(
            w.endswith("ed") or w in {f["past"] for f in IRREGULAR_VERB_FORMS.values()}
            for w in s_words
        )
        if not s_has_ing and s_has_simple_past:
            return ("verb_tense_error", "wrong_past_form")

    return None


def _check_sva_error(student: str, correct: str) -> Optional[tuple[str, str]]:
    """Check for missing third-person -s, auxiliary mismatch, or
    student-side third-person singular agreement errors."""
    s = _normalize(student)
    c = _normalize(correct)
    s_words = set(s.split())
    c_words = set(c.split())
    s_words_list = s.split()

    # 1. Correct answer has verb-s/-es, student used bare stem (generalized)
    for cw in c_words:
        if len(cw) < 3:
            continue
        if cw in KNOWN_VERB_STEMS:
            continue
        # -es ending: goes -> go, does -> do, watches -> watch
        if cw.endswith("es") and len(cw) > 3:
            base = cw[:-2]
            if base in s_words and base in KNOWN_VERB_STEMS:
                return ("subject_verb_agreement_error", "missing_third_person_s")
        # -s ending (but not -ss or -es): sleeps -> sleep, runs -> run
        if cw.endswith("s") and not cw.endswith("ss") and not cw.endswith("es"):
            base = cw[:-1]
            if base in s_words and base in KNOWN_VERB_STEMS:
                return ("subject_verb_agreement_error", "missing_third_person_s")
        # -ies ending: carries -> carry, tries -> try
        if cw.endswith("ies") and len(cw) > 4:
            base = cw[:-3] + "y"
            if base in s_words and base in KNOWN_VERB_STEMS:
                return ("subject_verb_agreement_error", "missing_third_person_s")

    # 2. Student-side SVA: he/she/it + bare verb in student's sentence
    for i, w in enumerate(s_words_list):
        w_lower = w.lower()
        if w_lower in THIRD_PERSON_SINGULAR_PRONOUNS and i + 1 < len(s_words_list):
            next_w = s_words_list[i + 1].rstrip(".,!?;:")
            if next_w in KNOWN_VERB_STEMS and next_w not in ("have", "has", "do", "does"):
                # Check student didn't already use inflected form
                if (next_w + "s") not in s_words and (next_w + "es") not in s_words:
                    return ("subject_verb_agreement_error", "missing_third_person_s")

    # 3. Auxiliary mismatch: "don't" with third-person subject (should be "doesn't")
    if "don't" in s_words and "doesn't" in c_words:
        for pron in THIRD_PERSON_SINGULAR_PRONOUNS:
            if pron in s_words:
                return ("subject_verb_agreement_error", "missing_third_person_s")
    # "do" with third-person subject (should be "does")
    if "do" in s_words and "does" in c_words:
        for i, w in enumerate(s_words_list):
            if w == "do" and i > 0:
                prev_w = s_words_list[i - 1].lower().rstrip(".,!?;:")
                if prev_w in THIRD_PERSON_SINGULAR_PRONOUNS:
                    return ("subject_verb_agreement_error", "missing_third_person_s")

    return None


def _check_plural_subject_error(student: str, correct: str) -> Optional[tuple[str, str]]:
    """Detect plural subject + singular verb, or singular indefinite
    pronoun + plural verb agreement errors."""
    s = _normalize(student)
    c = _normalize(correct)
    s_words = set(s.split())
    c_words = set(c.split())

    # is/are mismatch: student used singular "is", correct uses plural "are"
    if "is" in s_words and "are" in c_words:
        return ("subject_verb_agreement_error", "plural_subject_error")

    # was/were mismatch: student used singular "was", correct uses plural "were"
    if "was" in s_words and "were" in c_words:
        return ("subject_verb_agreement_error", "plural_subject_error")

    # has/have mismatch: student used singular "has", correct uses plural "have"
    if "has" in s_words and "have" in c_words:
        return ("subject_verb_agreement_error", "plural_subject_error")

    # have/has mismatch: student used plural "have", correct uses singular "has"
    if "have" in s_words and "has" in c_words:
        return ("subject_verb_agreement_error", "plural_subject_error")

    # Over-applied -s: student used verb-s for plural subject ("plays" -> "play").
    # Guard: skip when student uses "don't/doesn't" since the error is
    # likely auxiliary-related, not a plural-subject SVA error.
    for sw in s_words:
        if sw.endswith("s") and not sw.endswith("ss") and len(sw) > 3:
            base = sw[:-1]
            if base in c_words and base in KNOWN_VERB_STEMS:
                if "don't" in s_words or "doesn't" in s_words:
                    continue
                return ("subject_verb_agreement_error", "plural_subject_error")
        if sw.endswith("es") and len(sw) > 4:
            base = sw[:-2]
            if base in c_words and base in KNOWN_VERB_STEMS:
                if "don't" in s_words or "doesn't" in s_words:
                    continue
                return ("subject_verb_agreement_error", "plural_subject_error")

    # Singular indefinite pronoun + plural verb: "everyone have" -> "has"
    s_words_list = s.split()
    for i, w in enumerate(s_words_list):
        w_lower = w.lower()
        if w_lower in SINGULAR_INDEFINITE_PRONOUNS and i + 1 < len(s_words_list):
            next_w = s_words_list[i + 1].rstrip(".,!?;:")
            if next_w == "have" and "has" in c_words:
                return ("subject_verb_agreement_error", "plural_subject_error")
            if next_w == "are" and "is" in c_words:
                return ("subject_verb_agreement_error", "plural_subject_error")

    return None


def _check_article_error(student: str, correct: str) -> Optional[tuple[str, str]]:
    """Check for a/an confusion or missing article."""
    s = _normalize(student)
    c = _normalize(correct)
    # a vs an — handle both multi-word sentences and single-word answers
    c_has_a = " a " in c or c.startswith("a ") or c == "a"
    c_has_an = " an " in c or c.startswith("an ") or c == "an"
    s_has_a = " a " in s or s.startswith("a ") or s == "a"
    s_has_an = " an " in s or s.startswith("an ") or s == "an"
    if c_has_a and s_has_an:
        return ("article_error", "a_vs_an_confusion")
    if c_has_an and s_has_a:
        return ("article_error", "a_vs_an_confusion")
    # Missing article
    if (c_has_a or c_has_an or " the " in c or c.startswith("the ") or c == "the") and not any(
        art in s for art in [" a ", " an ", " the "]
    ) and s not in ("a", "an", "the"):
        return ("article_error", "missing_article")
    return None


def _check_preposition_error(student: str, correct: str) -> Optional[tuple[str, str]]:
    """Check for preposition substitution."""
    common_preps = {"at", "in", "on", "to", "for", "with", "from", "of", "by", "about"}
    s_words = set(_normalize(student).split())
    c_words = set(_normalize(correct).split())
    s_preps = s_words & common_preps
    c_preps = c_words & common_preps
    if s_preps and c_preps and s_preps != c_preps:
        return ("preposition_error", "wrong_preposition")
    return None


# Topic -> list of diagnosis check functions
TOPIC_DIAGNOSIS_RULES: dict[str, list[Callable]] = {
    "verb_tense": [_check_verb_tense_error, _check_wrong_irregular_past],
    "subject_verb_agreement": [_check_sva_error, _check_plural_subject_error],
    "article_usage": [_check_article_error],
    "preposition_usage": [_check_preposition_error],
    "sentence_correction": [
        _check_verb_tense_error,
        _check_wrong_irregular_past,
        _check_sva_error,
        _check_plural_subject_error,
        _check_article_error,
        _check_preposition_error,
    ],
}

# Error type -> remediation topics
REMEDIATION_MAP: dict[str, list[str]] = {
    "verb_tense_error": [
        "simple_past_tense", "past_tense_forms", "irregular_verbs",
        "past_continuous", "present_perfect",
    ],
    "subject_verb_agreement_error": [
        "subject_verb_agreement", "third_person_singular",
        "plural_subjects", "indefinite_pronouns",
    ],
    "article_error": ["definite_article", "indefinite_article", "a_vs_an"],
    "preposition_error": [
        "time_prepositions", "place_prepositions", "dependent_prepositions",
    ],
}


# -- EnglishQuestionEngine ----------------------------------------------------


class EnglishQuestionEngine(SubjectEngine):
    """Deterministic English grammar question generator.

    Usage:
        engine = EnglishQuestionEngine(seed=99)
        q = engine.generate("verb_tense", "easy")
    """

    _TOPICS = (
        "verb_tense",
        "subject_verb_agreement",
        "article_usage",
        "preposition_usage",
        "sentence_correction",
    )
    _DIFFICULTIES = ("easy", "medium", "hard")

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self._templates: dict[tuple[str, str], Callable[[], Question]] = {}
        self._register_all()

    # -- SubjectEngine interface ----------------------------------------------

    def generate(self, topic: str, difficulty: str) -> Question:
        if topic not in self._TOPICS:
            raise ValueError(f"Unknown topic: {topic}. Valid: {self._TOPICS}")
        if difficulty not in self._DIFFICULTIES:
            raise ValueError(f"Unknown difficulty: {difficulty}. Valid: {self._DIFFICULTIES}")
        q = self._templates[(topic, difficulty)]()
        q.subject = "english"
        q.knowledge_tags = TOPIC_TO_KNOWLEDGE.get(topic, [])
        q.learning_objectives = TOPIC_TO_OBJECTIVES.get(topic, [])
        return q

    def validate(self, student_answer: str, correct_answer: str) -> ValidationResult:
        # Split acceptable answers by "|||"
        acceptable = [a.strip() for a in correct_answer.split("|||")]
        ok = _exact_match(student_answer, *acceptable)
        return ValidationResult(is_correct=ok)

    def diagnose(
        self,
        student_answer: str,
        correct_answer: str,
        question: Question,
    ) -> DiagnosisResult:
        """Rule-based diagnosis — no LLM."""
        if student_answer is None:
            student_answer = ""

        rules = TOPIC_DIAGNOSIS_RULES.get(question.topic, [])
        error_types: list[str] = []
        diagnosis_labels: list[str] = []

        for check_fn in rules:
            result = check_fn(student_answer, correct_answer)
            if result is not None:
                et, dl = result
                if et not in error_types:
                    error_types.append(et)
                if dl not in diagnosis_labels:
                    diagnosis_labels.append(dl)

        return DiagnosisResult(
            error_types=error_types,
            diagnosis_labels=diagnosis_labels,
            confidence=0.85 if error_types else 1.0,
        )

    def plan_remediation(self, diagnosis: DiagnosisResult) -> RemediationPlan:
        """Map diagnosis labels to remediation topics and retrieval tags."""
        topics: list[str] = []
        tags: list[str] = []

        for et in diagnosis.error_types:
            remed = REMEDIATION_MAP.get(et, [])
            for r in remed:
                if r not in topics:
                    topics.append(r)
            for r in remed:
                if r not in tags:
                    tags.append(r)

        # Also include knowledge tags for retrieval
        for dl in diagnosis.diagnosis_labels:
            if dl not in tags:
                tags.append(dl)

        return RemediationPlan(recommended_topics=topics, retrieval_tags=tags)

    def get_knowledge_tags(self, topic: str) -> list[str]:
        return TOPIC_TO_KNOWLEDGE.get(topic, [])

    @property
    def topics(self) -> tuple[str, ...]:
        return self._TOPICS

    @property
    def difficulties(self) -> tuple[str, ...]:
        return self._DIFFICULTIES

    # -- template registration ------------------------------------------------

    def _register_all(self) -> None:
        self._templates[("verb_tense", "easy")] = self._verb_tense_easy
        self._templates[("verb_tense", "medium")] = self._verb_tense_medium
        self._templates[("verb_tense", "hard")] = self._verb_tense_hard
        self._templates[("subject_verb_agreement", "easy")] = self._sva_easy
        self._templates[("subject_verb_agreement", "medium")] = self._sva_medium
        self._templates[("subject_verb_agreement", "hard")] = self._sva_hard
        self._templates[("article_usage", "easy")] = self._article_easy
        self._templates[("article_usage", "medium")] = self._article_medium
        self._templates[("article_usage", "hard")] = self._article_hard
        self._templates[("preposition_usage", "easy")] = self._prep_easy
        self._templates[("preposition_usage", "medium")] = self._prep_medium
        self._templates[("preposition_usage", "hard")] = self._prep_hard
        self._templates[("sentence_correction", "easy")] = self._sent_easy
        self._templates[("sentence_correction", "medium")] = self._sent_medium
        self._templates[("sentence_correction", "hard")] = self._sent_hard

    # -- verb_tense templates -------------------------------------------------

    _VERB_TENSE_POOL = [
        # (cloze_sentence, answer, metadata)
        ("She ___ (go) to the store yesterday.", "went", {"verb": "go", "tense": "past"}),
        ("They ___ (eat) dinner at 7pm last night.", "ate", {"verb": "eat", "tense": "past"}),
        ("I ___ (see) that movie last week.", "saw", {"verb": "see", "tense": "past"}),
        ("He ___ (take) the bus to work this morning.", "took", {"verb": "take", "tense": "past"}),
        ("She ___ (write) a letter to her friend yesterday.", "wrote", {"verb": "write", "tense": "past"}),
        ("They ___ (drink) all the water after the game.", "drank", {"verb": "drink", "tense": "past"}),
        ("She ___ (sing) beautifully at the concert.", "sang", {"verb": "sing", "tense": "past"}),
        ("He ___ (begin) his homework after dinner.", "began", {"verb": "begin", "tense": "past"}),
        ("She ___ (give) him a book for his birthday.", "gave", {"verb": "give", "tense": "past"}),
        ("He ___ (speak) to the manager about the issue.", "spoke", {"verb": "speak", "tense": "past"}),
    ]

    def _verb_tense_easy(self) -> Question:
        template = self.rng.choice(self._VERB_TENSE_POOL)
        return Question(
            id=str(uuid.uuid4()),
            topic="verb_tense",
            difficulty="easy",
            question_text=f"Fill in the blank with the correct past tense form:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _verb_tense_medium(self) -> Question:
        sentences = [
            ("She ___ (walk) to school when it started raining.", "was walking",
             {"verb": "walk", "tense": "past_continuous"}),
            ("They ___ (play) football at 3pm yesterday.", "were playing",
             {"verb": "play", "tense": "past_continuous"}),
            ("I ___ (read) a book when she called.", "was reading",
             {"verb": "read", "tense": "past_continuous"}),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="verb_tense",
            difficulty="medium",
            question_text=f"Fill in the blank with the correct past continuous form:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _verb_tense_hard(self) -> Question:
        sentences = [
            ("By next month, she ___ (study) English for three years.",
             "will have been studying",
             {"verb": "study", "tense": "future_perfect_continuous"}),
            ("By the time you arrive, I ___ (finish) my homework.",
             "will have finished|||shall have finished",
             {"verb": "finish", "tense": "future_perfect"}),
            ("She ___ (live) here since 2010.",
             "has been living|||has lived",
             {"verb": "live", "tense": "present_perfect_continuous"}),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="verb_tense",
            difficulty="hard",
            question_text=f"Fill in the blank with the correct tense:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    # -- subject_verb_agreement templates -------------------------------------

    _SVA_EASY_POOL = [
        ("The cat ___ (sleep) on the sofa every afternoon.", "sleeps", {"subject": "cat", "number": "singular"}),
        ("The dogs ___ (bark) loudly at strangers.", "bark", {"subject": "dogs", "number": "plural"}),
        ("She ___ (run) three miles every morning.", "runs", {"subject": "she", "number": "singular"}),
        ("They ___ (eat) lunch at noon every day.", "eat", {"subject": "they", "number": "plural"}),
        ("My brother ___ (play) the guitar very well.", "plays", {"subject": "brother", "number": "singular"}),
        ("The birds ___ (sing) early in the morning.", "sing", {"subject": "birds", "number": "plural"}),
    ]

    def _sva_easy(self) -> Question:
        template = self.rng.choice(self._SVA_EASY_POOL)
        return Question(
            id=str(uuid.uuid4()),
            topic="subject_verb_agreement",
            difficulty="easy",
            question_text=f"Choose the correct verb form:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _sva_medium(self) -> Question:
        sentences = [
            ("Everyone ___ (want) to succeed in life.", "wants", {"subject": "everyone", "note": "indefinite_pronoun"}),
            ("The news ___ (be) surprising this morning.", "was|||is", {"subject": "news", "note": "uncountable"}),
            ("Neither the teacher nor the students ___ (be) happy about the test.", "were|||are",
             {"subject": "compound", "note": "nearest_noun_rule"}),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="subject_verb_agreement",
            difficulty="medium",
            question_text=f"Choose the correct verb form:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _sva_hard(self) -> Question:
        sentences = [
            ("The committee ___ (have) different opinions on the matter.",
             "has|||have",
             {"subject": "committee", "note": "collective_noun"}),
            ("Each of the students ___ (be) required to submit the form.",
             "is", {"subject": "each", "note": "each_of_construction"}),
            ("A number of problems ___ (be) identified during the audit.",
             "were|||have been", {"subject": "a_number_of", "note": "plural_sense"}),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="subject_verb_agreement",
            difficulty="hard",
            question_text=f"Choose the correct verb form:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    # -- article_usage templates ----------------------------------------------

    _ARTICLE_EASY_POOL = [
        ("I saw ___ elephant at the zoo.", "an", {"rule": "a_vs_an", "word": "elephant"}),
        ("She bought ___ book from the store.", "a", {"rule": "a_vs_an", "word": "book"}),
        ("He is ___ honest person.", "an", {"rule": "a_vs_an", "word": "honest"}),
        ("They live in ___ small apartment.", "a", {"rule": "a_vs_an", "word": "small"}),
        ("She ate ___ orange for breakfast.", "an", {"rule": "a_vs_an", "word": "orange"}),
        ("I need ___ umbrella because it's raining.", "an", {"rule": "a_vs_an", "word": "umbrella"}),
    ]

    def _article_easy(self) -> Question:
        template = self.rng.choice(self._ARTICLE_EASY_POOL)
        return Question(
            id=str(uuid.uuid4()),
            topic="article_usage",
            difficulty="easy",
            question_text=f"Fill in 'a' or 'an':\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _article_medium(self) -> Question:
        sentences = [
            ("___ sun rises in the east.", "The", {"rule": "definite_article", "context": "unique_entity"}),
            ("She is ___ best student in the class.", "the", {"rule": "definite_article", "context": "superlative"}),
            ("___ water in this bottle is cold.", "The", {"rule": "definite_article", "context": "specific_noun"}),
            ("I go to school by ___ bus every day.", "", {"rule": "zero_article", "context": "transport"}),
            ("She had ___ breakfast at 7am.", "", {"rule": "zero_article", "context": "meal"}),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="article_usage",
            difficulty="medium",
            question_text=f"Fill in 'a', 'an', 'the', or leave blank:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _article_hard(self) -> Question:
        sentences = [
            ("___ Mount Everest is the highest peak in ___ world.", "|||the", {"rule": "mixed"}),
            ("She plays ___ piano and is learning ___ guitar.", "the|||the",
             {"rule": "instrument"}),
            ("___ honesty is ___ best policy.", "|||the", {"rule": "abstract_noun"}),
        ]
        template = self.rng.choice(sentences)
        # Answer format: first_blank|||second_blank
        return Question(
            id=str(uuid.uuid4()),
            topic="article_usage",
            difficulty="hard",
            question_text=(
                f"Fill in each blank with 'a', 'an', 'the', or leave blank.\n"
                f"Answer format: first,second (e.g. 'the,a' or ',the' for blank first)\n\n"
                f"{template[0]}"
            ),
            answer=template[1],
            metadata=template[2],
        )

    # -- preposition_usage templates ------------------------------------------

    _PREP_EASY_POOL = [
        ("She is good ___ math.", "at", {"preposition": "at", "category": "adjective_dependent"}),
        ("The book is ___ the table.", "on", {"preposition": "on", "category": "place"}),
        ("He wakes up ___ 7am every day.", "at", {"preposition": "at", "category": "time"}),
        ("I go to school ___ foot.", "on", {"preposition": "on", "category": "transport"}),
        ("She is interested ___ learning Japanese.", "in", {"preposition": "in", "category": "adjective_dependent"}),
        ("The cat is hiding ___ the bed.", "under", {"preposition": "under", "category": "place"}),
    ]

    def _prep_easy(self) -> Question:
        template = self.rng.choice(self._PREP_EASY_POOL)
        return Question(
            id=str(uuid.uuid4()),
            topic="preposition_usage",
            difficulty="easy",
            question_text=f"Fill in the blank with the correct preposition:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _prep_medium(self) -> Question:
        sentences = [
            ("I have been waiting ___ over an hour.", "for", {"preposition": "for", "category": "duration"}),
            ("She is afraid ___ spiders.", "of", {"preposition": "of", "category": "adjective_dependent"}),
            ("He apologized ___ being late.", "for", {"preposition": "for", "category": "verb_dependent"}),
            ("We arrived ___ the airport on time.", "at", {"preposition": "at", "category": "place"}),
            ("She insisted ___ paying for dinner.", "on", {"preposition": "on", "category": "verb_dependent"}),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="preposition_usage",
            difficulty="medium",
            question_text=f"Fill in the blank with the correct preposition:\n\n{template[0]}",
            answer=template[1],
            metadata=template[2],
        )

    def _prep_hard(self) -> Question:
        sentences = [
            (
                "She is responsible ___ managing the team and reports ___ the CEO.",
                "for|||to",
                {"prepositions": ["for", "to"], "category": "multi_preposition"}
            ),
            (
                "He succeeded ___ passing the exam ___ his first attempt.",
                "in|||on",
                {"prepositions": ["in", "on"], "category": "multi_preposition"}
            ),
            (
                "I congratulated her ___ her promotion and wished her luck ___ her new role.",
                "on|||in",
                {"prepositions": ["on", "in"], "category": "multi_preposition"}
            ),
        ]
        template = self.rng.choice(sentences)
        return Question(
            id=str(uuid.uuid4()),
            topic="preposition_usage",
            difficulty="hard",
            question_text=(
                f"Fill in each blank with the correct preposition.\n"
                f"Answer format: first,second\n\n"
                f"{template[0]}"
            ),
            answer=template[1],
            metadata=template[2],
        )

    # -- sentence_correction templates ----------------------------------------

    _SENT_CORRECTION = [
        # (incorrect_sentence, correct_answer, error_focus, metadata)
        (
            "He go to school every day.",
            "He goes to school every day.",
            "subject_verb_agreement",
            {"error_type": "missing_third_person_s"}
        ),
        (
            "She don't like coffee.",
            "She doesn't like coffee.",
            "subject_verb_agreement",
            {"error_type": "wrong_auxiliary"}
        ),
        (
            "I have went to the store.",
            "I have gone to the store.",
            "verb_tense",
            {"error_type": "wrong_past_participle"}
        ),
        (
            "She has ate breakfast already.",
            "She has eaten breakfast already.",
            "verb_tense",
            {"error_type": "wrong_past_participle"}
        ),
        (
            "He is good at play football.",
            "He is good at playing football.",
            "preposition_usage",
            {"error_type": "gerund_after_preposition"}
        ),
        (
            "She is interested on learning Spanish.",
            "She is interested in learning Spanish.",
            "preposition_usage",
            {"error_type": "wrong_dependent_preposition"}
        ),
        (
            "I saw a elephant at the zoo.",
            "I saw an elephant at the zoo.",
            "article_usage",
            {"error_type": "a_vs_an"}
        ),
        (
            "Sun rises in east.",
            "The sun rises in the east.",
            "article_usage",
            {"error_type": "missing_articles"}
        ),
        (
            "The dogs barks loudly.",
            "The dogs bark loudly.",
            "subject_verb_agreement",
            {"error_type": "plural_subject_singular_verb"}
        ),
        (
            "She study English since 2010.",
            "She has been studying English since 2010.|||She has studied English since 2010.",
            "verb_tense",
            {"error_type": "missing_perfect_tense"}
        ),
    ]

    def _sent_easy(self) -> Question:
        # Pick SVA or article errors (more straightforward)
        easy_pool = [s for s in self._SENT_CORRECTION
                     if s[2] in ("subject_verb_agreement", "article_usage")]
        template = self.rng.choice(easy_pool)
        return Question(
            id=str(uuid.uuid4()),
            topic="sentence_correction",
            difficulty="easy",
            question_text=(
                f"Correct the error in this sentence:\n\n"
                f"\"{template[0]}\""
            ),
            answer=template[1],
            metadata={"incorrect": template[0], "error_focus": template[2], **template[3]},
        )

    def _sent_medium(self) -> Question:
        # Pick verb_tense or preposition errors
        med_pool = [s for s in self._SENT_CORRECTION
                    if s[2] in ("verb_tense", "preposition_usage")]
        template = self.rng.choice(med_pool)
        return Question(
            id=str(uuid.uuid4()),
            topic="sentence_correction",
            difficulty="medium",
            question_text=(
                f"Correct the error in this sentence:\n\n"
                f"\"{template[0]}\""
            ),
            answer=template[1],
            metadata={"incorrect": template[0], "error_focus": template[2], **template[3]},
        )

    def _sent_hard(self) -> Question:
        # Any type, including those with multiple acceptable corrections
        hard_pool = [s for s in self._SENT_CORRECTION if "|||" in s[1]]
        if not hard_pool:
            hard_pool = self._SENT_CORRECTION
        template = self.rng.choice(hard_pool)
        return Question(
            id=str(uuid.uuid4()),
            topic="sentence_correction",
            difficulty="hard",
            question_text=(
                f"Correct the error in this sentence:\n\n"
                f"\"{template[0]}\""
            ),
            answer=template[1],
            metadata={"incorrect": template[0], "error_focus": template[2], **template[3]},
        )
