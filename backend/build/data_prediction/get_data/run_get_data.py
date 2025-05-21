from data_prediction.get_data.dump_price_chunks import dump_price_history_by_company_column
from data_prediction.get_data.dump_financial_statements_chunks import dump_financial_statements_chunks
from data_prediction.get_data.dump_macro_values_chunks import dump_macro_values_chunks
# depois da sua conn estar ativa

def run_get_data():
    dump_price_history_by_company_column()
    dump_financial_statements_chunks()
    dump_macro_values_chunks()
    
if __name__ == "__main__":
    run_get_data()