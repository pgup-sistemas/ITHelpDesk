import os
import sqlite3
from components.database import init_database

def setup_database():
    """
    Configura o banco de dados SQLite.
    Cria o diretório 'data' se não existir e inicializa o banco de dados.
    """
    # Cria o diretório 'data' se não existir
    os.makedirs('data', exist_ok=True)
    
    # Cria um arquivo vazio .gitkeep no diretório data/
    open('data/.gitkeep', 'a').close()
    
    # Inicializa o banco de dados
    init_database()
    print("✅ Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    setup_database()
