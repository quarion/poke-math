import requests
import os
import shutil


def normalize_name(name):
    """Normalize Pokémon names to match PokéAPI format."""
    special_cases = {
        "Nidoran♂": "nidoran-m",
        "Nidoran♀": "nidoran-f",
        "Mr. Mime": "mr-mime",
        "Mime Jr.": "mime-jr",
        # Add more special cases if needed
    }
    if name in special_cases:
        return special_cases[name]
    return name.lower().replace(" ", "-")


def sanitize_filename(name):
    """Ensure filenames are valid by replacing special characters."""
    return name.replace("♂", " Male").replace("♀", " Female")


# Step 1: Fetch all Pokémon data from PokéAPI to create a name-to-ID mapping
response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=100000")
if response.status_code != 200:
    print("Failed to fetch Pokémon list from PokéAPI")
    exit()

data = response.json()
name_to_id = {pokemon["name"]: pokemon["url"].split("/")[-2] for pokemon in data["results"]}

# Step 2: Read the list of Pokémon names from the file
try:
    with open("pokemon_list.txt", "r") as f:
        pokemon_list = [line.strip() for line in f.readlines() if line.strip()]
except FileNotFoundError:
    print("Error: 'pokemon_list.txt' not found. Please create it with one Pokémon name per line.")
    exit()

# Step 3: Create a folder for the images
os.makedirs("pokemon_images", exist_ok=True)

# Step 4: Download images for each Pokémon
for original_name in pokemon_list:
    normalized_name = normalize_name(original_name)
    if normalized_name in name_to_id:
        pokemon_id = name_to_id[normalized_name]
        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"

        # Download the image
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            sanitized_name = sanitize_filename(original_name)
            file_path = os.path.join("pokemon_images", f"{sanitized_name}.png")
            with open(file_path, "wb") as f:
                response.raw.decode_content = True  # Handle content-encoding
                shutil.copyfileobj(response.raw, f)
            print(f"Downloaded image for {original_name}")
        else:
            print(f"Failed to download image for {original_name} (HTTP {response.status_code})")
    else:
        print(f"Pokémon '{original_name}' not found in PokéAPI")