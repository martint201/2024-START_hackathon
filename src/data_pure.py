# Python file to retrieve the clean data set

# Packages

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import zipfile
import json
from datetime import datetime

#1  path data
DATA_PATH = "../ESG/"
print(os.listdir(DATA_PATH))

#2 import data
esg_light = "EUESGMANUFACTURER-LIGHT.zip"
esg_light_data = pd.DataFrame()

with zipfile.ZipFile(DATA_PATH + esg_light, 'r') as z:
    for filename in z.namelist():
        if filename.endswith('.csv'):
            with z.open(filename) as f:
                esg_light_data = pd.read_csv(f)


#3 Data cleaning, drop unecessary columns 
columns_to_drop = ["swissValorNumber", "ISIN_BC", "FISN", 
                   "fundManagerSIXCompanyKey", "fundManagerLEI", "fundManagerLongName",
                   "companyDomicileISO", "issuerSIXCompanyKey", "LEI",
                   "ESGFactorDate", "ESGDeliveryDate", "ESGFactor"
                   ]
df = esg_light_data.drop(columns=columns_to_drop)


#4  Obtain first version of pure data set

# Number of financial products
number_financial_products = len(esg_light_data["ISIN"].unique())

# Create ProductType, classification of financial products with their ESG Activity
X = np.zeros(shape=(number_financial_products, 1))

# Create separate list to optimize the search
article_20040 = df[ df['ESGFactorProviderId'] == "20040"]
article_20050 = df[ df['ESGFactorProviderId'] == "20050"]

for i, isin in enumerate(df["ISIN"].unique()):

    X[i] = article_20040.loc[article_20040["ISIN"]== isin, "ESGFactorAmountLastYear"].iloc[0]

    # If the value is 0, it might be a product under miFID
    if X[i] == 0:
        X[i] = article_20050.loc[article_20050["ISIN"]== isin, "ESGFactorAmountLastYear"].iloc[0]

# Flatten X 
X_flat = X.flatten()

# Create a panda frame with the foundamental data
df_pure = pd.DataFrame({
    "ISIN": df["ISIN"].unique(),
    "ProductType": X_flat
})
