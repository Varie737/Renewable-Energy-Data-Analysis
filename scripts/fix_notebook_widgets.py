import nbformat
import sys

def fix_notebook(path):
    nb = nbformat.read(path, as_version=4)

    if "widgets" in nb.metadata:
        if "state" not in nb.metadata["widgets"]:
            nb.metadata["widgets"]["state"] = {}

    nbformat.write(nb, path)

if __name__ == "__main__":
    for notebook in sys.argv[1:]:
        fix_notebook(notebook)