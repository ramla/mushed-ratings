from string import ascii_letters, digits

ALLOWED_CHARACTERS = ascii_letters + digits
REPORT_REWARD       = 15
SYMPTOM_REWARD      = 10
SYMPTOM_REWARD_MIN  = 2
SYMPTOM_REWARD_DIMINISHING_MULTIPLIER = 1
TESTING = True
ADVANCED_SEARCH_PARAMETERS = ["user_name",
                            #   "date", not yet implemented
                              "category_name",
                              "color_name",
                              "culinaryvalue_name",
                              "taste_ids",
                              "edibility",
                              "deleted"
                            ]
VALID_SEARCH_QUERY_VALUES = {
    "min_length": 3,
    "max_length": 20,
    "sorting": ["date", "id", "user", "category", "culinary", "edibility"]
    }
