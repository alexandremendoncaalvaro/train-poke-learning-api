from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import random
import httpx
import base64
from functools import lru_cache

app = FastAPI()

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    try:
        with httpx.Client(timeout=3) as client:
            response = client.get(f"{POKEAPI_BASE_URL}pokemon/pikachu")
            if response.status_code != 200:
                return {"status": "unhealthy", "details": "Failed to reach PokéAPI"}
    except Exception as e:
        return {"status": "unhealthy", "details": str(e)}
    
    return {"status": "ok"}

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"
SPRITE_BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"

# Modelo de entrada com restrições
class TrainingData(BaseModel):
    pokemon: str
    battles: int = Field(ge=1, le=100, description="Número de batalhas, mínimo 1, máximo 100")
    max_recoveries: int = Field(ge=0, description="Número máximo de recuperações, mínimo 0")
    training_intensity: float = Field(ge=0.1, le=1.0, description="Intensidade do treino, entre 0.1 e 1.0")

# Cache para evitar múltiplas chamadas à API externa
@lru_cache(maxsize=50)
def get_pokemon_data(pokemon: str):
    with httpx.Client() as client:
        response = client.get(f"{POKEAPI_BASE_URL}pokemon/{pokemon.lower()}")
    if response.status_code != 200:
        return None
    return response.json()

@lru_cache(maxsize=50)
def get_pokemon_evolution(pokemon: str):
    with httpx.Client() as client:
        species_response = client.get(f"{POKEAPI_BASE_URL}pokemon-species/{pokemon.lower()}")
    if species_response.status_code != 200:
        return None
    species_data = species_response.json()
    
    evolution_chain_url = species_data["evolution_chain"]["url"]
    with httpx.Client() as client:
        evolution_response = client.get(evolution_chain_url)
    if evolution_response.status_code != 200:
        return None
    return evolution_response.json()

@app.get("/pokemon/{name}/image")
def get_pokemon_image(name: str):
    pokemon_data = get_pokemon_data(name)
    if not pokemon_data:
        return {"error": "Pokémon não encontrado."}
    image_url = f"{SPRITE_BASE_URL}{pokemon_data['id']}.png"
    
    try:
        with httpx.Client() as client:
            image_response = client.get(image_url)
            if image_response.status_code == 200:
                image_base64 = base64.b64encode(image_response.content).decode("utf-8")
                return {"pokemon": name, "image_base64": image_base64}
    except Exception as e:
        return {"error": f"Falha ao obter imagem: {str(e)}"}

    return {"error": "Imagem não encontrada."}

# Função para simular batalha
def simulate_battle(pokemon: str, training_intensity: float):
    pokemon_data = get_pokemon_data(pokemon)
    if not pokemon_data:
        return None
    
    base_xp = pokemon_data["base_experience"]
    xp_gained = int(base_xp * random.uniform(0.3, 1.2) * training_intensity)  # Reduzi a variação para menos XP
    hp_lost = int(20 * random.uniform(0.5, 1.5) * (2 - training_intensity))
    
    all_pokemons = ["pikachu", "charmander", "squirtle", "bulbasaur"]
    enemy = random.choice(all_pokemons)
    return {"enemy": enemy, "xp_gained": xp_gained, "hp_lost": hp_lost}

@app.post("/train/")
def train_pokemon(data: TrainingData):
    pokemon_data = get_pokemon_data(data.pokemon)
    if not pokemon_data:
        return {"error": "Pokémon não encontrado."}
    
    # Ajustar máximo de recuperações dinamicamente
    max_recoveries_allowed = data.battles // 3
    if data.max_recoveries > max_recoveries_allowed:
        return {"error": f"max_recoveries não pode ser maior que {max_recoveries_allowed}."}
    
    total_xp = 0
    recoveries = 0
    battles_log = []
    current_pokemon = data.pokemon
    evolution_data = get_pokemon_evolution(data.pokemon)
    evolution_threshold = 500  # Aumentei o XP necessário para evoluir
    
    for _ in range(data.battles):
        battle = simulate_battle(current_pokemon, data.training_intensity)
        total_xp += battle["xp_gained"]
        battles_log.append(battle)
        
        if len(battles_log) % 3 == 0 and recoveries < data.max_recoveries:
            recoveries += 1  # Recuperação a cada 3 batalhas
        
        # Verificar se atingiu o XP necessário para evolução
        if total_xp >= evolution_threshold and evolution_data:
            chain = evolution_data["chain"]
            current_species = chain
            
            while current_species:
                if current_species["species"]["name"] == current_pokemon.lower():
                    if "evolves_to" in current_species and len(current_species["evolves_to"]) > 0:
                        current_pokemon = current_species["evolves_to"][0]["species"]["name"]
                        evolution_threshold += 600  # Aumentei ainda mais o XP para a próxima evolução
                    break
                current_species = current_species.get("evolves_to", [None])[0]
    
    evolved_pokemon_data = get_pokemon_data(current_pokemon)
    return {
        "pokemon": data.pokemon,
        "pokemon_image": get_pokemon_image(data.pokemon)["image_base64"],
        "final_pokemon": current_pokemon,
        "final_pokemon_image": get_pokemon_image(current_pokemon)["image_base64"] if evolved_pokemon_data else None,
        "total_xp": total_xp,
        "battles": battles_log,
        "recoveries": recoveries
    }
