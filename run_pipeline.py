from src.data_ingestion import load_raw_data, basic_cleaning
from src.feature_engineering import add_handcrafted_features, save_processed_data
from src.modeling import train_models
from src.insights import label_clusters
from src.config import PROCESSED_DATA_PATH


def main():
    df_raw = load_raw_data()
    df_clean = basic_cleaning(df_raw)

    df_fe = add_handcrafted_features(df_clean)
    save_processed_data(df_fe)

    models, df_with_labels = train_models(df_clean)
    df_with_labels = label_clusters(df_with_labels)

    df_with_labels.to_parquet(PROCESSED_DATA_PATH, index=False)
    print("Pipeline completed. Processed data saved at:", PROCESSED_DATA_PATH)


if __name__ == "__main__":
    main()
