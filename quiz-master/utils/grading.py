"""Grading helpers: pass/fail, grade letters and performance messages."""

from .security import sanitize_text

PASS_PERCENTAGE = 60.0


def get_grade(percentage: float) -> str:
    """Map a percentage to a letter grade.

        90-100 -> A+
        80-89  -> A
        70-79  -> B
        60-69  -> C
        < 60   -> Fail
    """
    if percentage >= 90:
        return "A+"
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    return "Fail"


def is_pass(percentage: float) -> bool:
    return percentage >= PASS_PERCENTAGE


def get_message(percentage: float, grade: str) -> str:
    """Motivational message based on performance."""
    if percentage >= 90:
        return "Outstanding! You're a true Quiz Master. A flawless display of knowledge."
    if percentage >= 80:
        return "Excellent work! You clearly know your stuff. Keep climbing."
    if percentage >= 70:
        return "Great job! A solid performance. A little more practice and you'll be unstoppable."
    if percentage >= 60:
        return "Well done, you passed! Review the questions you missed and try the next level."
    return "Don't give up! Every expert was once a beginner. Retry this level and learn from the answers."


def safe_category(value: str) -> str:
    """Normalise a category name coming from the client."""
    return sanitize_text(value, max_len=60)
