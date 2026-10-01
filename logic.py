from math import isfinite

# Validation 

# validates an entry as a finite number
def number(num):
    try:
        num = float(num)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Error: wrong type/value")
    if not isfinite(num):
        raise ValueError("Error: not finite")
    
    return num

# checks if a number is an integer
def integer(num):
    num = number(num)
    if not num.is_integer():
        raise ValueError("Error: not an integer")
    
    return int(num)

# Helpers

# converts raw scores into percentages
def percentage(score, maximum_score):
    # Validation
    score, maximum_score = number(score), number(maximum_score)
    if maximum_score <= 0:
        raise ValueError("maximum score must be greater than 0")
    if not (0 <= score <= maximum_score):
        raise ValueError("score must be within 0 and max_score")

    return 100 * (score / maximum_score)

def score_to_grade(score, maximum_score, boundaries):
    # Validation
    


    
# Statistics

# Mean of percentage scores
def mean(scores):   # must take list of scores in percentage form
    # Validation
    if len(scores) == 0:
        raise ValueError("No scores available")
    
    return sum(scores) / len(scores)

# Median of percentage scores
def median(scores): # must take list of scores in percentage form
    # Validation
    if len(scores) == 0:
            raise ValueError("No scores available")

    # Finds "center" after sorting the list
    ordered_scores = sorted(scores)
    n = len(ordered_scores)
    mid = n // 2

    if n % 2 == 1:
        return ordered_scores[mid] 

    # if the length is even (no central element)
    return (ordered_scores[mid - 1] + ordered_scores[mid]) / 2


# Prediction