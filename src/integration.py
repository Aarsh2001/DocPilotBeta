from anthropic import Anthropic
import fileinput


def _extract_relevant_info(text):
    start_index = text.find('"""')
    if start_index != -1:
        end_index = text.find('"""', start_index + 1)
        extracted_text = text[start_index : end_index + 3]
        return extracted_text
    else:
        return None


def generate_docstring(file_str, fn_name, key):
    with open(file_str, "r") as f:
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
    template_file = open("resources/fn_docstring_template.txt", "r")
    docstring_template = template_file.read()
    prompt = prompt.replace("[docstring_example]", docstring_template)

    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=300,
        prompt=prompt,
    )
    docstring = _extract_relevant_info(completion.completion)
    docstring = docstring.replace("\n", "\n    ")
    return "    " + docstring + "\n"


def add_docstring(key):
    # diff text file all strings, parse the file to only fetch statements with additions
    # changed file names
    with open("diff.txt", "+rb") as f:
        # intelligent regex
        content = f.readlines()
        file_fns_without_docstring = {}
        filename = " "
        contains_docstring = False
        in_func = False
        for i, line in enumerate(content):
            line = line.decode("utf-8")  # Decode the bytes to a string
            if line.startswith("+++"):
                start_index = line.find("/")
                if start_index != -1:
                    filename = line[start_index + 1 :].rstrip("\n")
                    fns_without_docstring = {}
            if line.replace(" ", "").startswith("+def"):
                in_func = True
                func_name = line.replace(" ", "").split("+def")[1].split("(")[0]
                # regex to check if there exists a docstring
            if (
                line.replace(" ", "") == "+\n"
                or line.replace(" ", "") == "\n"
                or i == len(content) - 1
            ):
                if in_func and not contains_docstring:
                    fns_without_docstring[func_name] = generate_docstring(
                        filename, func_name, key
                    )
                    if filename not in file_fns_without_docstring:
                        file_fns_without_docstring[filename] = {}
                    file_fns_without_docstring[filename] = fns_without_docstring
                in_func = False
                contains_docstring = False
                func_name = ""
            if '"""' in line:
                contains_docstring = True
    return file_fns_without_docstring


def merge_docstring(file_fns_without_docstring):
    """Merges generated docstrings into the original files.

    This function takes the dictionary of filenames and functions without docstrings,
    iterates through each file, and inserts the generated docstring at the appropriate place.

    Parameters
    ----------
    file_fns_without_docstring : dict
        A dictionary with filenames as keys, and dictionaries as values. The inner dict has
        function names without docstrings as keys, and the generated docstring as values.

    Returns
    -------
    None
        The function edits the files in place.
    """
    for filename, fns_without_docstring in file_fns_without_docstring.items():
        with open(filename, "+rb") as f:
            content = f.readlines()
            fn_wo_doc = False
            current_docstring = ""
            docstring_placement = {}
            for i, line in enumerate(content):
                line = line.decode("utf-8")

                # if a fn without docstring is defined on this line
                if (
                    any([fn_name in line for fn_name in fns_without_docstring.keys()])
                    and "def" in line
                ):
                    fn_wo_doc = True
                    for fn_name in fns_without_docstring.keys():
                        if fn_name in line:
                            current_docstring = fns_without_docstring[fn_name]
                            break
                if ("):" in line or ") ->" in line) and fn_wo_doc:
                    docstring_placement[i + 2] = current_docstring
                    current_docstring = ""
                    fn_wo_doc = False

        # sort docstring placements
        docstring_placement = dict(sorted(docstring_placement.items()))

        with fileinput.input(files=(filename,), inplace=True) as file:
            for line_num, line in enumerate(file, start=1):
                # Check if this line should have content added
                if line_num in docstring_placement:
                    content_to_add = docstring_placement[line_num]
                    print(content_to_add, end="")
                print(line, end="")


if __name__ == "__main__":
    # key = sys.argv[1]
    docstring_dict = add_docstring(
        "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"
    )
    merge_docstring(docstring_dict)
