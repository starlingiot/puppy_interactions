HELP_MESSAGE = {
    "response_type": "ephemeral",
    "text": "This app helps you track you interactions with people (like Don talks "
            "about at PuPPy. It's simple - you rate your interactions with people as a "
            "positive (*+*) or negative (*-*), each time. Over time you can see who is "
            "most worth spending your time with! Here are the commands you might need.",
    "attachments": [
        {"text": "Create an interaction: `/interactions @will +`"},
        {"text": "Create a few: `/interactions @will + @don + Random Name -`"},
        {"text": "See them: `/interactions`"},
        {"text": "See them for this week: `/interactions 7`"},
        {"text": "See this year, categorized by person: `/interactions 365 person`"},
        {"text": "See this month, categorized by week: `/interactions 31 time`"},
        {"text": "See only positives: `/interactions +`"},
        {"text": "See only in the past 45 days: `/interactions 45 -`"},
        {"text": "Clear your logs: `/interactions clear` :warning: No confirmation!"},
        {"text": "See this message: `/interactions help`"},
    ]
}
