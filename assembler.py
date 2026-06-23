import sys

OPCODES = {
    "LOAD": 0x01, "ADD": 0x02, "SUB": 0x03, "JMP": 0x04, "MUL": 0x05,
    "PUSH": 0x06, "POP": 0x07, "JZ": 0x08, "JNZ": 0x09, "JC": 0x0A,
    "JNC": 0x0B, "CMP": 0x0C, "JE": 0x0D, "JL": 0x0E, "JG": 0x0F,
    "STORE": 0x10, "STOP": 0xFF,
}

REGISTERS = {
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "LR": 4, "AR": 5,
}

INSTRUCTION_SIZES = {
    "LOAD": 3, "ADD": 3, "SUB": 3, "STORE": 3,
    "JMP": 3, "JZ": 3, "JNZ": 3, "JC": 3, "JNC": 3,
    "CMP": 3, "JE": 3, "JL": 3, "JG": 3,
    "MUL": 2, "PUSH": 2, "POP": 2,
    "STOP": 1,
}

THREE_OPERAND = {"LOAD", "ADD", "SUB"}
JUMP_OPS = {"JMP", "JZ", "JNZ", "JC", "JNC", "JE", "JL", "JG"}
SINGLE_REGISTER = {"MUL", "PUSH", "POP"}


def parse_line(line):
    useful = line.split(";")[0]
    cleaned = useful.replace(",", " ").strip()
    if not cleaned:
        return None
    return cleaned.upper().split()


def parse_int(text):
    return int(text.strip(), 0)


def get_register(name):
    if name not in REGISTERS:
        raise SyntaxError(f"Unknown register: '{name}'")
    return REGISTERS[name]


def parse_ram_address(arg):
    arg = arg.strip()
    if arg.startswith("[") and arg.endswith("]"):
        arg = arg[1:-1].strip()
    value = parse_int(arg)
    if not 0 <= value <= 255:
        raise ValueError(f"RAM address {value} out of bounds (0-255)")
    return value


def parse_source_operand(arg):
    arg = arg.strip()
    if arg.startswith("[") and arg.endswith("]"):
        inner = arg[1:-1].strip()
        if inner in REGISTERS:
            return 3, REGISTERS[inner]
        value = parse_int(inner)
        if not 0 <= value <= 255:
            raise ValueError(f"RAM address {value} out of bounds (0-255)")
        return 2, value
    if arg in REGISTERS:
        return 1, REGISTERS[arg]
    value = parse_int(arg)
    if not 0 <= value <= 255:
        raise ValueError(f"Immediate value {value} out of bounds (0-255)")
    return 0, value


def parse_store_source(arg):
    arg = arg.strip()
    if arg in REGISTERS:
        return 0x80 | REGISTERS[arg]
    value = parse_int(arg)
    if not 0 <= value <= 127:
        raise ValueError(f"STORE immediate value {value} out of bounds (0-127)")
    return value


def resolve_target(target, labels):
    if target in labels:
        address = labels[target]
    else:
        try:
            address = parse_int(target)
        except ValueError:
            raise SyntaxError(f"Unknown label or address: '{target}'")
    if not 0 <= address <= 65535:
        raise ValueError(f"Target address {address} out of bounds (0-65535)")
    return address


def instruction_size(cmd):
    if cmd not in INSTRUCTION_SIZES:
        raise SyntaxError(f"Unknown instruction: '{cmd}'")
    return INSTRUCTION_SIZES[cmd]


def collect_labels(source_path):
    labels = {}
    address = 0
    errors = False

    with open(source_path, "r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            tokens = parse_line(line)
            if tokens is None:
                continue

            if tokens[0].endswith(":"):
                label_name = tokens[0][:-1]
                if label_name in labels:
                    print(f"[-] Error Line {line_number}: Label '{label_name}' already defined.")
                    errors = True
                labels[label_name] = address
                if len(tokens) == 1:
                    continue
                tokens = tokens[1:]

            cmd = tokens[0]
            try:
                address += instruction_size(cmd)
            except SyntaxError as exc:
                print(f"[-] Error Line {line_number}: {exc}")
                errors = True

    return labels, errors


def encode_instruction(cmd, tokens, labels):
    if cmd in THREE_OPERAND:
        if len(tokens) != 3:
            raise SyntaxError(f"Instruction {cmd} requires exactly 2 arguments")
        dest = get_register(tokens[1])
        mode, source = parse_source_operand(tokens[2])
        return bytes([OPCODES[cmd], (mode << 6) | dest, source])

    if cmd in JUMP_OPS:
        if len(tokens) != 2:
            raise SyntaxError(f"Instruction {cmd} requires exactly 1 argument")
        target = resolve_target(tokens[1], labels)
        return bytes([OPCODES[cmd], (target >> 8) & 0xFF, target & 0xFF])

    if cmd == "CMP":
        if len(tokens) != 3:
            raise SyntaxError("Instruction CMP requires exactly 2 registers")
        left = get_register(tokens[1])
        right = get_register(tokens[2])
        return bytes([OPCODES[cmd], left, right])

    if cmd in SINGLE_REGISTER:
        if len(tokens) != 2:
            raise SyntaxError(f"Instruction {cmd} requires exactly 1 register")
        reg = get_register(tokens[1])
        return bytes([OPCODES[cmd], reg])

    if cmd == "STORE":
        if len(tokens) != 3:
            raise SyntaxError("Instruction STORE requires exactly 2 arguments")
        ram_address = parse_ram_address(tokens[1])
        source_byte = parse_store_source(tokens[2])
        return bytes([OPCODES[cmd], ram_address, source_byte])

    if cmd == "STOP":
        if len(tokens) != 1:
            raise SyntaxError("Instruction STOP takes no arguments")
        return bytes([OPCODES[cmd]])

    raise SyntaxError(f"Unknown instruction: '{cmd}'")


def compile_source(source_path, destination_path):
    labels, label_errors = collect_labels(source_path)
    if label_errors:
        print("\n[-] Build aborted due to compilation errors.")
        return False

    binary = bytearray()
    errors = False

    with open(source_path, "r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            tokens = parse_line(line)
            if tokens is None:
                continue

            if tokens[0].endswith(":"):
                if len(tokens) == 1:
                    continue
                tokens = tokens[1:]

            cmd = tokens[0]
            try:
                binary.extend(encode_instruction(cmd, tokens, labels))
            except (SyntaxError, ValueError) as exc:
                print(f"[-] Error Line {line_number}: {exc}")
                errors = True

    if errors:
        print("\n[-] Build aborted due to compilation errors.")
        return False

    with open(destination_path, "wb") as handle:
        handle.write(binary)

    print(f"[+] Success! Generated '{destination_path}' ({len(binary)} bytes).")
    return True


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source> <output>")
        sys.exit(1)

    if not compile_source(sys.argv[1], sys.argv[2]):
        sys.exit(1)


if __name__ == "__main__":
    main()
