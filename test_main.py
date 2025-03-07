from fastapi.testclient import TestClient
from main import app  # Certifique-se de importar corretamente sua aplicação

client = TestClient(app)

def test_valid_training():
    response = client.post(
        "/train/",
        json={
            "pokemon": "charmander",
            "battles": 10,
            "max_recoveries": 3,
            "training_intensity": 0.8
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert "pokemon" in data
    assert "final_pokemon" in data
    assert "total_xp" in data
    assert "battles" in data
    assert "recoveries" in data
    assert "pokemon_image" in data
    assert "final_pokemon_image" in data

def test_pokemon_not_found():
    response = client.post(
        "/train/",
        json={
            "pokemon": "missingno",
            "battles": 10,
            "max_recoveries": 3,
            "training_intensity": 0.8
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert "error" in data
    assert data["error"] == "Pokémon não encontrado."

def test_evolution_occurs():
    response = client.post(
        "/train/",
        json={
            "pokemon": "bulbasaur",
            "battles": 50,
            "max_recoveries": 10,
            "training_intensity": 1.0
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["final_pokemon"] != "bulbasaur"  # Deve ter evoluído
    assert "final_pokemon_image" in data

def test_no_evolution():
    response = client.post(
        "/train/",
        json={
            "pokemon": "bulbasaur",
            "battles": 5,
            "max_recoveries": 1,
            "training_intensity": 0.5
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["final_pokemon"] == "bulbasaur"  # Não evolui com poucas batalhas

def test_max_recoveries_validation():
    response = client.post(
        "/train/",
        json={
            "pokemon": "squirtle",
            "battles": 6,
            "max_recoveries": 3,  # Máximo permitido seria 2
            "training_intensity": 0.7
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert "error" in data
    assert "max_recoveries" in data["error"]

def test_invalid_intensity():
    response = client.post(
        "/train/",
        json={
            "pokemon": "pikachu",
            "battles": 10,
            "max_recoveries": 3,
            "training_intensity": 1.5  # Fora do limite permitido
        }
    )
    assert response.status_code == 422  # FastAPI retorna 422 para erro de validação

def test_health_check():
    response = client.get("/health")
    data = response.json()
    assert response.status_code == 200
    assert "status" in data

def test_pokemon_image():
    response = client.get("/pokemon/pikachu/image")
    data = response.json()
    assert response.status_code == 200
    assert "pokemon" in data
    assert "image_url" in data
    assert "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/" in data["image_url"]