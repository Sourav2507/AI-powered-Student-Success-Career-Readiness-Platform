import random
import string

def generate_otp():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=7))

