from configparser import ConfigParser
import os


def config(
    filename="./config.ini",
    section="postgresql",
):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename, encoding="utf-8-sig")

    # get section, default to postgresql
    conf_dict = {}
    if parser.has_section(section):
        params = parser.items(section)
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
    return conf_dict
