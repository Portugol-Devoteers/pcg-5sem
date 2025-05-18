import psycopg

def get_conn(
    dbname="tcc_b3",
    user="trainer",
    password="postgresql",
    host="localhost",
    port="5432"
):
    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
