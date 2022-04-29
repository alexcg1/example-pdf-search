import yaml
import os


def load_config():
    """
    Loads config from docker-compose variables or file in project root folder (i.e. folder above backend/frontend)
    """
    try:
        config = {
            "data_dir": os.getenv("DATA_DIR", "data"),
            "metadata_dir": os.getenv("METADATA_DIR", "data/metadata"),
            "port": int(os.getenv("PORT", 5689)),
            "num_docs": int(os.getenv("NUM_DOCS", 1000)),
            "return_docs": int(os.getenv("RETURN_DOCS", 10)),
        }
    except:
        CONFIG_FILE = "config.yml"
        with open(CONFIG_FILE) as file:
            config = yaml.safe_load(file.read())

    return config
