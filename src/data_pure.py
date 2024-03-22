# Python file to retrieve the clean data set

# Packages

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import zipfile
import json
from datetime import datetime


def get_clean_data_esg(esg_data):
    # # 1  path data
    # DATA_PATH = "../ESG/"
    # print(os.listdir(DATA_PATH))

    # # 2 import data
    # esg_light = "EUESGMANUFACTURER-LIGHT.zip"
    # esg_light_data = pd.DataFrame()

    # with zipfile.ZipFile(DATA_PATH + esg_light, "r") as z:
    #     for filename in z.namelist():
    #         if filename.endswith(".csv"):
    #             with z.open(filename) as f:
    #                 esg_light_data = pd.read_csv(f)

    # 3 Data cleaning, drop unecessary columns
    columns_to_drop = [
        "swissValorNumber",
        "ISIN_BC",
        "FISN",
        "fundManagerSIXCompanyKey",
        "fundManagerLEI",
        "fundManagerLongName",
        "companyDomicileISO",
        "issuerSIXCompanyKey",
        "LEI",
        "ESGFactorDate",
        "ESGDeliveryDate",
        "ESGFactor",
    ]
    df = esg_data.drop(columns=columns_to_drop)

    # 4  Obtain first version of pure data set

    # Number of financial products
    number_financial_products = len(esg_data["ISIN"].unique())

    # Create ProductType, classification of financial products with their ESG Activity
    X = np.zeros(shape=(number_financial_products, 1))

    # Create separate list to optimize the search
    article_20040 = df[df["ESGFactorProviderId"] == "20040"]
    article_20050 = df[df["ESGFactorProviderId"] == "20050"]

    for i, isin in enumerate(df["ISIN"].unique()):

        X[i] = article_20040.loc[
            article_20040["ISIN"] == isin, "ESGFactorAmountLastYear"
        ].iloc[0]

        # If the value is 0, it might be a product under miFID
        if X[i] == 0:
            X[i] = article_20050.loc[
                article_20050["ISIN"] == isin, "ESGFactorAmountLastYear"
            ].iloc[0]

    # Flatten X
    X_flat = X.flatten()

    # Create a panda frame with the foundamental data
    df_pure = pd.DataFrame({"ISIN": df["ISIN"].unique(), "ProductType": X_flat})

    # all classification
    classification = df["ESGClassification"].unique()[-12:]
    number_classification = len(classification)

    # Define ESG factors
    environment = [
        "Greenhouse gas emissions",
        "Biodiversity",
        "Water",
        "Waste",
        "Environmental",
        "Fossil fuels",
        "Energy efficiency",
        "Energy efficiency",
    ]
    social = ["Social and employee matters"]
    governance = ["Social"]

    number_financial_products = len(esg_data["ISIN"].unique())

    # Define metric of ESG for df_pure
    environment_ranking = np.zeros(shape=(number_financial_products, 1))
    social_ranking = np.zeros(shape=(number_financial_products, 1))
    governance_ranking = np.zeros(shape=(number_financial_products, 1))

    # Retrieve the metric values for each ISIN

    for i, isin in enumerate(df_pure["ISIN"]):
        # Create the dataframe with only the stock isin
        df_isin = df[df["ISIN"] == isin]

        for j, classif in enumerate(classification):
            # Create a subcategory desired
            df_isin_class = df_isin[df_isin["ESGClassification"] == classif]
            # Get the pourcentage for this category
            pourcentage = (
                df_isin_class["ESGClassSymbol"].str.lower().str.contains("yes").mean()
            )
            if classif in environment:
                environment_ranking[i] += pourcentage
            elif classif in social:
                social_ranking[i] = pourcentage
            elif classif in governance:
                governance_ranking[i] = pourcentage

    # Mean for the number of factors
    environment_ranking = environment_ranking / len(environment)
    social_ranking = social_ranking / len(social)
    governance_ranking = governance_ranking / len(governance)

    # Make the assumption that if it is nan it is 0

    environment_ranking_no_nan = np.nan_to_num(environment_ranking)
    social_ranking_no_nan = np.nan_to_num(social_ranking)
    governance_ranking_no_nan = np.nan_to_num(governance_ranking)

    # Put the new data
    df_pure["Environment"] = environment_ranking_no_nan
    df_pure["Social"] = social_ranking_no_nan
    df_pure["Governance"] = governance_ranking_no_nan

    return df_pure
