from enum import Enum
from dataclasses import dataclass

DECODED_BYTES = 0
INSTUCTION_SPACING = 35

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
    0b000: 'add',
    0b000001: 'add',
    0b111: 'cmp',
    0b001110: 'cmp',
    0b001111: 'cmp',
    0b101: 'sub',
    0b001011: 'sub',
    0b001010: 'sub',
}


@dataclass(frozen=True)
class FieldEncoding:
    op: bytes = None
    d: bytes = None
    w: bytes = None
    mod: bytes = None
    reg: bytes = None
    r_m: bytes = None
    s: bytes = None


@dataclass(frozen=True)
class AsmInstruction:
    operation: str
    destination: str
    source: str
    byte_size: str


class DecodePattern(Enum):
    DEFAULT = 0
    I2REG = 1
    I2R_M = 2
    I2ACC = 3


def decode_field_encoding(ins: bytearray, pattern: DecodePattern) -> FieldEncoding:
    decoded_bytes = 0

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
        decoded_bytes += 2

    elif pattern == DecodePattern.I2REG:
        op_code = (ins[0] & 0b11110000) >> 4
        w_code = (ins[0] & 0b00001000) >> 3
        reg_code = (ins[0] & 0b00000111)
        field_encoding = FieldEncoding(
            op=op_code,
            w=w_code,
            reg=reg_code,
        )
        decoded_bytes += 1

    elif pattern == DecodePattern.I2R_M:
        op_code = (ins[0] & 0b11111100) >> 2
        if op_code == 0b110001:
            s_code = 0
        elif op_code == 0b100000:
            op_code = (ins[1] & 0b00111000) >> 3
            s_code = (ins[0] & 0b00000010) >> 1
        w_code = (ins[0] & 0b00000001)
        mod_code = (ins[1] & 0b11000000) >> 6
        r_m_code = (ins[1] & 0b00000111)
        field_encoding = FieldEncoding(
            op=op_code,
            d=s_code,
            w=w_code,
            r_m=r_m_code,
            mod=mod_code
        )
        decoded_bytes += 2

    elif pattern == DecodePattern.I2ACC:
        op_code = (ins[0] & 0b11111100) >> 2
        w_code = (ins[0] & 0b00000001)
        field_encoding = FieldEncoding(op=op_code, w=w_code)
        decoded_bytes += 1
    
    assert decoded_bytes > 0, "Decoded bytes must be greater than 0"

    return field_encoding, decoded_bytes


def get_decode_pattern(ins: bytearray):
    op_code = (ins[0] & 0b11111100) >> 2
    assert op_code < 0b111111, "Invalid op_code, value is greater than 63"

    if (op_code >> 2) == 0b1011:
        pattern = DecodePattern.I2REG
    elif op_code == 0b110001 or (op_code >> 3) == 0b100:
        pattern = DecodePattern.I2R_M
    elif (op_code == 0b000001) or (op_code == 0b001111) or (op_code == 0b001011):
        pattern = DecodePattern.I2ACC
    else:
        pattern = DecodePattern.DEFAULT
    return pattern
        

def gen_assembly(asm_instruction: AsmInstruction) -> str:
    """
    Generate assembly code from an AsmInstruction object.
    """
    if asm_instruction.byte_size:
        return f"{asm_instruction.operation} {asm_instruction.byte_size} {asm_instruction.destination}, {asm_instruction.source}"
    else:
        return f"{asm_instruction.operation} {asm_instruction.destination}, {asm_instruction.source}"
    
    
def decode_single_instruction(ins: bytearray):
    byte_size = None
    try:
        pattern = get_decode_pattern(ins)
        encoding, decoded_bytes = decode_field_encoding(ins, pattern)

        # Decode instruction
        if pattern == DecodePattern.DEFAULT:
            operation = OP_TABLE[encoding.op]
            reg = REG_TABLE[encoding.reg][encoding.w]
            if encoding.mod == 0b11:
                r_m = REG_TABLE[encoding.r_m][encoding.w]
            elif encoding.mod == 0b00:
                r_m = '[' + R_M_TABLE[encoding.r_m] + ']'
            elif encoding.mod == 0b01:
                r_m = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2]}' + ']'
                decoded_bytes += 1
            elif encoding.mod == 0b10:
                r_m = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2] | (ins[3] << 8)}' + ']'
                decoded_bytes += 2
            else:
                raise ValueError("Invalid mod_code, value is greater than 3")
            if encoding.d == 1:
                destination = reg
                source = r_m
            else:
                destination = r_m
                source = reg
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                source=source,
                byte_size=byte_size
            )

        elif pattern == DecodePattern.I2REG:
            operation = OP_TABLE[encoding.op]
            destination = REG_TABLE[encoding.reg][encoding.w]
            if encoding.w == 0:
                source = f'{ins[1]}'
                decoded_bytes += 1
            else:
                source = f'{ins[1] | (ins[2] << 8)}'
                decoded_bytes += 2
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                source=source,
                byte_size=byte_size
            )

        elif pattern == DecodePattern.I2R_M:
            operation = OP_TABLE[encoding.op]
            if encoding.mod == 0b11:
                destination = REG_TABLE[encoding.r_m][encoding.w]
            if encoding.mod == 0b00:
                byte_size = 'word' if encoding.w else 'byte'
                if encoding.r_m == 0b110:
                    destination = f'[{ins[2] | (ins[3] << 8)}]'
                    decoded_bytes += 2
                else:
                    destination = '[' + R_M_TABLE[encoding.r_m] + ']'
            elif encoding.mod == 0b01:
                byte_size = 'word' if encoding.w else 'byte'
                destination = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2]}' + ']'
                decoded_bytes += 1
            elif encoding.mod == 0b10:
                byte_size = 'word' if encoding.w else 'byte'
                destination = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2] | (ins[3] << 8)}' + ']'
                decoded_bytes += 2
            if encoding.s == 0 and encoding.w == 1:
                source = f'{ins[decoded_bytes] | (ins[decoded_bytes + 1] << 8)}'
                decoded_bytes += 2 
            else:
                source = f'{ins[decoded_bytes]}'
                decoded_bytes += 1
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                source=source,
                byte_size=byte_size
            )
        
        elif pattern == DecodePattern.I2ACC:
            operation = OP_TABLE[encoding.op]
            if encoding.w == 0:
                destination = 'al'
                source = f'{ins[decoded_bytes]}'
                decoded_bytes += 1
            else:
                destination = 'ax'
                source = f'{ins[decoded_bytes] | (ins[decoded_bytes + 1] << 8)}'
                decoded_bytes += 2
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                source=source,
                byte_size=byte_size
            )

        assert isinstance(operation, str), "Operation must be a string"
        
        machine_code_str = ' '.join([f"{ins[i]:08b}" for i in range(decoded_bytes)])
        asm_instruction_str = gen_assembly(asm_instruction)
        print("{:<{width}} | {}".format(asm_instruction_str, machine_code_str, width=INSTUCTION_SPACING))    
        return decoded_bytes

    except Exception as e:
        machine_code_str = ' '.join([f"{ins[i]:08b}" for i in range(decoded_bytes)])
        raise ValueError(f"Error decoding bytes: {machine_code_str} \n With error: {e}") from e


def decode(filename: str):
    global DECODED_BYTES

    # load binary instruction
    with open('./decoding_8086/' + filename, 'rb') as f:
        ins = f.read()
    ins = bytearray(ins)

    print(f"{'Assembly Instruction':<{INSTUCTION_SPACING}} | Machine Code")
    while DECODED_BYTES < len(ins):
        DECODED_BYTES += decode_single_instruction(ins[DECODED_BYTES:])


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python decode_ins.py <filename>")
        sys.exit(1)

    decode(sys.argv[1])