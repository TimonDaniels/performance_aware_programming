from helpers import add_bytearrays

IP_REG = bytearray([0, 0])
FLAGS_REG = bytearray([0, 0])   # ZF, PF, SF, CF, OF, AF, DF, IF

FULL_REG_STORAGE = [
    bytearray([0, 0]),
    bytearray([0, 0]),
    bytearray([0, 0]),
    bytearray([0, 0]),
    bytearray([0, 0]),
    bytearray([0, 0]),
    bytearray([0, 0]),
    bytearray([0, 0]),
]

HALF_REG_STORAGE = [
    FULL_REG_STORAGE[0][:1],
    FULL_REG_STORAGE[1][:1],
    FULL_REG_STORAGE[2][:1],
    FULL_REG_STORAGE[3][:1],
    FULL_REG_STORAGE[0][1:],
    FULL_REG_STORAGE[1][1:],
    FULL_REG_STORAGE[2][1:],
    FULL_REG_STORAGE[3][1:],
]

# REG_STORAGE should have exact same indexing as REG_TABLE
REG_STORAGE = [
    HALF_REG_STORAGE, FULL_REG_STORAGE
]

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

R_M_STORAGE = [
    add_bytearrays(FULL_REG_STORAGE[3], FULL_REG_STORAGE[6]),
    add_bytearrays(FULL_REG_STORAGE[3], FULL_REG_STORAGE[7]),
    add_bytearrays(FULL_REG_STORAGE[5], FULL_REG_STORAGE[6]),
    add_bytearrays(FULL_REG_STORAGE[5], FULL_REG_STORAGE[7]),
    FULL_REG_STORAGE[6],
    FULL_REG_STORAGE[7],
    FULL_REG_STORAGE[5],
    FULL_REG_STORAGE[3],
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
    0b000: 'add',
    0b000001: 'add',
    0b111: 'cmp',
    0b001110: 'cmp',
    0b001111: 'cmp',
    0b101: 'sub',
    0b001011: 'sub',
    0b001010: 'sub',
    0b01110101: 'jnz',
}