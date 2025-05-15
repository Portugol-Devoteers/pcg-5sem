import psycopg


conn = psycopg.connect(
    dbname="tcc_b3",
    user="postgres",
    password="postgres",  # troque se necessário
    host="localhost",
    port="5432"
)