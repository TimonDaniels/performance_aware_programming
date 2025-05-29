
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
    0b110001: 'mov',
    0b101000: 'mov',
    0b100011: 'mov',
    0b100010: 'mov',
}


def decode_single_instruction(ins: bytearray):
    decoded_bytes = 2

    # Get field encodings
    op_code = (ins[0] & 0b11111100) >> 2
    d_code = (ins[0] & 0b00000010) >> 1
    assert d_code <= 1, "Invalid d_code, value is greater than 1"
    w_code = (ins[0] & 0b00000001)
    assert w_code <= 1, "Invalid w_code, value is greater than 1"
    mod_code = (ins[1] & 0b11000000) >> 6
    assert mod_code <= 3, "Invalid mod_code, value is greater than 3"
    reg_code = (ins[1] & 0b00111000) >> 3
    assert reg_code <= 7, "Invalid reg_code, value is greater than 7"
    r_m_code = (ins[1] & 0b00000111)
    assert r_m_code <= 7, "Invalid rm_code, value is greater than 7"
    print(f'Instruction: {ins[0]:08b} {ins[1]:08b}')

    # Decode instruction
    operation = OP_TABLE[op_code]
    reg = REG_TABLE[reg_code][w_code]
    if mod_code == 0b11:
        r_m = REG_TABLE[r_m_code][w_code]
    elif mod_code == 0b00:
        r_m = '[' + R_M_TABLE[r_m_code] + ']'
    elif mod_code == 0b01:
        r_m = '[' + R_M_TABLE[r_m_code] + f' + {ins[2]}' + ']'
        decoded_bytes += 1
    elif mod_code == 0b10:
        r_m = '[' + R_M_TABLE[r_m_code] + f' + {ins[2] | (ins[3] << 8)}' + ']'
        decoded_bytes += 2
    else:
        raise ValueError("Invalid mod_code, value is greater than 3")

    if d_code == 1:
        destination = reg
        source = r_m
    else:
        destination = r_m
        source = reg

    print(f'Assebmly: {operation} {destination}, {source}')

    return decoded_bytes


def decode(filename: str):
    # load binary instruction
    with open('./decoding_8086/' + filename, 'rb') as f:
        ins = f.read()
    ins = bytearray(ins)

    current_byte_idx = 0
    while current_byte_idx < len(ins):
        # Decode instruction
        num_bytes_decoded = decode_single_instruction(ins[current_byte_idx:])
        current_byte_idx += num_bytes_decoded


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python decode_ins.py <filename>")
        sys.exit(1)

    decode(sys.argv[1])