from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI()

# Dados mockados de Pokémons populares e suas evoluções
POKEMONS = {
    "pikachu": {"xp_base": 112, "evolui_para": "raichu", "xp_necessario": 300},
    "charmander": {"xp_base": 62, "evolui_para": "charmeleon", "xp_necessario": 250},
    "squirtle": {"xp_base": 63, "evolui_para": "wartortle", "xp_necessario": 240},
    "bulbasaur": {"xp_base": 64, "evolui_para": "ivysaur", "xp_necessario": 245},
}

# Modelo de entrada
class TrainingData(BaseModel):
    pokemon: str
    battles: int
    max_recoveries: int
    training_intensity: float  # 0.1 a 1.0 indicando a intensidade do treino

# Função para simular batalha
def simulate_battle(pokemon: str, training_intensity: float):
    if pokemon not in POKEMONS:
        return None
    
    base_xp = POKEMONS[pokemon]["xp_base"]
    xp_gained = int(base_xp * random.uniform(0.5, 1.5) * training_intensity)
    hp_lost = int(20 * random.uniform(0.5, 1.5) * (2 - training_intensity))
    enemy = random.choice(list(POKEMONS.keys()))
    return {"enemy": enemy, "xp_gained": xp_gained, "hp_lost": hp_lost}

@app.post("/train/")
def train_pokemon(data: TrainingData):
    if data.pokemon not in POKEMONS:
        return {"error": "Pokémon não encontrado."}
    
    total_xp = 0
    recoveries = 0
    battles_log = []
    
    for _ in range(data.battles):
        battle = simulate_battle(data.pokemon, data.training_intensity)
        total_xp += battle["xp_gained"]
        battles_log.append(battle)
        
        if len(battles_log) % 3 == 0 and recoveries < data.max_recoveries:
            recoveries += 1  # Recuperação a cada 3 batalhas
    
    evolved_to = None
    if total_xp >= POKEMONS[data.pokemon]["xp_necessario"]:
        evolved_to = POKEMONS[data.pokemon]["evolui_para"]
    
    return {
        "pokemon": data.pokemon,
        "total_xp": total_xp,
        "battles": battles_log,
        "recoveries": recoveries,
        "evolved_to": evolved_to
    }
