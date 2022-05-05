import yaml
import os


def load_config():
    """
    Loads config from docker-compose variables or file in project root folder (i.e. folder above backend/frontend)
    """
    CONFIG_FILE = "config.yml"
    with open(CONFIG_FILE) as file:
        default_config = yaml.safe_load(file.read())

    config = {
        "data_dir": os.getenv("DATA_DIR", default_config["data_dir"]),
        "metadata_dir": os.getenv("METADATA_DIR", default_config["metadata_dir"]),
        "port": int(os.getenv("PORT", default_config["port"])),
        "num_docs": int(os.getenv("NUM_DOCS", default_config["num_docs"])),
        "return_docs": int(os.getenv("RETURN_DOCS", default_config["return_docs"])),
    }

    return config
