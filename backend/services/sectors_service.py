from config.db import conn


def get_sectors_from_db(): 
    """
    Função para obter os setores da base de dados.
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT name FROM sectors")
        rows = cursor.fetchall()
        sectors = [row[0] for row in rows]
    return sectors
