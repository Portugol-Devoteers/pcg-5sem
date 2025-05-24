export interface Statistics {
    general: {
        stats: {
            Hit_rate_percentage: number;
            MAE: number;
            R2: number;
            RMSE: number;
            SMAPE_percentage: number;
            n_obs: number;
        };
    };
    sector: {};
}
