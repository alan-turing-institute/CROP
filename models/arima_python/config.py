from configparser import ConfigParser
import os


def config(filename="./config.ini", section="postgresql"):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename, encoding="utf-8-sig")

    # get section and save as a dictionary
    conf_dict = {}
    if parser.has_section(section):
        params = parser.items(section)  # returns a list with item name and item value
        for param in params:
            conf_dict[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    # If the same variable is defined also as an environment variable, have that
    # override the value in the file.
    for key in conf_dict.keys():
        env_var = "CROP_{}".format(key).upper()
        if env_var in os.environ:
            conf_dict[key] = os.environ[env_var]

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
