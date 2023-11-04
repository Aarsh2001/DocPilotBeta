from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import sys
import json
import os


def generate_docstring(file_str, fn_name, key):
    anthropic = Anthropic(
        api_key=key,
    )

    prompt_file = open("resources/prompt.txt", "r")
    prompt = prompt_file.read()
    prompt = prompt.replace("[fn_name]", fn_name)
    prompt = prompt.replace("[file]", file_str)

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
    print(completion.completion)

def starter_code(key):
    # diff text file all strings, parse the file to only fetch statements with additions
    with open("diff.txt", '+rb') as f:
        # intelligent regex 
        content = f.open()
        # changed function names here
    # changed file names
    with open("~/files.json", 'r') as f:
        filename = json.loads(f)
        # use os to walkthrough this file path
        generate_docstring()
    generate_docstring(filename, content, key)

if __name__ == "__main__":
    key = sys.argv[1]
    starter_code(key)
    