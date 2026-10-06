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

# converts assessment type into its importance weight
def assessment_type_weight(assessment_type):
    weights = {
        "Learning Experience": 0.05,
        "Formative": 0.25,
        "Summative": 0.75,
        "Mock Exam": 1,
        "IA": 1
    }

    # Validation
    if assessment_type not in weights:
        raise ValueError("Invalid assessment type")

    return weights[assessment_type]

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

# prepares lists needed for weighted regression
def prepare_regression_data(assessments, total_topics,
                            latest_assessment_date, reference_date):

    times = []
    weights = []
    score_percentages = []

    for assessment in assessments:
        score_percentage = number(assessment["score_percentage"])

        if score_percentage < 0 or score_percentage > 100:
            raise ValueError("Invalid assessment percentage")

        time = days_between(reference_date, assessment["assessment_date"])

        weight = assessment_weight(
            assessment["assessment_type_importance_weight"],
            assessment["assessment_date"],
            latest_assessment_date,
            assessment["topics_covered"],
            total_topics
        )

        times.append(time)
        weights.append(weight)
        score_percentages.append(score_percentage)

    return times, weights, score_percentages


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

# Weighted Linear Regression (WLR), provides line info to make future predictions, and showcase trend
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

    # Calculates numerator = weighted covariance of time and score
    # and        denominator = weighted variance of time 
    for i in range(len(times)):
        time_difference = times[i] - mean_time
        score_percentage_difference = score_percentages[i] - mean_score_percentage

        numerator += weights[i] * time_difference * score_percentage_difference
        denominator += weights[i] * time_difference ** 2

    # When denominator=0 it means there is no variation in assessment times,
    # thus a regression slope cannot be calculated
    if denominator == 0:
        raise ValueError("Insufficient time variation to calculate a trend")

    # Closed-form weighted least-squares slope and intercept
    slope = numerator / denominator
    intercept = mean_score_percentage - slope * mean_time

    return slope, intercept, mean_score_percentage

# Estimates, based on mean and future prediction, the expected PG
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

# Calculates sum of all PGs to get an overall PG
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


# Advice

# validates inputs for minimum required percentage calculation
def validate_minimum_required(existing_assessments, proposed_assessment,
                              total_topics, target_grade, boundaries):

    if len(existing_assessments) == 0:
        raise ValueError("No existing assessments available")

    total_topics = integer(total_topics)
    target_grade = integer(target_grade)

    if total_topics <= 0:
        raise ValueError("Invalid total topics count")

    if target_grade < 1 or target_grade > 7:
        raise ValueError("Target grade must be between 1 and 7")

    if target_grade not in boundaries:
        raise ValueError("No boundary available for target grade")

    target_percentage = number(boundaries[target_grade])

    if target_percentage < 0 or target_percentage > 100:
        raise ValueError("Invalid target percentage")

    # finds earliest and latest existing assessment dates
    dates = []

    for assessment in existing_assessments:
        assessment_date = assessment["assessment_date"]

        # also validates the date
        days_between(assessment_date, assessment_date)
        dates.append(assessment_date)

    reference_date = min(dates)
    latest_assessment_date = max(dates)
    proposed_date = proposed_assessment["assessment_date"]

    # checks dates are in the correct order
    if days_between(latest_assessment_date, proposed_date) < 0:
        raise ValueError("Proposed assessment date is before latest assessment")

    return total_topics, target_percentage, reference_date, proposed_date


# calculates regression after adding a possible future score
def regression_with_proposed_score(times, weights, existing_scores,
                                   proposed_score):

    scores = existing_scores.copy()
    scores.append(proposed_score)

    return weighted_regression(times, scores, weights)


# finds points where future prediction reaches the 0 or 100 limits
def prediction_breakpoints(forecast_zero, forecast_hundred):

    breakpoints = [0, 100]
    forecast_change = forecast_hundred - forecast_zero

    if forecast_change != 0:
        for forecast_boundary in [0, 100]:
            fraction = (forecast_boundary - forecast_zero) / forecast_change

            if 0 < fraction < 1:
                breakpoints.append(fraction * 100)

    breakpoints.sort()

    return breakpoints


# calculates predicted percentage for a possible future score
def predicted_percentage_for_proposed_score(
        proposed_score,
        slope_zero, intercept_zero, mean_zero,
        slope_hundred, intercept_hundred, mean_hundred,
        prediction_time):

    fraction = proposed_score / 100

    slope = slope_zero + fraction * (slope_hundred - slope_zero)
    intercept = intercept_zero + fraction * (intercept_hundred - intercept_zero)
    mean_score_percentage = mean_zero + fraction * (mean_hundred - mean_zero)

    return estimate_predicted_grade_score_percentage(
        slope,
        intercept,
        prediction_time,
        mean_score_percentage
    )


# finds minimum percentage needed in a future assessment
# to reach the target predicted grade
def minimum_required_percentage(existing_assessments, proposed_assessment,
                                total_topics,
                                target_grade, boundaries):

    # validation
    total_topics, target_percentage, reference_date, proposed_date = validate_minimum_required(
        existing_assessments,
        proposed_assessment,
        total_topics,
        target_grade,
        boundaries
    )

    # prepares data from existing assessments
    times, weights, score_percentages = prepare_regression_data(
        existing_assessments,
        total_topics,
        proposed_date,
        reference_date
    )

    # adds the proposed assessment time and weight
    proposed_time = days_between(reference_date, proposed_date)

    proposed_weight = assessment_weight(
        proposed_assessment["assessment_type_importance_weight"],
        proposed_date,
        proposed_date,
        proposed_assessment["topics_covered"],
        total_topics
    )

    times.append(proposed_time)
    weights.append(proposed_weight)

    # finds regression values if proposed score is 0%
    slope_zero, intercept_zero, mean_zero = regression_with_proposed_score(
        times, weights, score_percentages, 0
    )

    # finds regression values if proposed score is 100%
    slope_hundred, intercept_hundred, mean_hundred = regression_with_proposed_score(
        times, weights, score_percentages, 100
    )

    # predicts up to 60 days after proposed date
    prediction_time = days_between(reference_date, proposed_date) + 60

    # estimates future regression values before the 0-100 limit is applied
    forecast_zero = slope_zero * prediction_time + intercept_zero
    forecast_hundred = slope_hundred * prediction_time + intercept_hundred

    breakpoints = prediction_breakpoints(forecast_zero, forecast_hundred)

    # calculates predicted percentage for each breakpoint
    predictions = []

    for proposed_score in breakpoints:
        predicted_percentage = predicted_percentage_for_proposed_score(
            proposed_score,
            slope_zero, intercept_zero, mean_zero,
            slope_hundred, intercept_hundred, mean_hundred,
            prediction_time
        )

        predictions.append(predicted_percentage)

    # target is reached even with a score of 0%
    if predictions[0] >= target_percentage:
        return 0

    # finds the interval in which the target is reached
    for i in range(len(breakpoints) - 1):
        if predictions[i + 1] >= target_percentage:
            prediction_change = predictions[i + 1] - predictions[i]

            if prediction_change == 0:
                continue

            fraction = (target_percentage - predictions[i]) / prediction_change

            required_percentage = breakpoints[i] + fraction * (
                breakpoints[i + 1] - breakpoints[i]
            )

            return required_percentage

    # target is not reached even with 100%
    return "Target can't be reached with this assessment"

# Calculates advice for future assessment
def calculate_advice(assessments, proposed_assessment, total_topics,
                    target_grade, boundaries):

    assessment_type = proposed_assessment["assessment_type"]
    assessment_date = proposed_assessment["assessment_date"]
    topics_covered_count = proposed_assessment["topics_covered_count"]

    # Validation
    total_topics = integer(total_topics)
    topics_covered_count = integer(topics_covered_count)

    if topics_covered_count < 0 or topics_covered_count > total_topics:
        raise ValueError("Invalid number of topics covered")

    type_weight = assessment_type_weight(assessment_type)

    # prepares existing assessment info
    existing_assessments = []

    for assessment in assessments:
        existing_assessments.append({
            "score_percentage": percentage(assessment["score"], assessment["maximum_score"]),
            "assessment_type_importance_weight": assessment_type_weight(assessment["assessment_type"]),
            "assessment_date": assessment["assessment_date"],
            "topics_covered": assessment["topics_covered_count"]
        })

    # prepares proposed assessment info
    proposed_assessment = {
        "assessment_type_importance_weight": type_weight,
        "assessment_date": assessment_date,
        "topics_covered": topics_covered_count
    }

    return minimum_required_percentage(existing_assessments,
                                        proposed_assessment,
                                        total_topics,
                                        target_grade,
                                        boundaries)


# Analysis (returns full info breakdown directly)

# *for a specific subject
def analyse_subject(assessments, total_topics, boundaries):

    # returns N/A values if no assessments
    if len(assessments) == 0:
        return {
            "mean": "N/A",
            "median": "N/A",
            "predicted_percentage": "N/A",
            "predicted_grade": "N/A",
            "uncertainty_range": "N/A",
            "slope": "N/A",
            "intercept": "N/A",
            "graph_dates": [],
            "graph_percentages": [],
            "regression_percentages": []
        }

    score_percentages = []
    regression_assessments = []
    dates = []

    # prepare assessment information
    for assessment in assessments:
        score_percentage = percentage(assessment["score"], assessment["maximum_score"])

        score_percentages.append(score_percentage)
        dates.append(assessment["assessment_date"])

        regression_assessments.append({
            "score_percentage": score_percentage,
            "assessment_type_importance_weight": assessment_type_weight(assessment["assessment_type"]),
            "assessment_date": assessment["assessment_date"],
            "topics_covered": assessment["topics_covered_count"]
        })

    # calculates stats
    subject_mean = mean(score_percentages)
    subject_median = median(score_percentages)

    reference_date = min(dates)
    latest_assessment_date = max(dates)

    # prepares values for WLR
    times, weights, score_percentages = prepare_regression_data(
        regression_assessments,
        total_topics,
        latest_assessment_date,
        reference_date
    )

    # prediction can't be calculated without time variation
    try:
        slope, intercept, mean_score_percentage = weighted_regression(times, score_percentages, weights)
    except ValueError:
        return {
            "mean": subject_mean,
            "median": subject_median,
            "predicted_percentage": "N/A",
            "predicted_grade": "N/A",
            "uncertainty_range": "N/A",
            "slope": "N/A",
            "intercept": "N/A",
            "graph_dates": [],
            "graph_percentages": [],
            "regression_percentages": []
        }

    # prepares trajectory graph data
    graph_dates, graph_percentages, regression_percentages = prepare_graph_data(regression_assessments,
                                                                                reference_date,
                                                                                slope,
                                                                                intercept)

    # time from reference to 60 days after latest assessment 
    prediction_time = days_between(reference_date, latest_assessment_date) + 60

    # calculates predicted percentage
    predicted_percentage = estimate_predicted_grade_score_percentage(
        slope,
        intercept,
        prediction_time,
        mean_score_percentage
    )

    # converts predicted percentage to IB grade
    predicted_grade = score_to_grade(predicted_percentage, 100, boundaries)

    # calculates uncertainty for predicted grade
    uncertainty_range = assumed_uncertainty_range(predicted_grade, 7)

    return {
        "mean": subject_mean,
        "median": subject_median,
        "predicted_percentage": predicted_percentage,
        "predicted_grade": predicted_grade,
        "uncertainty_range": uncertainty_range,
        "slope": slope,
        "intercept": intercept,
        "graph_dates": graph_dates,
        "graph_percentages": graph_percentages,
        "regression_percentages": regression_percentages
    }

# Calculates overall stats and pg
def analyse_overall(subject_means, predicted_grades):

    # calculates overall mean and median
    if len(subject_means) == 0:
        overall_mean = "N/A"
        overall_median = "N/A"
    else:
        overall_mean = mean(subject_means)
        overall_median = median(subject_means)

    # calculates overall pg
    overall_predicted = overall_pg(predicted_grades)

    uncertainty_range = assumed_uncertainty_range(overall_predicted, 42)

    return {
        "mean": overall_mean,
        "median": overall_median,
        "predicted_grade": overall_predicted,
        "uncertainty_range": uncertainty_range
    }

# prepares data to display subject trajectory graph
def prepare_graph_data(regression_assessments, reference_date,
                       slope, intercept):

    graph_dates = []
    graph_percentages = []
    regression_percentages = []

    for assessment in regression_assessments:
        assessment_time = days_between(reference_date, assessment["assessment_date"])

        regression_percentage = slope * assessment_time + intercept

        # limits percentage between 0 and 100
        regression_percentage = max(0, min(100, regression_percentage))

        graph_dates.append(assessment["assessment_date"])
        graph_percentages.append(assessment["score_percentage"])
        regression_percentages.append(regression_percentage)

    return graph_dates, graph_percentages, regression_percentages