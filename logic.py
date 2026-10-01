from math import isfinite
from datetime import date

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

# calculates days between two dates
def days_between(first_date, second_date):
    try:
        first_date = date.fromisoformat(first_date)
        second_date = date.fromisoformat(second_date)
    except (ValueError, TypeError):
        raise ValueError("Invalid date")

    return (second_date - first_date).days

# Converts scores to grades (1-7), based on minimum percentage in boundaries
def score_to_grade(score, maximum_score, boundaries):
    # convert score to percentage
    # includes validation
    score = percentage(score, maximum_score)

    # checks if percentage above the minimum boundary for a grade
    for grade in range(7,0,-1):
        if score >= boundaries[grade]:
            return grade

def assessment_weight(assessment_type_importance_weight, 
                           assessment_date, latest_assessment_date,
                           topics_covered, total_topics):

    HALF_LIFE_DAYS = 80     # used in exponential decay to indicate 
                            # after how many days the importance of a assessment with a certain date halves
    
    # Validation
    total_topics = integer(total_topics)
    assessment_type_importance_weight = number(assessment_type_importance_weight)
    topics_covered = integer(topics_covered)

    if total_topics <= 0:
        raise ValueError("Invalid total topics count")
    
    if assessment_type_importance_weight < 0 or assessment_type_importance_weight > 1:
        raise ValueError("Invalid assessment type value")

    if topics_covered < 0 or topics_covered > total_topics:
        raise ValueError("Invalid topic count")

    age_days = days_between(assessment_date, latest_assessment_date)

    if age_days < 0:
        raise ValueError("Assessment date is after the latest assessment")


    age_importance_weight = 2 ** (-age_days / HALF_LIFE_DAYS)
    topics_covered_importance_weight = topics_covered / total_topics

    weight = assessment_type_importance_weight * age_importance_weight * topics_covered_importance_weight

    return weight


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
