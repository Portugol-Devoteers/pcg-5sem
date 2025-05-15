from config.db import conn


def get_companies_from_db(): 
    """
    Função para obter as empresas da base de dados.
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.b3_code ticker, 
                c.name,
                s.name sector       
            FROM 
                companies c
            JOIN 
                sectors s ON c.sector_id = s.id
        """)
        rows = cursor.fetchall()
        companies = [
            {
                "ticker": row[0],
                "name": row[1],
                "sector": row[2]
            }
            for row in rows
        ]

        
    return companies