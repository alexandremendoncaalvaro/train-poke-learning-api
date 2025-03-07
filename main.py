from fastapi import FastAPI, Query
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

@app.get("/pokemon")
def list_pokemon(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Lista os Pokémon com paginação."""
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
