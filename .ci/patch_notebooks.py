import sys
from pathlib import Path
import nbformat
import nbconvert
from traitlets.config import Config


# Notebooks that are excluded from the CI tests
EXCLUDED_NOTEBOOKS = ["data-preparation-ct-scan.ipynb"]


def patch_notebooks(notebooks_dir):
    """
    Patch notebooks in notebooks directory with replacement values
    found in notebook metadata to speed up test execution.
    This function is specific for the OpenVINO notebooks
    Github Actions CI.

    For example: change nr of epochs from 15 to 1 in
    301-tensorflow-training-openvino-nncf.ipynb by adding
    {"test_replace": {"epochs = 15": "epochs = 1"} to the cell
    metadata of the cell that contains `epochs = 15`

    :param notebooks_dir: Directory that contains the notebook subdirectories.
                          For example: openvino_notebooks/notebooks
    """

    nb_convert_config = Config()
    nb_convert_config.NotebookExporter.preprocessors = ["nbconvert.preprocessors.ClearOutputPreprocessor"]
    output_remover = nbconvert.NotebookExporter(nb_convert_config)
    for notebookfile in Path(notebooks_dir).glob("**/*.ipynb"):
        if (
            not str(notebookfile.name).startswith("test_")
            and notebookfile.name not in EXCLUDED_NOTEBOOKS
        ):
            nb = nbformat.read(notebookfile, as_version=nbformat.NO_CONVERT)
            found = False
            for cell in nb["cells"]:
                replace_dict = cell.get("metadata", {}).get("test_replace")
                if replace_dict is not None:
                    found = True
                    for source_value, target_value in replace_dict.items():
                        if source_value not in cell["source"]:
                            raise ValueError(
                                f"Processing {notebookfile} failed: {source_value} does not exist in cell"
                            )
                        cell["source"] = cell["source"].replace(
                            source_value, target_value
                        )
                        cell["source"] = "# Modified for testing\n" + cell["source"]
                        print(
                            f"Processed {notebookfile}: {source_value} -> {target_value}"
                        )
            if not found:
                print(f"No replacements found for {notebookfile}")
            nb_without_out, _ = output_remover.from_notebook_node(nb)
            with notebookfile.with_name(f"test_{notebookfile.name}").open("w", encoding="utf-8") as out_file:
                out_file.write(nb_without_out)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If this script is called without any arguments, patch notebooks
        # in the current directory (recursively).
        notebooks_dir = "."
    else:
        # If the script is called with a command line argument, it is expected
        # to be the path to the notebooks directory
        notebooks_dir = sys.argv[1]
        if not Path(notebooks_dir).is_dir():
            raise ValueError(f"'{notebooks_dir}' is not an existing directory")

    patch_notebooks(notebooks_dir)
