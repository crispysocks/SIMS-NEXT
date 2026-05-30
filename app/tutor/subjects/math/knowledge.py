"""
Math educational ontology �?topic labels, prerequisites, knowledge tags,
and learning objectives for the math subject module.
"""

SUBJECT_NAME = "math"

TOPIC_NAMES = {
    "linear_equation": "一元一次方�?,
    "quadratic_equation": "一元二次方�?,
    "factoring": "因式分解",
    "derivative": "求导",
    "integral": "积分",
}

DIFFICULTY_LABELS = {
    "easy": "简�?,
    "medium": "中等",
    "hard": "困难",
}

PREREQUISITES = {
    "linear_equation": [],
    "quadratic_equation": ["linear_equation"],
    "factoring": ["linear_equation"],
    "derivative": ["linear_equation"],
    "integral": ["derivative"],
}

# Educational ontology �?topic -> fine-grained knowledge tags
TOPIC_TO_KNOWLEDGE = {
    "linear_equation": ["linear_equation", "solving", "algebraic_manipulation"],
    "quadratic_equation": ["quadratic_equation", "solving", "factoring", "roots"],
    "factoring": ["factoring", "algebraic_manipulation", "difference_of_squares"],
    "derivative": ["derivative", "power_rule", "chain_rule", "differentiation"],
    "integral": ["integral", "power_rule", "antiderivative", "integration"],
}

# Learning objectives per topic
TOPIC_TO_OBJECTIVES = {
    "linear_equation": [
        "Solve single-variable linear equations",
        "Apply algebraic manipulation to isolate unknowns",
    ],
    "quadratic_equation": [
        "Find roots of quadratic equations",
        "Recognize standard form ax^2+bx+c=0",
    ],
    "factoring": [
        "Factor polynomial expressions",
        "Recognize common factoring patterns like a^2-b^2",
    ],
    "derivative": [
        "Compute derivatives of polynomial functions",
        "Apply the power rule and chain rule",
    ],
    "integral": [
        "Compute indefinite integrals of polynomial functions",
        "Apply the power rule for integration",
    ],
}

# Full knowledge tag taxonomy
KNOWLEDGE_TAGS = sorted(set(
    tag for tags in TOPIC_TO_KNOWLEDGE.values() for tag in tags
))
