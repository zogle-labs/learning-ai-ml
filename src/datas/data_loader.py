import os
import sys
import pandas as pd
import yaml

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',  ))
os.chdir(project_root)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def loadData():
    config = load_config()
    print("config-->", config)

    raw_path = config['data']['raw_path']
    abs_path = os.path.abspath(raw_path) 

    df = pd.read_csv(abs_path)
    print("Loaded data...")
    return df

if __name__ == "__main__":
    data = loadData()
    print(data.head())
