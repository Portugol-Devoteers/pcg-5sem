from config.db import conn

def get_prediction_from_db(company_id: int):
    """
    Função para obter as previsões da base de dados.
    """
    # with conn.cursor() as cursor:
    #     cursor.execute("""
    #         SELECT 
    #             p.date,
    #             p.value,
    #             m.model
    #         FROM 
    #             predictions p 
    #         JOIN models m ON p.model_id = m.id
    #         WHERE 
    #             p.company_id = %s
    #     """)
    #     cursor.execute((company_id,))
    #     rows = cursor.fetchall()
    #     predictions = []
    #     for row in rows:
    #         prediction = {
    #             "date": row[0],
    #             "value": row[1],
    #             "model": row[2]
    #         }
    #         predictions.append(prediction)
    # return predictions