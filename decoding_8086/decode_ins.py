from enum import Enum
from dataclasses import dataclass

DECODED_BYTES = 0

REG_TABLE = [
    ['al', 'ax'],
    ['cl', 'cx'],
    ['dl', 'dx'],
    ['bl', 'bx'],
    ['ah', 'sp'],
    ['ch', 'bp'],
    ['dh', 'si'],
    ['bh', 'di'],
]

R_M_TABLE = [
    'bx + si',
    'bx + di',
    'bp + si',
    'bp + di',
    'si',
    'di',
    'bp',
    'bx',
]

OP_TABLE = {
    0b1011: 'mov',
    0b110001: 'mov',
    0b101000: 'mov',
    0b100011: 'mov',
    0b100010: 'mov',
}


@dataclass(frozen=True)
class FieldEncoding:
    op: bytes = None
    d: bytes = None
    w: bytes = None
    mod: bytes = None
    reg: bytes = None
    r_m: bytes = None


class DecodePattern(Enum):
    DEFAULT = 0
    I2R_M = 1


def decode_field_encoding(ins: bytearray, pattern: DecodePattern) -> FieldEncoding:
    global DECODED_BYTES

    if pattern == DecodePattern.DEFAULT:
        op_code = (ins[0] & 0b11111100) >> 2
        d_code = (ins[0] & 0b00000010) >> 1
        w_code = (ins[0] & 0b00000001)
        mod_code = (ins[1] & 0b11000000) >> 6
        reg_code = (ins[1] & 0b00111000) >> 3
        r_m_code = (ins[1] & 0b00000111)
        field_encoding =  FieldEncoding(
            op=op_code,
            d=d_code,
            w=w_code,
            mod=mod_code,
            reg=reg_code,
            r_m=r_m_code
        )
        DECODED_BYTES += 2
    elif pattern == DecodePattern.I2R_M:
        op_code = (ins[0] & 0b11110000) >> 4
        w_code = (ins[0] & 0b00001000) >> 3
        reg_code = (ins[0] & 0b00000111)
        field_encoding = FieldEncoding(
            op=op_code,
            w=w_code,
            reg=reg_code,
        )
        DECODED_BYTES += 1

    return field_encoding


def get_decode_pattern(ins: bytearray):
    op_code = (ins[0] & 0b11111100) >> 2
    assert op_code < 0b111111, "Invalid op_code, value is greater than 63"

    if (op_code >> 2) == 0b1011:
        pattern = DecodePattern.I2R_M
    else:
        pattern = DecodePattern.DEFAULT
    return pattern
        

def decode_single_instruction(ins: bytearray):
    global DECODED_BYTES

    start_bytes = DECODED_BYTES
    try:
        pattern = get_decode_pattern(ins)
        encoding = decode_field_encoding(ins, pattern)

        # Decode instruction
        operation = OP_TABLE[encoding.op]
        if pattern == DecodePattern.DEFAULT:
            reg = REG_TABLE[encoding.reg][encoding.w]
            if encoding.mod == 0b11:
                r_m = REG_TABLE[encoding.r_m][encoding.w]
            elif encoding.mod == 0b00:
                r_m = '[' + R_M_TABLE[encoding.r_m] + ']'
            elif encoding.mod == 0b01:
                r_m = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2]}' + ']'
                DECODED_BYTES += 1
            elif encoding.mod == 0b10:
                r_m = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2] | (ins[3] << 8)}' + ']'
                DECODED_BYTES += 2
            else:
                raise ValueError("Invalid mod_code, value is greater than 3")
            if encoding.d == 1:
                destination = reg
                source = r_m
            else:
                destination = r_m
                source = reg

        elif pattern == DecodePattern.I2R_M:
            destination = REG_TABLE[encoding.reg][encoding.w]
            if encoding.w == 0:
                source = f'{ins[1]}'
                DECODED_BYTES += 1
            else:
                source = f'{ins[1] | (ins[2] << 8)}'
                DECODED_BYTES += 2
        
        machine_code = ' '.join([f"{ins[i]:08b}" for i in range(DECODED_BYTES - start_bytes)])
        print(f'Machine code: {machine_code}')
        print(f'Assebmly: {operation} {destination}, {source}')

    except Exception as e:
        print(f"Raw bytes: {ins[0]:08b} {ins[1]:08b}")
        raise f"Error decoding bytes: {ins[0]:08b} {ins[1]:08b} \n With error: {e}"


def decode(filename: str):
    # load binary instruction
    with open('./decoding_8086/' + filename, 'rb') as f:
        ins = f.read()
    ins = bytearray(ins)

    while DECODED_BYTES < len(ins):
        decode_single_instruction(ins[DECODED_BYTES:])


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python decode_ins.py <filename>")
        sys.exit(1)

    decode(sys.argv[1])