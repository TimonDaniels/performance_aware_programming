from dataclasses import dataclass


def add_bytearrays(a: bytearray, b: bytearray) -> bytearray:
    assert isinstance(a, bytearray), "First argument must be a bytearray"
    assert isinstance(b, bytearray), "Second argument must be a bytearray"
    assert len(a) == len(b), "Both bytearrays must have the same length"
    a_val = int.from_bytes(a, byteorder='little')
    b_val = int.from_bytes(b, byteorder='little')
    result_val = a_val + b_val
    length = len(a)
    return bytearray(result_val.to_bytes(length, byteorder='little'))


def set_bit(byte_array: bytearray, bit_position: int, value: int) -> bytearray:
    assert value in (0, 1), "Value must be either 0 or 1"
    byte_index = bit_position // 8
    bit_index = bit_position % 8
    if byte_index < len(byte_array):
        byte_array[byte_index] |= (value << bit_index)
    return byte_array


def is_bit_set(byte_array, bit_position):
    byte_index = bit_position // 8
    bit_index = bit_position % 8
    assert byte_index <= len(byte_array), "Byte index out of range"
    return bool(byte_array[byte_index] & (1 << bit_index))


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
    dest_value: bytearray
    destination: str = None
    source: str = None
    src_value: bytearray = None
    byte_size: str = None


def format_bytearray(byte_arr: bytearray) -> str:
    # Note that byte_arry[0] are the lowest byte values, so we have to reverse the order
    hex_formatted = '0x' + ''.join(f'{b:02x}' for b in byte_arr[::-1])
    return hex_formatted


def gen_assembly(asm_instruction: AsmInstruction) -> str:
    """
    Generate assembly code from an AsmInstruction object.
    """
    # TODO: see if source is a immediate value and check if it is a postive or negative value
    if asm_instruction.operation == 'jnz':
        return f"{asm_instruction.operation} {int.from_bytes(asm_instruction.dest_value, byteorder='little')}"
    elif asm_instruction.byte_size:
        return f"{asm_instruction.operation} {asm_instruction.byte_size} {asm_instruction.destination}, {asm_instruction.source}"
    else:
        return f"{asm_instruction.operation} {asm_instruction.destination}, {asm_instruction.source}"
    