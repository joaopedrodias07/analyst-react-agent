import sqlite3
import random
from datetime import datetime, timedelta


def create_database():
    # Conecta ao banco — se não existir, cria o arquivo automaticamente
    conn = sqlite3.connect("data/vendas.db")
    cursor = conn.cursor()
    # cursor é o "lápis" que escreve no banco

    # ── DIMENSÕES ──────────────────────────────────────────

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_produtos (
            id_produto   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome         TEXT NOT NULL,
            categoria    TEXT NOT NULL,
            preco_unitario REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL,
            sexo       TEXT NOT NULL,
            idade      INTEGER NOT NULL,
            email      TEXT NOT NULL,
            regiao     TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_vendedores (
            id_vendedor INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            email       TEXT NOT NULL,
            regiao      TEXT NOT NULL,
            cargo       TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fato_vendas (
            id_venda    INTEGER PRIMARY KEY AUTOINCREMENT,
            id_produto  INTEGER NOT NULL,
            id_cliente  INTEGER NOT NULL,
            id_vendedor INTEGER NOT NULL,
            data        TEXT NOT NULL,
            quantidade  INTEGER NOT NULL,
            valor_total REAL NOT NULL,
            desconto    REAL NOT NULL,
            FOREIGN KEY (id_produto)  REFERENCES dim_produtos(id_produto),
            FOREIGN KEY (id_cliente)  REFERENCES dim_clientes(id_cliente),
            FOREIGN KEY (id_vendedor) REFERENCES dim_vendedores(id_vendedor)
        )
    """)

    # ── DADOS FICTÍCIOS ─────────────────────────────────────

    produtos = [
        ("Software Analytics", "Software", 299.90),
        ("Software CRM",       "Software", 199.90),
        ("Hardware Server",    "Hardware", 4500.00),
        ("Hardware Workstation", "Hardware", 3200.00),
        ("Consultoria BI",     "Serviço",  850.00),
    ]

    # executemany insere várias linhas de uma vez
    cursor.executemany("""
        INSERT INTO dim_produtos (nome, categoria, preco_unitario)
        VALUES (?, ?, ?)
    """, produtos)

    nomes_clientes = ["Ana Lima", "Bruno Souza", "Carla Dias",
                      "Diego Melo", "Elena Costa", "Felipe Rocha",
                      "Gabi Nunes", "Hugo Pires", "Iris Moura", "João Vitor"]

    sexos = ["M", "F"]
    regioes = ["Sul", "Norte", "Sudeste", "Nordeste", "Centro-Oeste"]

    clientes = [
        (
            nome,
            random.choice(sexos),
            random.randint(20, 60),
            f"{nome.lower().replace(' ', '.')}@email.com",
            random.choice(regioes)
        )
        for nome in nomes_clientes
    ]

    cursor.executemany("""
        INSERT INTO dim_clientes (nome, sexo, idade, email, regiao)
        VALUES (?, ?, ?, ?, ?)
    """, clientes)

    vendedores = [
        ("Ana Silva",    "ana.silva@empresa.com",    "Sudeste", "Sênior"),
        ("Bruno Costa",  "bruno.costa@empresa.com",  "Sul",     "Pleno"),
        ("Carla Mendes", "carla.mendes@empresa.com", "Norte",   "Júnior"),
        ("Diego Rocha",  "diego.rocha@empresa.com",  "Nordeste", "Sênior"),
    ]

    cursor.executemany("""
        INSERT INTO dim_vendedores (nome, email, regiao, cargo)
        VALUES (?, ?, ?, ?)
    """, vendedores)

    # ── FATO VENDAS ─────────────────────────────────────────

    data_inicio = datetime(2024, 1, 1)

    vendas = []
    for _ in range(500):  # 500 registros de vendas
        produto_id = random.randint(1, len(produtos))
        cliente_id = random.randint(1, len(clientes))
        vendedor_id = random.randint(1, len(vendedores))
        data = data_inicio + timedelta(days=random.randint(0, 364))
        quantidade = random.randint(1, 20)
        preco = produtos[produto_id - 1][2]  # pega o preço do produto
        desconto = round(random.uniform(0, 0.20), 2)  # 0% a 20%
        valor_total = round(preco * quantidade * (1 - desconto), 2)

        vendas.append((
            produto_id, cliente_id, vendedor_id,
            data.strftime("%Y-%m-%d"),
            quantidade, valor_total, desconto
        ))

    cursor.executemany("""
        INSERT INTO fato_vendas 
        (id_produto, id_cliente, id_vendedor, data, quantidade, valor_total, desconto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, vendas)

    # Salva tudo no banco — sem isso nada é persistido!
    conn.commit()
    conn.close()
    print("Banco criado com sucesso!")


if __name__ == "__main__":
    create_database()
