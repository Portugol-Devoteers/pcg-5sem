import psycopg


conn = psycopg.connect(
    dbname="tcc_b3",
    user="writer",
    password="postgres",  
    host="localhost",
    port="5432"
)