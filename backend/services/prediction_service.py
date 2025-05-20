from collections import defaultdict
from config.db import conn

def get_prediction_from_db(ticker: str):
    """
    Retorna as previsões formatadas para gráfico,
    começando a partir da primeira data com valor real.
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.date,
                p.model_id,
                p.value,
                m.model,
                ph.close AS real
            FROM 
                predictions p
            LEFT JOIN 
                models m ON p.model_id = m.id
            LEFT JOIN 
                price_history ph ON p.date = ph.date AND ph.company_id = p.b3_code_id
            LEFT JOIN
                companies c ON p.b3_code_id = c.id
            WHERE 
                c.b3_code = %s
            ORDER BY 
                p.date ASC;
        """, (ticker,))
        rows = cursor.fetchall()

    grouped = defaultdict(dict)

    for row in rows:
        data_formatada = row[0].strftime("%d/%m/%Y")
        model_name = row[3].lower()
        valor_previsto = float(row[2])
        valor_real = row[4]

        if valor_real is not None:
            grouped[data_formatada]["real"] = float(valor_real)
            
        grouped[data_formatada]["date"] = data_formatada
        grouped[data_formatada][model_name] = valor_previsto


    # ⚠️ Ignorar datas anteriores à primeira com valor "real"
    valores = list(grouped.values())
    inicio_real = next((i for i, item in enumerate(valores) if "real" in item), 0)

    return valores[inicio_real:]
