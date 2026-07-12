from pathlib import Path
import tomllib

MAP_CONFIG_PATH = Path(__file__).parents[1] / "config" / "map_layers.toml"
QUERY_CONFIG_PATH = Path(__file__).parents[1] / "config" / "queries.toml"

with open(MAP_CONFIG_PATH, "rb") as f:
    MAP_LAYERS = tomllib.load(f)

with open(QUERY_CONFIG_PATH, "rb") as f:
    QUERIES = tomllib.load(f)