from hashlib import sha256
import hmac

SECRET1 = bytes.fromhex('CHANGEME')
SECRET2 = bytes.fromhex('CHANGEME')
SECRET3 = bytes.fromhex('CHANGEME')

MUNGE_MAP = 'F1E2D3C4B5A69780'
NUMBER_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NUMBER_BASE = len(NUMBER_ALPHABET)
URL_PREFIX = 'HTTPS://TMGCP.TYB.JP/'

def _munge_hex(s):
    return ''.join(MUNGE_MAP[int(x, 16)] for x in s)

def make_hash(data):
    digest1 = hmac.new(SECRET1, data, sha256).digest()
    digest2 = hmac.new(SECRET2, digest1, sha256).hexdigest().upper()
    digest3 = hmac.new(SECRET3, _munge_hex(digest2).encode(), sha256).hexdigest().upper()
    return digest3

def make_secret_code(data):
    return URL_PREFIX + data + make_hash(data.encode())

def decode_number(encoded, base):
    return int(encoded, base)

def encode_number(value, base, min_width=0):
    if value < 0:
        raise ValueError('value cannot be negative')

    encoded = ''
    while value != 0:
        value, rem = divmod(value, base)
        encoded = NUMBER_ALPHABET[rem] + encoded

    pad_len = min_width - len(encoded)
    if pad_len < 0:
        pad_len = 0

    return '0' * pad_len + encoded

def decode_secret_code(code):
    DATA_LENGTH = 35

    if not code.startswith(URL_PREFIX):
        raise ValueError('Code does not start with correct prefix.')
    if len(code) != len(URL_PREFIX) + DATA_LENGTH + 64:  # prefix + data + hash
        raise ValueError('Code has incorrect length.')

    code_payload = code[len(URL_PREFIX) : len(URL_PREFIX) + DATA_LENGTH]
    code_hash = code[len(URL_PREFIX) + DATA_LENGTH :]
    if code_hash != make_hash(code_payload.encode()):
        raise ValueError('Code hash check failed.')

    decoded_data = {}
    offset = 0
    decoded_data['device_uid'] = code_payload[offset:offset + 6 + 6 + 7]  # generated from savedata checksum (+ tick), systick/vsync tick, random seed
    offset += 6 + 6 + 7
    decoded_data['rom_type'] = decode_number(code_payload[offset:offset + 2], NUMBER_BASE)
    offset += 2
    decoded_data['chara_id'] = decode_number(code_payload[offset:offset + 4], NUMBER_BASE)
    offset += 4
    decoded_data['eye_chara_id'] = decode_number(code_payload[offset:offset + 4], NUMBER_BASE)
    offset += 4
    decoded_data['color'] = decode_number(code_payload[offset:offset + 1], NUMBER_BASE)
    offset += 1
    decoded_data['planet_level'] = decode_number(code_payload[offset:offset + 1], NUMBER_BASE)
    offset += 1
    decoded_data['num_friends'] = decode_number(code_payload[offset:offset + 1], NUMBER_BASE)
    offset += 1
    decoded_data['random'] = decode_number(code_payload[offset:offset + 3], NUMBER_BASE)
    offset += 3

    return decoded_data

def _check_too_big(name, data, length):
    if len(data) > length:
        raise ValueError(f'Value for {name} is too big.')

def encode_secret_code(data):
    encoded = ''
    if len(data['device_uid']) != 6 + 6 + 7:
        raise ValueError('Invalid length for device_uid')
    encoded += data['device_uid']

    piece = encode_number(data['rom_type'], NUMBER_BASE, 2)
    _check_too_big('rom_type', piece, 2)
    encoded += piece

    piece = encode_number(data['chara_id'], NUMBER_BASE, 4)
    _check_too_big('chara_id', piece, 4)
    encoded += piece

    piece = encode_number(data['eye_chara_id'], NUMBER_BASE, 4)
    _check_too_big('eye_chara_id', piece, 4)
    encoded += piece

    piece = encode_number(data['color'], NUMBER_BASE, 1)
    _check_too_big('color', piece, 1)
    encoded += piece

    piece = encode_number(data['planet_level'], NUMBER_BASE, 1)
    _check_too_big('planet_level', piece, 1)
    encoded += piece

    piece = encode_number(data['num_friends'], NUMBER_BASE, 1)
    _check_too_big('num_friends', piece, 1)
    encoded += piece

    piece = encode_number(data['random'], NUMBER_BASE, 3)
    _check_too_big('random', piece, 3)
    encoded += piece

    return make_secret_code(encoded)
