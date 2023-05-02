import re

class State:
    def __init__(self, runs, keys):
        self.old_matches: list[str] = []
        self.matches: list[str] = []
        self.runs = runs
        self.keys = keys
        self.old_text = ""
        self.text = ""


    def get_matches(self, text):
        self.old_text = self.text
        self.text = text
        return list(filter(lambda x: re.match(text, x), self.keys))

    def update_matches(self, text):
        self.old_matches = self.matches.copy()
        self.matches = self.get_matches(text)
        return self.new_matches()

    def new_matches(self):
        return self.old_matches != self.matches
