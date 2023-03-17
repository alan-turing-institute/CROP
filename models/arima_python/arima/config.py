"""
Python module to read the parameters specified in the configuration file,
including parameters required to connect to the PostgreSQL database server
"""

from configparser import ConfigParser
import os
import ast


def config(
    # gets config.ini file from the parent directory, no matter where the script is run from
    filename=os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "config.ini"
    ),
    section="postgresql",
):

    # check that configuration file exists
    if not os.path.isfile(filename):
        raise Exception(f"File {filename} does not exist")

    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename, encoding="utf-8-sig")

    # get section and save as a dictionary
    conf_dict = {}
    if parser.has_section(section):
        params = parser.items(section)  # returns a list with item name and item value
        for param in params:
            try:
                # use ast.literal_eval to convert a string to a Python literal structure
                conf_dict[param[0]] = ast.literal_eval(parser.get(section, param[0]))
            except Exception as e:
                print(f"Error while parsing '{param[0]}': {e}")
                raise
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    # If the same variable is defined also as an environment variable, have that
    # override the value in the file.
    # Note that the environment variable must follow this structure: CROP_ARIMA_VARIABLENAME
    for key in conf_dict.keys():
        env_var = "CROP_ARIMA_{}".format(key).upper()
        if env_var in os.environ:
            # use ast.literal_eval to convert a string to a Python literal structure
            conf_dict[key] = ast.literal_eval(os.environ[env_var])

    # special treatment for SQL environment variables
    if section == "postgresql":
        env_var1 = "CROP_SQL_HOST"
        env_var2 = "CROP_SQL_USERNAME"
        if env_var1 in os.environ:
            conf_dict["host"] = os.environ[env_var1]
            if env_var2 in os.environ:
                conf_dict["user"] = os.environ[env_var2] + "@" + os.environ[env_var1]
        env_var = "CROP_SQL_PASS"
        if env_var in os.environ:
            conf_dict["password"] = os.environ[env_var]
        env_var = "CROP_SQL_DBNAME"
        if env_var in os.environ:
            conf_dict["dbname"] = os.environ[env_var]

    return conf_dict
