"""Pick the 'ask the user to confirm' threshold from validation results (pure numpy)."""
import numpy as np


def choose_threshold(max_prob, correct, min_precision=0.95, min_coverage=0.70, default=0.60):
    """Smallest threshold t such that predictions with probability >= t are at least
    `min_precision` correct while still covering >= `min_coverage` of the images.
    Falls back to `default` if no threshold satisfies both."""
    max_prob = np.asarray(max_prob, dtype=float)
    correct = np.asarray(correct, dtype=bool)
    for t in np.arange(0.30, 0.96, 0.05):
        accepted = max_prob >= t
        if accepted.sum() == 0:
            break
        if correct[accepted].mean() >= min_precision and accepted.mean() >= min_coverage:
            return round(float(t), 2)
    return default
