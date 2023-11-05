from anthropic import Anthropic
import sys
import fileinput


filename = "dummy-files/test.py"

def _extract_relevant_info(text):
    start_index = text.find('"""')
    if start_index != -1:
        end_index = text.find('"""', start_index + 1)
        extracted_text = text[start_index:end_index+3]
        return extracted_text
    else:
        return None

def generate_docstring(file_str, fn_name, key):
    with open(file_str, 'r') as f:
        content = f.read()
    anthropic = Anthropic(
        api_key=key,
    )

    prompt_file = open("resources/prompt.txt", "r")
    prompt = prompt_file.read()
    prompt = prompt.replace("[fn_name]", fn_name)
    prompt = prompt.replace("[file]", content)

    # TODO: replace this default docstring template with one generated by Claude?
    # (so it can support any language, not just Python)
    template_file = open("resources/python_docstring_template.txt", "r")
    docstring_template = template_file.read()
    prompt = prompt.replace("[docstring_example]", docstring_template)

    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=300,
        prompt=prompt,
    )
    print(_extract_relevant_info(completion.completion))
    print("\n")
    docstring = _extract_relevant_info(completion.completion)
    return docstring + "\n"

def add_docstring(key):
    # diff text file all strings, parse the file to only fetch statements with additions
    # changed file names
    with open("diff.txt", '+rb') as f:
        # intelligent regex
        content = f.readlines()
        fns_with_docstring = dict()
        contains_docstring = False
        in_func = False
        for i, line in enumerate(content):
            line = line.decode('utf-8')  # Decode the bytes to a string
            if line.startswith("+def "):
                in_func = True
                func_name = line.split('+def ')[1].split('(')[0]
                # regex to check if there exists a docstring
            if line.replace(' ', '') == '+\n' or line.replace(' ', '') == '\n' or i == len(content) - 1:
                if in_func and not contains_docstring:
                    fns_with_docstring[func_name] = generate_docstring(filename, func_name, key)
                in_func = False
                contains_docstring = False
                func_name = ""
            if '"""' in line:
                contains_docstring = True
    return fns_with_docstring


def merge_docstring(fns_without_docstring):
    with open(filename, '+rb') as f:
        content = f.readlines()
        fn_wo_doc = False
        current_docstring = ""
        docstring_placement = {}
        for i, line in enumerate(content):
            line = line.decode('utf-8')

            # if a fn without docstring is defined on this line
            if any([fn_name in line for fn_name in fns_without_docstring.keys()]) and "def" in line:
                fn_wo_doc = True
                for fn_name in fns_without_docstring.keys():
                    if fn_name in line:
                        current_docstring = fns_without_docstring[fn_name]
                        break
            if ("):" in line or ") ->" in line) and fn_wo_doc:
                docstring_placement[i + 2] = current_docstring
                current_docstring = ""
                fn_wo_doc = False
    
    docstring_placement = dict(sorted(docstring_placement.items()))  # sort docstring placements

    accumulated_shift = 0
    modified_docstring_placement = {}
    for i, (ln_num, docstring) in enumerate(docstring_placement.items()):
        new_ln_num = ln_num + i + accumulated_shift
        modified_docstring_placement[new_ln_num] = docstring
        accumulated_shift += docstring.count("\n") + 1
    # TODO: test the shift here is correct with many docstrings being added

    with fileinput.input(files=(filename,), inplace=True) as file:
        for line_num, line in enumerate(file, start=1):
            # Check if this line should have content added
            if line_num in modified_docstring_placement:
                content_to_add = modified_docstring_placement[line_num]
                print(content_to_add, end='')
            print(line, end='')

if __name__ == "__main__":
    key = sys.argv[1]
    docstring_dict = add_docstring(key)
    merge_docstring(docstring_dict)
    