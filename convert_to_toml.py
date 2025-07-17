def convert_env_to_toml(env_path, toml_path):
    with open(env_path) as f:
        lines = f.readlines()

    with open(toml_path, 'w') as f:
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            value = value.strip().strip('"').strip("'")

            # Try to infer type
            if value.lower() in ("true", "false"):
                f.write(f'{key} = {value.lower()}\n')
            elif value.isdigit():
                f.write(f'{key} = {value}\n')
            else:
                f.write(f'{key} = "{value}"\n')

if __name__ == "__main__":
    # Example usage
    convert_env_to_toml(".env", "config.toml")

