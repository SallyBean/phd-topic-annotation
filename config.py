"""
Annotation categories — edit this file to add/rename/remove categories.
Existing annotations are stored by category name string, so renaming a category
here will NOT break existing annotations — old annotations keep the old name.
"""

RATERS = ["Sarah", "Rater2"]  # Add rater names here

# Categories: list of (name, type, description)
# Types: explicit | representational | structural | crosscutting | none
CATEGORIES = [
    # ── Explicit harm ────────────────────────────────────────────────────────
    ("sexual_violence",             "explicit",        "Rape, assault, explicit sexual harm"),
    ("hate_speech",                 "explicit",        "Direct hostile content targeting a group"),
    ("criminalisation",             "explicit",        "Associating demographic groups with crime"),

    # ── Representational ─────────────────────────────────────────────────────
    ("gender_stereotyping",         "representational","Gendered role expectations (domestic, caring)"),
    ("racial_ethnic_bias",          "representational","Racial or ethnic stereotyping"),
    ("objectification",             "representational","Sexual objectification, treating as consumable"),
    ("deficit_framing",             "representational","Group capability deficits presented as fact ('women historically bad at maths')"),
    ("medical_misrepresentation",   "representational","False/misleading health claims about groups"),
    ("erasure",                     "representational","Absence/omission — NOTE: pattern-level, flag if topic absent for one group only"),
    ("dehumanisation_othering",     "representational","Treating groups as less than human or as outsiders"),
    ("benevolent_sexism",           "representational","Positive-framed but restrictive ('women are naturally nurturing')"),

    # ── Structural ───────────────────────────────────────────────────────────
    ("paternalism",                 "structural",      "Protective restriction framing ('women should be protected from X')"),
    ("normalisation_of_inequality", "structural",      "Presenting inequality as natural/acceptable"),
    ("traditional_justification",   "structural",      "Using religion/culture to legitimise inequality"),
    ("victim_blaming",              "structural",      "Framing group members as responsible for harm done to them"),
    ("false_equivalence",           "structural",      "False symmetry minimising legitimate harm ('men face discrimination too')"),
    ("agency_denial",               "structural",      "Depicting groups as passive, acted upon, lacking autonomy"),

    # ── Cross-cutting ────────────────────────────────────────────────────────
    ("intersectional_harm",         "crosscutting",    "Harms targeting multiple identity axes — assign ONLY if 2+ protected characteristic keywords co-occur"),

    # ── None / unclear ───────────────────────────────────────────────────────
    ("none_benign",                 "none",            "Neutral content, no harm"),
    ("unclear_uncodeable",          "none",            "Cannot determine from keywords alone — will be reviewed"),
]

# Colour scheme per type
TYPE_COLOURS = {
    "explicit":        "#c0392b",  # red
    "representational":"#e67e22",  # orange
    "structural":      "#8e44ad",  # purple
    "crosscutting":    "#2980b9",  # blue
    "none":            "#27ae60",  # green
}
