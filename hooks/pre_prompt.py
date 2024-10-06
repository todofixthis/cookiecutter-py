from datetime import date
from json import dump, load
from platform import python_version_tuple


def main() -> None:
    context_filename = "cookiecutter.json"

    with open(context_filename, "r") as f_in:
        context_data: dict[str, str] = load(f_in)

    context_data.update({
        "python_version": ".".join(python_version_tuple()[:-1]),
        "this_year": date.today().year
    })

    with open(context_filename, "w") as f_out:
        dump(context_data, f_out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
