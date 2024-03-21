# all classification
classification = df["ESGClassification"].unique()[-12:]
number_classification = len(classification)

# Define ESG factors
environment = ['Greenhouse gas emissions', 'Biodiversity','Water', 'Waste', 'Environmental', 
               'Fossil fuels','Energy efficiency', 'Energy efficiency']
social = ['Social and employee matters']
governance = ['Social']

# Define metric of ESG for df_pure
environment_ranking = np.zeros(shape=(number_financial_products, 1))
social_ranking = np.zeros(shape=(number_financial_products, 1))
governance_ranking = np.zeros(shape=(number_financial_products, 1))

# Retrieve the metric values for each ISIN

for i, isin in enumerate(df_pure["ISIN"]):
    # Create the dataframe with only the stock isin
    df_isin = df[ df["ISIN"]== isin]

    for j, classif in enumerate(classification):
        # Create a subcategory desired
        df_isin_class = df_isin[ df_isin["ESGClassification"]== classif]
        # Get the pourcentage for this category
        pourcentage = df_isin_class["ESGClassSymbol"].str.lower().str.contains('yes').mean()
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

df_pure