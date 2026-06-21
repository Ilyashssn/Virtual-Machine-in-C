import sys

OPCODES = {
    "LOAD": 0x01, "ADD": 0x02, "SUB": 0x03, "JMP": 0x04, "MUL": 0x05,
    "PUSH": 0x06, "POP": 0x07, "JZ": 0x08, "JNZ": 0x09, "JC": 0x0A,
    "JNC": 0x0B, "CMP": 0x0C, "JE": 0x0D, "JL": 0x0E, "JG": 0x0F, "STOP": 0xFF
}

REGISTRES = {
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "LR": 4, "AR": 5
}

def parser_ligne(ligne):
    ligne_utile = ligne.split(";")[0]
    ligne_propre = ligne_utile.replace(",", " ").strip()
    if not ligne_propre:
        return None
    return ligne_propre.upper().split()

def analyser_argument_source(arg_texte, num_ligne):
    arg_texte = arg_texte.strip()
    
    if arg_texte.startswith("[") and arg_texte.endswith("]"):
        interieur = arg_texte[1:-1].strip()
        if interieur in REGISTRES:
            return 3, REGISTRES[interieur]
        else:
            try:
                val = int(interieur)
                if not (0 <= val <= 255):
                    raise ValueError(f"RAM address {val} out of bounds (0-255)")
                return 2, val
            except ValueError:
                raise SyntaxError(f"Invalid bracket content: '{interieur}'")
                
    elif arg_texte in REGISTRES:
        return 1, REGISTRES[arg_texte]
        
    else:
        try:
            val = int(arg_texte)
            if not (0 <= val <= 255):
                raise ValueError(f"Immediate value {val} out of bounds (0-255)")
            return 0, val
        except ValueError:
            raise SyntaxError(f"Invalid argument: '{arg_texte}'")

def compiler(fichier_source, fichier_destination):
    LABELS = {}
    adresse_actuelle = 0
    erreurs_detectees = False
    
    try:
        with open(fichier_source, "r", encoding="utf-8") as f:
            for num_ligne, ligne in enumerate(f, 1):
                tokens = parser_ligne(ligne)
                if tokens is None:
                    continue
                
                if tokens[0].endswith(":"):
                    nom_label = tokens[0][:-1]
                    if nom_label in LABELS:
                        print(f"[-] Error Line {num_ligne}: Label '{nom_label}' already defined.")
                        erreurs_detectees = True
                    LABELS[nom_label] = adresse_actuelle
                    
                    if len(tokens) > 1:
                        tokens = tokens[1:]
                    else:
                        continue
                
                cmd = tokens[0]
                if cmd in ["LOAD", "ADD", "SUB"]:
                    adresse_actuelle += 3
                elif cmd in ["JMP", "JZ", "JNZ", "JC", "JNC", "CMP", "JE", "JL", "JG"]:
                    adresse_actuelle += 3
                elif cmd in ["MUL", "PUSH", "POP"]:
                    adresse_actuelle += 2
                elif cmd == "STOP":
                    adresse_actuelle += 1
                    
    except FileNotFoundError:
        print(f"[-] Error: Source file '{fichier_source}' not found.")
        return

    code_binaire = bytearray()
    
    try:
        with open(fichier_source, "r", encoding="utf-8") as f:
            for num_ligne, ligne in enumerate(f, 1):
                tokens = parser_ligne(ligne)
                if tokens is None:
                    continue
                    
                if tokens[0].endswith(":"):
                    if len(tokens) > 1:
                        tokens = tokens[1:]
                    else:
                        continue
                        
                cmd = tokens[0]
                
                try:
                    if cmd in ["LOAD", "ADD", "SUB"]:
                        if len(tokens) != 3:
                            raise SyntaxError(f"Instruction {cmd} requires exactly 2 arguments")
                        r1_index = REGISTRES[tokens[1]]
                        mod, valeur_src = analyser_argument_source(tokens[2], num_ligne)
                        
                        code_binaire.append(OPCODES[cmd])
                        code_binaire.append((mod << 6) | r1_index)
                        code_binaire.append(valeur_src)
                    
                    elif cmd in ["JMP", "JZ", "JNZ", "JC", "JNC", "JE", "JL", "JG"]:
                        if len(tokens) != 2:
                            raise SyntaxError(f"Instruction {cmd} requires exactly 1 argument")
                        
                        target = tokens[1]
                        if target in LABELS:
                            adresse_cible = LABELS[target]
                        else:
                            try:
                                adresse_cible = int(target)
                            except ValueError:
                                raise SyntaxError(f"Unknown label or address: '{target}'")
                        
                        if not (0 <= adresse_cible <= 65535):
                            raise ValueError(f"Target address {adresse_cible} out of bounds")
                            
                        code_binaire.append(OPCODES[cmd])
                        code_binaire.append((adresse_cible >> 8) & 0xFF)
                        code_binaire.append(adresse_cible & 0xFF)

                    elif cmd == "CMP":
                        if len(tokens) != 3:
                            raise SyntaxError("Instruction CMP requires exactly 2 registers")
                        code_binaire.append(OPCODES["CMP"])
                        code_binaire.append(REGISTRES[tokens[1]])
                        code_binaire.append(REGISTRES[tokens[2]])
                    
                    elif cmd in ["MUL", "PUSH", "POP"]:
                        if len(tokens) != 2:
                            raise SyntaxError(f"Instruction {cmd} requires exactly 1 register")
                        code_binaire.append(OPCODES[cmd])
                        code_binaire.append(REGISTRES[tokens[1]])
                    
                    elif cmd == "STOP":
                        if len(tokens) != 1:
                            raise SyntaxError("Instruction STOP takes no arguments")
                        code_binaire.append(OPCODES["STOP"])
                        
                except (SyntaxError, KeyError, ValueError) as e:
                    print(f"[-] Error Line {num_ligne}: {e}")
                    erreurs_detectees = True
                    continue

        if erreurs_detectees:
            print("\n[-] Build aborted due to compilation errors.")
            return
            
        with open(fichier_destination, "wb") as f_out:
            f_out.write(code_binaire)
        print(f"[+] Success! Generated '{fichier_destination}' ({len(code_binaire)} bytes).")

    except Exception as e:
        print(f"[-] Critical error during translation: {e}")

if __name__ == "__main__":
    compiler(r"C:\Users\acer\Desktop\VM\assembly_code_example.txt", r"C:\Users\acer\Desktop\VM\binary_code_example")