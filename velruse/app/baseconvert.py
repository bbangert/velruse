"""String functions to convert a string to another base"""

ALPHABET = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"


def base_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base_n_decoder(alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    char_value = dict(((c, v) for v, c in enumerate(alphabet)))

    def f(string):
        num = 0
        try:
            for char in string:
                num = num * base + char_value[char]
        except KeyError:
            raise ValueError('Unexpected character %r' % char)
        return num
    return f

base_decode = base_n_decoder()
