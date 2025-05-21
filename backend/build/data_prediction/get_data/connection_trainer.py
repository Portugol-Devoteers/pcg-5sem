import psycopg

def get_conn_trainer(
    dbname="tcc_b3",
    user="trainer",
    password="postgres",
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
