"""
English educational ontology — topic labels, prerequisites, knowledge tags,
and learning objectives for the English grammar subject module.
"""

SUBJECT_NAME = "english"

TOPIC_NAMES = {
    "verb_tense": "Verb Tense",
    "subject_verb_agreement": "Subject-Verb Agreement",
    "article_usage": "Article Usage",
    "preposition_usage": "Preposition Usage",
    "sentence_correction": "Sentence Correction",
}

DIFFICULTY_LABELS = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
}

# All English topics are independent — no prerequisite chain
PREREQUISITES = {
    "verb_tense": [],
    "subject_verb_agreement": [],
    "article_usage": [],
    "preposition_usage": [],
    "sentence_correction": [],
}

# Educational ontology — topic -> fine-grained knowledge tags
TOPIC_TO_KNOWLEDGE = {
    "verb_tense": [
        "verb_tense", "past_tense", "present_tense", "future_tense",
        "past_continuous", "present_perfect", "irregular_verbs",
    ],
    "subject_verb_agreement": [
        "subject_verb_agreement", "third_person_singular",
        "plural_subjects", "uncountable_nouns",
    ],
    "article_usage": [
        "article_usage", "definite_article", "indefinite_article",
        "zero_article", "a_vs_an",
    ],
    "preposition_usage": [
        "preposition_usage", "time_prepositions", "place_prepositions",
        "phrasal_prepositions", "dependent_prepositions",
    ],
    "sentence_correction": [
        "sentence_correction", "error_detection",
        "verb_tense", "subject_verb_agreement", "article_usage",
        "preposition_usage",
    ],
}

# Learning objectives per topic
TOPIC_TO_OBJECTIVES = {
    "verb_tense": [
        "Identify correct verb tense in context",
        "Apply past, present, and future tense forms correctly",
        "Recognize irregular verb forms",
    ],
    "subject_verb_agreement": [
        "Match subjects with correct verb forms",
        "Identify third-person singular subjects",
        "Handle collective and uncountable nouns",
    ],
    "article_usage": [
        "Choose between a, an, and the correctly",
        "Identify when zero article is required",
        "Apply article rules to common contexts",
    ],
    "preposition_usage": [
        "Select correct prepositions for time expressions",
        "Select correct prepositions for place expressions",
        "Use dependent prepositions with common verbs and adjectives",
    ],
    "sentence_correction": [
        "Detect grammatical errors in sentences",
        "Apply grammar rules to correct errors",
        "Integrate multiple grammar skills in context",
    ],
}

# Full knowledge tag taxonomy
KNOWLEDGE_TAGS = sorted(set(
    tag for tags in TOPIC_TO_KNOWLEDGE.values() for tag in tags
))
