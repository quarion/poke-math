import requests
import os
import shutil
import json


def normalize_name(name):
    """Normalize Pokémon names to match PokéAPI format."""
    special_cases = {
        "Nidoran♂": "nidoran-m",
        "Nidoran♀": "nidoran-f",
        "Mr. Mime": "mr-mime",
        "Mime Jr.": "mime-jr",
    }
    if name in special_cases:
        return special_cases[name]
    return name.lower().replace(" ", "-")


def sanitize_filename(name):
    name = name.lower()
    name = name.replace("♂", " male").replace("♀", " female")
    return name


def load_existing_json(json_path):
    """Load existing JSON data if it exists, otherwise return an empty structure."""
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    return {"pokemons": {}, "tiers": {}}


def save_json(data, json_path):
    """Save the updated data to the JSON file."""
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)


def fetch_pokemon_mapping():
    """Fetch all Pokémon data from PokéAPI to create a name-to-ID mapping."""
    response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=100000")
    if response.status_code != 200:
        raise Exception("Failed to fetch Pokémon list from PokéAPI")
    data = response.json()
    return {pokemon["name"]: pokemon["url"].split("/")[-2] for pokemon in data["results"]}


def read_pokemon_list(file_path):
    """Read the list of Pokémon names and tiers from the file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("Error: 'pokemon_list.txt' not found. Please create it with one Pokémon name per line.")

    with open(file_path, "r") as f:
        pokemon_lines = [line.strip() for line in f.readlines() if line.strip()]

    pokemon_list = []
    for line in pokemon_lines:
        parts = line.split(";")
        name = parts[0].strip().lower()  # Convert name to lowercase
        tier_str = parts[1].strip() if len(parts) > 1 else "0"
        try:
            tier = int(tier_str)
        except ValueError:
            tier = 0
        pokemon_list.append((name, tier))

    return pokemon_list


def download_image(original_name, pokemon_id, full_image_path):
    image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(full_image_path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        print(f"Downloaded image for {original_name} to {full_image_path}")
    else:
        print(f"Failed to download image for {original_name} (HTTP {response.status_code})")


def update_json_data(json_data, pokemon_list, name_to_id, image_folder):
    for original_name, tier in pokemon_list:
        normalized_name = normalize_name(original_name)
        if normalized_name in name_to_id:
            pokemon_id = name_to_id[normalized_name]

            # Compute the sanitized file name
            sanitized_name = sanitize_filename(original_name)
            file_name = f"{sanitized_name}.png"

            # Construct full path for file system operations
            full_image_path = os.path.join(image_folder, file_name)

            # Download the image if it doesn't exist
            if not os.path.exists(full_image_path):
                download_image(original_name, pokemon_id, full_image_path)

            # Initialize the Pokémon entry if it doesn't exist
            if original_name not in json_data["pokemons"]:
                json_data["pokemons"][original_name] = {}

            # Set the image_path to just the file name (no folder)
            json_data["pokemons"][original_name]["image_path"] = file_name

            # Remove from existing tiers
            for tier_list in json_data["tiers"].values():
                if original_name in tier_list:
                    tier_list.remove(original_name)
                    break

            # Add to the new tier
            tier_key = str(tier)
            json_data["tiers"].setdefault(tier_key, []).append(original_name)
        else:
            print(f"Pokémon '{original_name}' not found in PokéAPI")

    return json_data

def main():
    """Main function to execute the Pokémon scraping and JSON generation."""
    # File paths
    input_file = "pokemon_list.txt"
    json_path = "pokemons.json"
    image_folder = "pokemon_images"

    try:
        # Create image folder
        os.makedirs(image_folder, exist_ok=True)

        # Fetch Pokémon mapping
        name_to_id = fetch_pokemon_mapping()

        # Read Pokémon list from file
        pokemon_list = read_pokemon_list(input_file)

        # Load existing JSON
        json_data = load_existing_json(json_path)

        # Update JSON with new data
        update_json_data(json_data, pokemon_list, name_to_id, image_folder)

        # Save updated JSON
        save_json(json_data, json_path)
        print(f"Updated JSON data saved to {json_path}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()