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

# Returns the weight given to an assessment, then used in WLR
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

# Provides an uncertainty range for estimations
def assumed_uncertainty_range(score, maximum_score):
    # Validation
    if score == "N/A":
        return "N/A"    # No score available, thus no margin

    if maximum_score <= 0:
        raise ValueError("Maximum score must be greater than 0")

    if score < 0 or score > maximum_score:
        raise ValueError("Score not in range")

    # Deciding appropriate margin_rate
    rates = {7: 0.06, 
             42: 0.03}

    # Generating appropriate margins
    margin = rates.get(maximum_score, 0.05) * maximum_score
    # if not in dict, then margin_rate=0.05

    # Calculates range bounds
    lower_bound = max(0, score - margin)
    upper_bound = min(maximum_score, score + margin)

    return lower_bound, upper_bound

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

def weighted_regression(times, score_percentages, weights):
    # Validation
    if (len(times) != len(score_percentages)) or (len(times) != len(weights)):
        raise ValueError("Input lengths do not match")

    if len(times) == 0:
        raise ValueError("No assessments available")

    for weight in weights:
        if weight < 0:
            raise ValueError("Weights cannot be negative")

    total_weight = sum(weights)

    if total_weight == 0:
        raise ValueError("No positive weight")

    mean_time = 0
    mean_score_percentage = 0

    # Slope and intercept calculation with closed-form solution for weighted least squares
    for i in range(len(times)):
        mean_time += weights[i] * times[i]
        mean_score_percentage += weights[i] * score_percentages[i]

    mean_time = mean_time / total_weight

    # mean_score_percentage will be returned as used in other functions
    mean_score_percentage = mean_score_percentage / total_weight    

    numerator = 0
    denominator = 0

    for i in range(len(times)):
        time_difference = times[i] - mean_time
        score_percentage_difference = score_percentages[i] - mean_score_percentage

        numerator += weights[i] * time_difference * score_percentage_difference
        denominator += weights[i] * time_difference ** 2

    if denominator == 0:
        raise ValueError("Insufficient time variation to calculate a trend")

    slope = numerator / denominator
    intercept = mean_score_percentage - slope * mean_time

    return slope, intercept, mean_score_percentage

def estimate_predicted_grade_score_percentage(slope, intercept, prediction_time,
                                              mean_score_percentage):

    # weights, assigned to give more value to what has already been done
    FUTURE_WEIGHT = 0.35
    MEAN_WEIGHT = 0.65

    # Validation
    if mean_score_percentage < 0 or mean_score_percentage > 100:
        raise ValueError("Mean percentage must be between 0 and 100")

    # Calculate future score percentage estimate with regressed line information
    future_score_percentage = slope * prediction_time + intercept
    # prediction_time is the time at which the future score is estimated

    # Cap the future score estimate within percentage limits (0-100)
    future_score_percentage = max(0, min(100, future_score_percentage))
    
    # Calculation of the predicted score, through weighted average
    predicted_score_percentage = (
    FUTURE_WEIGHT * future_score_percentage + MEAN_WEIGHT * mean_score_percentage
    )

    return predicted_score_percentage


def overall_pg(subjects_predicted_scores):  # takes in list of individual PGs
    # Validation
    if len(subjects_predicted_scores) != 6:
        return "N/A"    # Used instead of raising an error
                        # Directly displays N/A to user

    for predicted in subjects_predicted_scores:
        if predicted == "N/A" or predicted == None:
            return "N/A"

    # Sum of individual predicted scores
    return sum(subjects_predicted_scores)
