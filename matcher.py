
# matcher.py
import difflib
import json
import os
import re
from typing import Tuple

HERE = os.path.dirname(__file__)

class Matcher:
    def __init__(self, kb_path: str = "kb.json", cutoff: float = 0.55):
        """
        kb_path: path to kb.json (relative to this file)
        cutoff: default minimum similarity (0..1) considered a match
        """
        self.kb_path = os.path.join(HERE, kb_path)
        self.cutoff = cutoff
        self._load_kb()

    def _preprocess(self, s: str) -> str:
        s = (s or "").lower().strip()
        # remove punctuation (keep letters+digits+spaces)
        s = re.sub(r"[^a-z0-9\s]", "", s)
        s = re.sub(r"\s+", " ", s)
        return s

    def _load_kb(self):
        with open(self.kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)
        # store original questions and preprocessed versions
        self.questions = [item.get("question", "") for item in self.kb]
        self._questions_proc = [self._preprocess(q) for q in self.questions]

    def reload_kb(self):
        """Call this if kb.json is updated while server is running."""
        self._load_kb()

    def find_best(self, query: str) -> Tuple[str, str, float]:
        """
        Returns: (answer, matched_question, score)
        If no match above cutoff, answer will be a generic fallback and score the best found (may be low).
        """
        q = self._preprocess(query)
        best_idx = -1
        best_score = 0.0

        for i, q_proc in enumerate(self._questions_proc):
            score = difflib.SequenceMatcher(None, q, q_proc).ratio()
            if score > best_score:
                best_score = score
                best_idx = i

        if best_idx != -1 and best_score >= self.cutoff:
            return (self.kb[best_idx]["answer"], self.questions[best_idx], best_score)

        # no confident match
        return ("", self.questions[best_idx] if best_idx != -1 else "", best_score)

    def get_answer_with_score(self, query: str) -> Tuple[str, str, float]:
        """
        Convenience wrapper for callers.
        Returns (answer_text, matched_question_text, score).
        If a confident answer is not found (score < cutoff) it returns ("", matched_question, score)
        so the caller can decide fallback or clarification.
        """
        answer, matched_q, score = self.find_best(query)
        return (answer, matched_q, score)


if __name__ == "__main__":
    # quick local test
    m = Matcher()
    while True:
        q = input("Enter question (or 'q' to quit): ").strip()
        if q.lower() in ("q", "quit", "exit"):
            break
        ans, matched, score = m.get_answer_with_score(q)
        if ans:
            print(f"Answer: {ans!s}\nMatched question: {matched!s}\nScore: {score:.3f}")
        else:
            print(f"No confident match (best match: '{matched}' score={score:.3f}).")
