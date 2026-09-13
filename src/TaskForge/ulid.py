import secrets
import time

# Crockford Base32 uses 32 characters to encode values
# This avoids characters that are easily confused e.g. "I", "L", "O"
CROCKFORD_BASE32 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def _encode(value: int, length: int) -> str:
    """
    Private method - not to be accessed
    Encode an int passed in the arg into a fixed-length Crockford Base32 string
    """
    result = []

# Each Base32 character represents 5 bits
# Extract 5 bits at a time until we have the required number of characters
    for _ in range(length):
        result.append(CROCKFORD_BASE32[value & 0x1F]) # FYI - '&' is a bitwise operator (not 'and')
        value >>= 5

    # The bits are extracted left to right, so reverse them to get the right representation
    return "".join(reversed(result))

def generate_ulid() -> str:
    """
    Function to generate a ULID
    Now packages exist instead of making my own function, but this is a learning project
    So I plan to build/understand and not import
    """
    # ULID is made by 48 bits of timestamp concat to 80 bits of randomness (both need to be endoded)
    timestamp = int(time.time()*100)
    randomness = secrets.randbits(80)

    # The timestamp is encoded into 10 Base32 characters
    timestamp_part = _encode(timestamp, 10)
    # The randomness is encoded into 16 Base32 characters
    random_part = _encode(randomness, 16)

    # 26 character ULID = 10 timestamp characters + 16 random characters
    return timestamp_part + random_part
    
