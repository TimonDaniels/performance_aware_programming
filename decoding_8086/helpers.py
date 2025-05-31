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
    dest_value: bytearray
    source: str
    src_value: bytearray
    byte_size: str


def format_bytearray(byte_arr: bytearray) -> str:
    # Note that byte_arry[0] are the lowest byte values, so we have to reverse the order
    hex_formatted = '0x' + ''.join(f'{b:02x}' for b in byte_arr[::-1])
    return hex_formatted


def gen_assembly(asm_instruction: AsmInstruction) -> str:
    """
    Generate assembly code from an AsmInstruction object.
    """
    if asm_instruction.byte_size:
        return f"{asm_instruction.operation} {asm_instruction.byte_size} {asm_instruction.destination}, {asm_instruction.source}"
    else:
        return f"{asm_instruction.operation} {asm_instruction.destination}, {asm_instruction.source}"
    