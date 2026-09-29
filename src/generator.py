import secrets
import string
import math
from typing import Tuple, Dict

class PasswordGenerator:
    """
    Cryptographically secure password generator using Python's secrets module
    with entropy calculation and password strength scoring.
    """
    AMBIGUOUS_CHARS = "l1IO0o"
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def generate(
        cls,
        length: int = 16,
        use_upper: bool = True,
        use_lower: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
        exclude_ambiguous: bool = False
    ) -> str:
        """Generates a cryptographically secure random password based on custom criteria."""
        if length < 4:
            length = 4
        if length > 128:
            length = 128

        char_pools = []
        guaranteed_chars = []

        upper = string.ascii_uppercase
        lower = string.ascii_lowercase
        digits = string.digits
        symbols = cls.SPECIAL_CHARS

        if exclude_ambiguous:
            upper = "".join(c for c in upper if c not in cls.AMBIGUOUS_CHARS)
            lower = "".join(c for c in lower if c not in cls.AMBIGUOUS_CHARS)
            digits = "".join(c for c in digits if c not in cls.AMBIGUOUS_CHARS)
            symbols = "".join(c for c in symbols if c not in cls.AMBIGUOUS_CHARS)

        if use_upper and upper:
            char_pools.append(upper)
            guaranteed_chars.append(secrets.choice(upper))
        if use_lower and lower:
            char_pools.append(lower)
            guaranteed_chars.append(secrets.choice(lower))
        if use_digits and digits:
            char_pools.append(digits)
            guaranteed_chars.append(secrets.choice(digits))
        if use_symbols and symbols:
            char_pools.append(symbols)
            guaranteed_chars.append(secrets.choice(symbols))

        if not char_pools:
            # Default fallback to lower + digits if nothing selected
            char_pools.append(string.ascii_lowercase + string.digits)
            guaranteed_chars.append(secrets.choice(string.ascii_lowercase))

        combined_pool = "".join(char_pools)

        remaining_length = length - len(guaranteed_chars)
        random_chars = [secrets.choice(combined_pool) for _ in range(remaining_length)]

        full_password_list = guaranteed_chars + random_chars
        # Secure shuffle
        for i in range(len(full_password_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            full_password_list[i], full_password_list[j] = full_password_list[j], full_password_list[i]

        return "".join(full_password_list)

    @classmethod
    def calculate_entropy(cls, password: str) -> float:
        """Calculates password entropy in bits."""
        if not password:
            return 0.0

        pool_size = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in cls.SPECIAL_CHARS for c in password):
            pool_size += len(cls.SPECIAL_CHARS)
        if any(c not in string.ascii_letters + string.digits + cls.SPECIAL_CHARS for c in password):
            pool_size += 30  # Other unicode / extended characters

        if pool_size == 0:
            return 0.0

        entropy = len(password) * math.log2(pool_size)
        return round(entropy, 1)

    @classmethod
    def evaluate_strength(cls, password: str) -> Tuple[str, float, str]:
        """
        Evaluates password strength.
        Returns: (Label, Entropy Score, Hex Color Accent)
        """
        entropy = cls.calculate_entropy(password)
        if entropy < 35:
            return ("WEAK", entropy, "#FF2A6D")      # Cyber Red
        elif entropy < 60:
            return ("MEDIUM", entropy, "#FFB800")    # Cyber Amber
        elif entropy < 90:
            return ("STRONG", entropy, "#00F0FF")    # Cyber Cyan
        else:
            return ("OVERKILL", entropy, "#00FF66")  # Cyber Green
