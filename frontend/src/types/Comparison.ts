export interface Comparison {
    short_term: Term[];
    long_term: Term[];
    company_name: string;
}

interface Term {
    error_percent: number;
    model_name: string;
    value: number;
    price_history_value: number;
}
