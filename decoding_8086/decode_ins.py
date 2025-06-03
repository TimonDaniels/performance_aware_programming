from enum import Enum
from typing import Tuple

from helpers import FieldEncoding, AsmInstruction, add_bytearrays, format_bytearray, gen_assembly, is_bit_set, set_bit
from tables import FLAGS_REG, FULL_REG_STORAGE, OP_TABLE, REG_TABLE, REG_STORAGE, R_M_TABLE, R_M_STORAGE, IP_REG


INSTUCTION_SPACING = 35


class DecodePattern(Enum):
    DEFAULT = 0
    I2REG = 1
    I2R_M = 2
    I2ACC = 3
    I2REGMOV = 4
    JUMP = 5


def get_decode_pattern(ins: bytearray):
    op_code = (ins[0] & 0b11111100) >> 2
    assert op_code < 0b111111, "Invalid op_code, value is greater than 63"

    if (op_code >> 2) == 0b1011:
        pattern = DecodePattern.I2REGMOV
    elif (op_code == 0b100010):
        pattern = DecodePattern.DEFAULT
    elif (op_code == 0b110001) or (op_code == 0b100000):
        pattern = DecodePattern.I2R_M
    elif (op_code == 0b000001) or (op_code == 0b001111) or (op_code == 0b001011):
        pattern = DecodePattern.I2ACC
    elif (ins[0] == 0b01110101):
        pattern = DecodePattern.JUMP
    else:
        pattern = DecodePattern.DEFAULT
    return pattern


def decode_field_encoding(ins: bytearray, pattern: DecodePattern) -> Tuple[FieldEncoding, int]:
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

    elif pattern == DecodePattern.I2REGMOV:
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
    
    elif pattern == DecodePattern.JUMP:
        op_code = ins[0]
        decoded_bytes += 1
    
    assert decoded_bytes > 0, "Decoded bytes must be greater than 0"

    return field_encoding, decoded_bytes

    
def decode_instruction(encoding: FieldEncoding, pattern: DecodePattern, ins: bytearray):
    byte_size = None
    decoded_bytes = 0
    try:
        if pattern == DecodePattern.DEFAULT:
            operation = OP_TABLE[encoding.op]
            reg = REG_TABLE[encoding.reg][encoding.w]
            reg_value = REG_STORAGE[encoding.w][encoding.reg]
            if encoding.mod == 0b11:
                r_m = REG_TABLE[encoding.r_m][encoding.w]
                r_m_value = REG_STORAGE[encoding.w][encoding.r_m]
            elif encoding.mod == 0b00:
                r_m = '[' + R_M_TABLE[encoding.r_m] + ']'
                r_m_value = R_M_STORAGE[encoding.r_m]
            elif encoding.mod == 0b01:
                r_m = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2]}' + ']'
                r_m_value = add_bytearrays(R_M_STORAGE[encoding.r_m] + bytearray(ins[2]))
                decoded_bytes += 1
            elif encoding.mod == 0b10:
                r_m = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2] | (ins[3] << 8)}' + ']'
                r_m_value = add_bytearrays(R_M_STORAGE[encoding.r_m] + bytearray([ins[2], ins[3]]))
                decoded_bytes += 2
            else:
                raise ValueError("Invalid mod_code, value is greater than 3")
            if encoding.d == 1:
                destination = reg
                dest_value = reg_value
                source = r_m
                src_value = r_m_value
            else:
                destination = r_m
                dest_value = r_m_value
                source = reg
                src_value = reg_value
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                dest_value=dest_value,
                source=source,
                src_value=src_value,
                byte_size=byte_size
            )

        elif pattern == DecodePattern.I2REGMOV:
            operation = 'mov' 
            destination = REG_TABLE[encoding.reg][encoding.w]
            dest_value = REG_STORAGE[encoding.w][encoding.reg]
            if encoding.w == 0:
                source = f'{ins[1]}'
                src_value = bytearray([ins[1]])
                decoded_bytes += 1
            else:
                source = f'{ins[1] | (ins[2] << 8)}'
                src_value = bytearray([ins[1], ins[2]])
                decoded_bytes += 2
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                dest_value=dest_value,
                source=source,
                src_value=src_value,
                byte_size=byte_size
            )

        elif pattern == DecodePattern.I2R_M:
            operation = OP_TABLE[encoding.op]
            if encoding.mod == 0b11:
                destination = REG_TABLE[encoding.r_m][encoding.w]
                dest_value = REG_STORAGE[encoding.w][encoding.r_m]
            if encoding.mod == 0b00:
                byte_size = 'word' if encoding.w else 'byte'
                if encoding.r_m == 0b110:
                    destination = f'[{ins[2] | (ins[3] << 8)}]'
                    dest_value = bytearray([ins[2], ins[3]])
                    decoded_bytes += 2
                else:
                    destination = '[' + R_M_TABLE[encoding.r_m] + ']'
                    dest_value = R_M_STORAGE[encoding.r_m]
            elif encoding.mod == 0b01:
                byte_size = 'word' if encoding.w else 'byte'
                destination = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2]}' + ']'
                displacement = bytearray([ins[2]]) if encoding.w == 0 else bytearray([ins[2], 0x00])
                dest_value = add_bytearrays(R_M_STORAGE[encoding.r_m], displacement)
                decoded_bytes += 1
            elif encoding.mod == 0b10:
                byte_size = 'word' # if encoding.w else 'byte'
                destination = '[' + R_M_TABLE[encoding.r_m] + f' + {ins[2] | (ins[3] << 8)}' + ']'
                dest_value = add_bytearrays(R_M_STORAGE[encoding.r_m], bytearray([ins[2], ins[3]]))
                decoded_bytes += 2
            if encoding.s == 0 and encoding.w == 1:
                source = f'{ins[decoded_bytes] | (ins[decoded_bytes + 1] << 8)}'
                src_value = bytearray([ins[decoded_bytes], ins[decoded_bytes + 1]])
                decoded_bytes += 2 
            else:
                source = f'{ins[decoded_bytes]}'
                src_value = bytearray([ins[decoded_bytes]])
                decoded_bytes += 1
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                dest_value=dest_value,
                source=source,
                src_value=src_value,
                byte_size=byte_size
            )
        
        elif pattern == DecodePattern.I2ACC:
            operation = OP_TABLE[encoding.op]
            if encoding.w == 0:
                destination = 'al'
                dest_value = REG_STORAGE[0][0] 
                source = f'{ins[decoded_bytes]}'
                src_value = bytearray([ins[decoded_bytes]])
                decoded_bytes += 1
            else:
                destination = 'ax'
                dest_value = REG_STORAGE[1][0]
                source = f'{ins[decoded_bytes] | (ins[decoded_bytes + 1] << 8)}'
                src_value = bytearray([ins[decoded_bytes], ins[decoded_bytes + 1]])
                decoded_bytes += 2
            asm_instruction = AsmInstruction(
                operation=operation,
                destination=destination,
                dest_value=dest_value,
                source=source,
                src_value=src_value,
                byte_size=byte_size
            )
        
        elif pattern == DecodePattern.JUMP:
            operation = OP_TABLE[encoding.op]
            dest_value = bytearray([ins[decoded_bytes]])
            asm_instruction = AsmInstruction(
                operation=operation,
                dest_value=dest_value,
            )

        assert isinstance(operation, str), "Operation must be a string"
        assert isinstance(dest_value, bytearray), "Destination value must be a bytearray"
        assert isinstance(src_value, bytearray), "Source value must be a bytearray"

        return asm_instruction, decoded_bytes

    except Exception as e:
        machine_code_str = ' '.join([f"{ins[i]:08b}" for i in range(decoded_bytes)])
        raise ValueError(f"Error decoding bytes: {machine_code_str} \n With error: {e}") from e


def evaluate_instruction(asm_instruction: AsmInstruction):
    global FLAGS_REG, IP_REG

    # Compute instruction
    dest_init_value = asm_instruction.dest_value[:]
    if asm_instruction.operation == 'mov':
        asm_instruction.dest_value[:] = asm_instruction.src_value[:]
    elif asm_instruction.operation == 'add':
        asm_instruction.dest_value[:] = add_bytearrays(asm_instruction.dest_value, asm_instruction.src_value)
    elif asm_instruction.operation == 'sub':
        asm_instruction.dest_value[:] = add_bytearrays(asm_instruction.dest_value, asm_instruction.src_value)
    elif asm_instruction.operation == 'cmp':
        dest = asm_instruction.dest_value[:]
        src = asm_instruction.src_value[:]
        # if 

    elif asm_instruction.operation == 'jnz':
        IP_REG[:] = add_bytearrays(IP_REG, asm_instruction.dest_value) if is_bit_set(FLAGS_REG, 0) else IP_REG[:]

    # Set the flags register based on the result of the operation
    dest_int = int.from_bytes(asm_instruction.dest_value, byteorder='little')
    if dest_int == 0:
        FLAGS_REG = set_bit(FLAGS_REG, 0, 1)
    else:
        FLAGS_REG = set_bit(FLAGS_REG, 0, 0)
    if asm_instruction.dest_value >= bytearray([0x80, 0x00]):
        # if the reg value is larger or equal to 0x8000, it means the sign bit is set 
        FLAGS_REG = set_bit(FLAGS_REG, 2, 1)
    else:
        FLAGS_REG = set_bit(FLAGS_REG, 2, 0)
        
    return dest_init_value, asm_instruction


def decode(filename: str):
    DECODED_BYTES = 0

    # load binary instruction
    with open('./decoding_8086/' + filename, 'rb') as f:
        ins = f.read()
    ins = bytearray(ins)

    print(f"{'Assembly Instruction':<{INSTUCTION_SPACING}} | Machine Code")
    while DECODED_BYTES < len(ins):
        instruction_start = DECODED_BYTES
        pattern = get_decode_pattern(ins[instruction_start:])
        encoding, decoded_bytes_1 = decode_field_encoding(ins[instruction_start:], pattern)
        asm_instruction, decoded_bytes_2 = decode_instruction(encoding, pattern, ins[instruction_start:])
        DECODED_BYTES += decoded_bytes_1 + decoded_bytes_2
        dest_init_value, asm_instruction = evaluate_instruction(asm_instruction)

        # Print the instruction and machine code
        machine_code_str = ' '.join([f"{ins[i]:08b}" for i in range(DECODED_BYTES - instruction_start)])
        asm_instruction_str = gen_assembly(asm_instruction)
        print("{:<{width}} | {}".format(asm_instruction_str, machine_code_str, width=INSTUCTION_SPACING))    
        print(f"{asm_instruction_str:<{INSTUCTION_SPACING}} | {asm_instruction.destination}:{format_bytearray(dest_init_value)} -> {format_bytearray(asm_instruction.dest_value)}")
    

    # print final register values
    print("\nFinal Register Values:")
    for idx in [0,3,1,2,4,5,6,7]:
        reg_name = REG_TABLE[idx][1]
        reg = FULL_REG_STORAGE[idx]
        reg_value = format_bytearray(reg)
        print(f"{reg_name}: {reg_value} | {int.from_bytes(reg, byteorder='little')}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python decode_ins.py <filename>")
        sys.exit(1)

    decode(sys.argv[1])
