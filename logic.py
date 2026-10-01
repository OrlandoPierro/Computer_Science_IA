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
# Statistics
# Prediction