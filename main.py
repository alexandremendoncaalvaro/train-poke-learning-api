from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import random
import httpx
import base64
from functools import lru_cache

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

class TrainingData(BaseModel):
    pokemon: str
    epochs: int = Field(ge=1, le=50)
    batch_size: int = Field(ge=1, le=10)
    learning_rate: float = Field(ge=0.01, le=1.0)
    optimizer: str
    early_stopping: bool = Field(default=False)

@lru_cache(maxsize=50)
def get_pokemon_data(pokemon: str):
    with httpx.Client() as client:
        response = client.get(f"{POKEAPI_BASE_URL}pokemon/{pokemon.lower()}")
    if response.status_code != 200:
        return None
    return response.json()

@lru_cache(maxsize=50)
def get_evolution_chain(pokemon: str):
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

@app.get("/pokemon")
def list_pokemon(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    with httpx.Client() as client:
        response = client.get(f"{POKEAPI_BASE_URL}pokemon?limit={limit}&offset={offset}")
        if response.status_code != 200:
            return {"error": "Não foi possível obter a lista de Pokémon."}
    
    data = response.json()
    pokemons = [
        {
            "name": pokemon["name"],
            "image_url": f"{SPRITE_BASE_URL}{pokemon['url'].split('/')[-2]}.png"
        }
        for pokemon in data["results"]
    ]
    
    return {
        "count": data["count"],
        "next": data["next"],
        "previous": data["previous"],
        "pokemons": pokemons
    }

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

@app.post("/train/")
def train_pokemon(data: TrainingData):
    pokemon_data = get_pokemon_data(data.pokemon)
    if not pokemon_data:
        return {"error": "Pokémon não encontrado."}
    
    total_xp = 0
    battles_log = []
    current_pokemon = data.pokemon
    evolution_threshold = 500
    evolution_data = get_evolution_chain(current_pokemon)
    
    for epoch in range(data.epochs):
        for _ in range(data.batch_size):
            battle_xp = int(pokemon_data["base_experience"] * data.learning_rate * random.uniform(0.5, 1.5))
            total_xp += battle_xp
            battles_log.append({"epoch": epoch + 1, "xp_gained": battle_xp})
            
            if total_xp >= evolution_threshold and evolution_data:
                chain = evolution_data["chain"]
                current_species = chain
                while current_species:
                    if current_species["species"]["name"] == current_pokemon:
                        if "evolves_to" in current_species and len(current_species["evolves_to"]) > 0:
                            current_pokemon = current_species["evolves_to"][0]["species"]["name"]
                            evolution_threshold += 600
                        break
                    current_species = current_species.get("evolves_to", [None])[0]
            
        if data.early_stopping and total_xp >= evolution_threshold:
            break
    
    return {
        "pokemon": data.pokemon,
        "final_pokemon": current_pokemon,
        "total_xp": total_xp,
        "battles": battles_log,
        "optimizer": data.optimizer,
        "learning_rate": data.learning_rate
    }
