import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Chargement des trois fichiers de vols
df1 = pd.read_csv("data/raw/2016_10.csv", low_memory=False)
df2 = pd.read_csv("data/raw/2016_11.csv", low_memory=False)
df3 = pd.read_csv("data/raw/2016_12.csv", low_memory=False)
df = pd.concat([df1, df2, df3])

# Colonnes à supprimer — même liste que dans le notebook E2
colonnes_a_supprimer = [
    'YEAR', 'QUARTER', 'CARRIER', 'ORIGIN_CITY_MARKET_ID', 'ORIGIN_CITY_NAME',
    'DEST_AIRPORT_SEQ_ID', 'DEST_CITY_NAME', 'ORIGIN_STATE_NM', 'FL_DATE',
    'DAY_OF_MONTH', 'DAY_OF_WEEK', 'DEP_DELAY', 'DEP_DELAY_NEW', 'DEP_DEL15',
    'DEP_DELAY_GROUP', 'ARR_TIME', 'ARR_DELAY', 'ORIGIN_AIRPORT_SEQ_ID',
    'DIVERTED', 'DEP_TIME', 'CANCELLED', 'DEST_STATE_ABR', 'ARR_DEL15',
    'ACTUAL_ELAPSED_TIME', 'ARR_DELAY_GROUP', 'WHEELS_ON', 'WHEELS_OFF',
    'AIR_TIME', 'DISTANCE_GROUP'
]

nan_percentage = df.isna().mean() * 100
columns_to_drop = nan_percentage[nan_percentage > 50].index
total_columns_to_drop = list(set(columns_to_drop).union(set(colonnes_a_supprimer)))
df_cleaned = df.drop(columns=total_columns_to_drop, errors='ignore')

cols_to_convert = [
    'DEST_AIRPORT_ID', 'DEST_CITY_MARKET_ID', 'DEST', 'DEST_STATE_NM',
    'DEP_TIME_BLK', 'ARR_TIME_BLK', 'ORIGIN_WAC', 'TAIL_NUM', 'FL_NUM',
    'UNIQUE_CARRIER', 'ORIGIN_AIRPORT_ID', 'ORIGIN_STATE_ABR', 'ORIGIN'
]
df_cleaned[cols_to_convert] = df_cleaned[cols_to_convert].astype(str)
df_cleaned = df_cleaned.drop_duplicates().dropna()

# Suppression de la valeur aberrante et encodage de la compagnie
df_cleaned = df_cleaned[df_cleaned['UNIQUE_CARRIER'] != '10397']
le = LabelEncoder()
df_cleaned['UNIQUE_CARRIER_ENCODED'] = le.fit_transform(df_cleaned['UNIQUE_CARRIER'])

# Variable cible : 1 si retard, 0 sinon
df_cleaned['ARR_DELAY_ENCODED'] = df_cleaned['ARR_DELAY_NEW'].apply(
    lambda x: 1 if x != 0 else 0
)

# Échantillon de 10% pour garder les mêmes conditions que le notebook
df_sampled = df_cleaned.sample(frac=0.1, random_state=42)
numeric_features = df_sampled.select_dtypes(include=['float64', 'int64'])
y = df_sampled['ARR_DELAY_ENCODED']
X = numeric_features.drop(columns=['ARR_DELAY_NEW', 'ARR_DELAY_ENCODED'])
X = X.fillna(X.mean())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Entraînement avec les hyperparamètres optimisés du E2
model = XGBClassifier(
    n_estimators=300,
    max_depth=7,
    learning_rate=0.02,
    min_child_weight=1.5,
    subsample=0.9,
    colsample_bytree=0.9,
    gamma=0.1,
    reg_lambda=1,
    reg_alpha=0.5,
    scale_pos_weight=1,
    random_state=42
)
model.fit(X_train, y_train)

# Sauvegarde du modèle et de la liste des features
joblib.dump(model, "models/xgboost_model.pkl")
joblib.dump(list(X.columns), "models/feature_names.pkl")

print("Modèle sauvegardé dans models/xgboost_model.pkl")
print(f"Features utilisées : {list(X.columns)}")
