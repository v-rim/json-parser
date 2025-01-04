"""
<json> ::= <primitive> | <container>

<primitive> ::= <number> | <string> | <boolean>
; Where:
; <number> is a valid real number expressed in one of a number of given formats
; <string> is a string of valid characters enclosed in quotes
; <boolean> is one of the literal strings 'true', 'false', or 'null' (unquoted)

<container> ::= <object> | <array>
<array> ::= '[' [ <json> *(', ' <json>) ] ']' ; A sequence of JSON values separated by commas
<object> ::= '{' [ <member> *(', ' <member>) ] '}' ; A sequence of 'members'
<member> ::= <string> ': ' <json> ; A pair consisting of a name, and a JSON value
"""

import re


def preprocess(source):
    preprocessed = ""
    inside_quotes = False
    for c in source:
        if c == '"':
            inside_quotes = not inside_quotes
        if not inside_quotes:
            preprocessed += re.sub(r"\s+", "", c)
        else:
            preprocessed += c
    return preprocessed


def assign_scopes(source):
    # Mapping of a bracket character to the number of characters until its pair
    scope_table = {}

    square_stack = []
    curly_stack = []
    type_stack = []
    for i, c in enumerate(source):
        if c == "[":
            square_stack.append(i)
            type_stack.append("[")
        elif c == "]":
            if square_stack == []:
                raise Exception("Extra square bracket")
            if type_stack[-1] != "[":
                raise Exception("Mismatched bracket types")
            type_stack.pop()
            left = square_stack.pop()
            scope_table[left] = i - left
        elif c == "{":
            curly_stack.append(i)
            type_stack.append("{")
        elif c == "}":
            if curly_stack == []:
                raise Exception("Extra curly bracket")
            if type_stack[-1] != "{":
                raise Exception("Mismatched bracket types")
            type_stack.pop()
            left = curly_stack.pop()
            scope_table[left] = i - left

    if square_stack != []:
        raise Exception("Missing square bracket")
    if curly_stack != []:
        raise Exception("Missing curly bracket")

    return scope_table


def parse(to_parse, scope_table, start) -> None:
    if to_parse == "":
        raise Exception("Invalid primitive", to_parse)
    elif to_parse == "[]":  # Empty arrays are valid(?)
        return []
    elif to_parse == "{}":  # Empty objects are valid(?)
        return {}
    elif to_parse[0] == "[":  # Array
        ret = []
        len_to_parse = len(to_parse)

        value = ""
        i = 1
        while i < len_to_parse:
            c = to_parse[i]
            if (global_start := start + i) in scope_table:
                skip = scope_table[global_start]
                value += to_parse[i : i + skip + 1]
                i += skip + 1
            elif c == ",":
                ret.append(
                    parse(
                        value,
                        scope_table,
                        start + i - len(value),
                    )
                )
                value = ""
                i += 1
            elif i == len_to_parse - 1:
                ret.append(
                    parse(
                        value,
                        scope_table,
                        start + i - len(value),
                    )
                )
                i += 1
            else:
                value += c
                i += 1

        return ret

    elif to_parse[0] == "{":  # Object
        ret = {}
        len_to_parse = len(to_parse)

        try:
            colon_index = to_parse.index(":")
        except Exception:
            raise Exception("Invalid structure for object", to_parse)
        key = to_parse[1:colon_index]
        value = ""

        i = 1 + colon_index
        while i < len_to_parse:
            c = to_parse[i]
            if (global_start := start + i) in scope_table:
                skip = scope_table[global_start]
                value += to_parse[i : i + skip + 1]
                i += skip + 1
            elif c == ",":
                # Validate key manually
                if not re.match(r"\"(.*?)\"", key):
                    raise Exception("Invalid object key", key)
                key = str(key[1:-1])

                ret[key] = parse(
                    value,
                    scope_table,
                    start + i - len(value),
                )

                try:
                    colon_index = to_parse.index(":", i)
                except Exception:
                    raise Exception("Invalid structure for object", to_parse)
                key = to_parse[i + 1 : colon_index]
                value = ""

                i = 1 + colon_index
            elif i == len_to_parse - 1:
                # Validate key manually
                if not re.match(r"\"(.*?)\"", key):
                    raise Exception("Invalid object key", key)
                key = str(key[1:-1])

                ret[key] = parse(
                    value,
                    scope_table,
                    start + i - len(value),
                )
                i += 1
            else:
                value += c
                i += 1

        return ret

    else:  # Primitives
        if re.match(r'"(.*?)"', to_parse):
            return str(to_parse[1:-1])
        if re.match(r"-?\d+(\.\d+)?", to_parse):
            return float(to_parse)
        if re.match(r"\b(true|false)\b", to_parse):
            return bool(to_parse)
        if re.match(r"\bnull\b", to_parse):
            return None
        else:
            raise Exception("Unknown object", to_parse)


def main(sources):
    def apply_all(source) -> None:
        preprocessed = preprocess(source)
        parsed = parse(
            preprocessed,
            assign_scopes(preprocessed),
            0,
        )
        print(parsed)

    for i, source in enumerate(sources):
        try:
            print(f"---------- Running test {i:2} ----------")
            apply_all(source)
        except Exception as e:
            print(f">>>>>>>>>> Error on test {i:2} <<<<<<<<<")
            print(e)
        finally:
            print()


if __name__ == "__main__":
    sources = [
        '"Hello_World!"',
        "12.12",
        "true",
        "null",
        """
        [
            [],
            [null, true],
            ["hello", ["WORLD", "!"]]
        ]
        """,
        """
        {"menu": {
            "id": "file",
            "value": "File",
            "popup": {
                "menuitem": [
                {"value": "New", "onclick": "CreateNewDoc()"},
                {"value": "Open", "onclick": "OpenDoc()"},
                {"value": "Close", "onclick": "CloseDoc()"}
                ]
            }
        }}
        """,
        """
        {
            "glossary": {
                "title": "example glossary",
                "GlossDiv": {
                    "title": "S",
                    "GlossList": {
                        "GlossEntry": {
                            "ID": "SGML",
                            "SortAs": "SGML",
                            "GlossTerm": "Standard Generalized Markup Language",
                            "Acronym": "SGML",
                            "Abbrev": "ISO 8879 1986",
                            "GlossDef": {
                                "para": "A meta-markup language used to create markup languages such as DocBook.",
                                "GlossSeeAlso": ["GML", "XML"]
                            },
                            "GlossSee": "markup"
                        }
                    }
                }
            }
        }
        """,
    ]

    main(sources)
