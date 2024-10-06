from datetime import date
from platform import python_version_tuple

cookiecutter = {
    "python_version": ".".join(python_version_tuple()[:-1]),
    "this_year": date.today().year
}
