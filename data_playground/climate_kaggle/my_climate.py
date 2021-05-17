import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats
from sklearn.linear_model import LinearRegression

def read_data(folder_name='..', what='cities', verbose=False):
    """Reads either city or country data from a properly named CSV in the target folder.

    folder_name (str): where to read from
    what (str): either 'cities' or 'countries', for a respective dataset
    verbose (bool): whether encouraging debugging info should be displayed
    """
    if what=='cities':
        file_name = 'GlobalLandTemperaturesByCity.csv'
    elif what=='countries':
        file_name = 'GlobalLandTemperaturesByCountry.csv'
    else:
        raise(ValueError("Dataset type should be either 'cities' or 'countries'."))
    if verbose:
        print(f"About to read from {folder_name + file_name}")
    df = pd.read_csv(folder_name + file_name)
    if verbose:
        print(f"Read successfully. Brushing the data up a bit.")
    df = df.assign(Date=pd.to_datetime(df.dt))
    df = (df
          .assign(Year=df.Date.dt.year)
          .assign(Month=df.Date.dt.month)
          )
    return df

def clean_data(df, first_date='1900-01-01', last_date='2013-01-01'):
    """Returns the part of the dataset between two dates; removes all NaNs.

    df:         the Dataframe to process
    first_date: first date to include
    last_date:  first date to NOT include (no dates >= this one will be included)
    """
    dfs = (df
           .query('dt >= @first_date & dt < @last_date')
           .query('AverageTemperature.notna()', engine='python')
           )
    if dfs.shape[0]==0  :
        raise(AttributeError("We have no data for this date range."))
    return dfs

def top_variable_cities(df, n, first_date='1900-01-01', last_date='2013-01-01', verbose=False):
    """Finds top n cities with highest temperature variability; returns an array of names.

    inputs:
        df:         cities dataframe
        n (int):    how many cities to find (doesn't check for cities with identical data!)
        first_date (string, optional):  earliest date to include in the analysis (format '1900-01-01')
        last_date (string, optional):   earliest date to exclude from the analysis (same format)
        verbose (bool): if stats for these cities are to be displayed

    returns: numpy array of strings (city names)
    """
    dfs = clean_data(df, first_date, last_date)
    beta = scipy.stats.t.ppf(1 - 0.025, df=29)  # Approximately 2
    dfs = (dfs
           .assign(Within_var=(dfs.AverageTemperatureUncertainty / beta * np.sqrt(30)) ** 2)
           .groupby('City')
           .agg({'AverageTemperature': 'var', 'Within_var': 'mean'})
           .reset_index()
           .set_axis(['City', 'Between_var', 'Within_var'], axis=1, inplace=False)
           .assign(SD_full=lambda x: np.sqrt(x.Between_var + x.Within_var))
           .sort_values('SD_full', ascending=False)
           .head(n)
           )
    if verbose:
        print(dfs)
    return dfs.City.values

def plot_cities(df, cities, first_date='1900-01-01', last_date='2013-01-01', save_png=False):
    """Displays per-decade averages and uncertainties for a list of cities.

    df: Dataframe with cities data
    cities: an interable of city names (strings)
    first_date (string, optional): earliest date to include in the analysis (default '1900-01-01')
    last_date (string, optional): earliest date to exclude from the analysis (default '2013-01-01)
    save_png (bool): if png is to be saved (default False)
    """
    df = clean_data(df, first_date, last_date)
    beta30 = scipy.stats.t.ppf(1 - 0.025, df=29)  # Approximately 2
    beta10 = scipy.stats.t.ppf(1 - 0.025, df=9)
    beta100 = scipy.stats.t.ppf(1 - 0.025, df=99)
    view = (df
            .query('City in @cities')
            .query('AverageTemperature.notna()', engine='python')
            )

    view_monthly = (view
                    .assign(Month=df.Date.dt.month)
                    .assign(Var_within=np.square(df.AverageTemperatureUncertainty / beta30))  # SEM squared
                    .groupby(['Month', 'City'])
                    .agg({'AverageTemperature': 'mean', 'Var_within': 'mean'})
                    .reset_index()
                    .set_axis(['Month', 'City', 'Mean_mo', 'Var_within'], axis=1, inplace=False)
                    )

    gross_averages = view_monthly.groupby('City').agg({'Mean_mo': 'mean'})

    view_yearly = (view
                   .assign(Decade=(df.Date.dt.year // 10) * 10)
                   .assign(Month=df.Date.dt.month)
                   .assign(Var_within=np.square(df.AverageTemperatureUncertainty / beta30))
                   .merge(view_monthly,  # Prepare to remove cyclicity
                          how='left',
                          on=['City', 'Month'],
                          suffixes=[None, '_m'])
                   .merge(gross_averages,
                          how='left',
                          on='City',
                          suffixes=[None, '_s'])
                   )
    view_yearly.AverageTemperature -= view_yearly.Mean_mo - view_yearly.Mean_mo_s  # Remove cyclicity
    view_yearly = (view_yearly
                   .groupby(['Decade', 'City'])
                   .agg({'AverageTemperature': ['mean', 'var'], 'Var_within': 'mean'})
                   .reset_index()
                   .set_axis(['Decade', 'City', 'Mean', 'Var_between', 'Var_within'], axis=1, inplace=False)
                   )
    view_yearly['Error'] = np.sqrt(view_yearly.Var_between +
                                   view_yearly.Var_within) / np.sqrt(10) * beta10

    # No pivoting this time around, as it's easier to plot uncertainty manually,
    # so long shape data is preferable.

    best_sequence = np.argsort(gross_averages.Mean_mo.values)
    cities = gross_averages.index[best_sequence[::-1]]  # We want to reverse the order

    plt.figure(figsize=(12, 5), facecolor='white')
    plt.subplot(121)
    for city in cities:
        subview = view_yearly.query('City == @city')
        plt.fill_between(subview.Decade + 5,
                         subview.Mean - subview.Error, subview.Mean + subview.Error, alpha=0.1)
        plt.plot(subview.Decade + 5, subview.Mean, '-', label=city)
        # Shift x by 5 years, to make it end at 2005, as we averaged up to 2010
    plt.xlabel('Decade')
    plt.ylabel('Average temperature, °C')
    plt.legend(loc='upper left', frameon=False)

    plt.subplot(122)
    for city in cities:
        subview = view_monthly.query('City == @city')
        plt.fill_between(subview.Month,
                         subview.Mean_mo - np.sqrt(subview.Var_within) / 10 * beta100,
                         subview.Mean_mo + np.sqrt(subview.Var_within) / 10 * beta100, alpha=0.1)
        plt.plot(subview.Month, subview.Mean_mo, '-', label=city)
        plt.xlabel('Month')
        plt.ylabel('Average temperature, °C')
    plt.legend(loc='upper left', frameon=False)

    if save_png:
        out_file_name = f"{len(cities):d}_top_cities.png"
        plt.gcf().savefig(out_file_name, dpi=150)
        print(f"PNG file saved as {out_file_name}")
    return

def predict_climate(df, city, date_training_left='1900-01-01', date_training_right='2013-01-01',
                    date_prediction_left='2013-01-01', date_prediction_right='2014-01-01'):
    """
    Predicts monthly temperatures for a given city.

    Inputs:
        df: dataframe of cities data
        city (str): city name
        date_training_left: start of the training dataset (default '1900-01-01')
        date_training_right: end of the training dateset, exclusive (default '2013-01-01')
        date_prediction_left: start of the prediction period (default '2013-01-01')
        date_prediction_right: end of the prediction period, inclusive  (default '2013-12-01').

    Returns: a dataframe with monthly dates and predicted average monthly temperatures.
    """

    def add_dummy_months(df):
        # Adds dummy variables for months
        for i in range(12):
            df[f"m{i + 1:02d}"] = (df.Date.dt.month == (i + 1)).astype(int)
        return df

    dfc = df.query('City==@city')
    dfc = clean_data(dfc, date_training_left, date_training_right)

    prediction_first_day = pd.to_datetime(date_prediction_left)
    prediction_last_day = pd.to_datetime(date_prediction_right)

    target_days = pd.DataFrame({'Date': pd.date_range(prediction_first_day,
                                                      prediction_last_day,
                                                      freq=pd.offsets.MonthBegin(1))})
    target_days['Year'] = target_days.Date.dt.year
    target_days = add_dummy_months(target_days)
    target_days['Y2'] = np.square(target_days.Year)

    view = dfc.query('City == @city').copy()
    view = add_dummy_months(view)
    view['Y2'] = np.square(view.Year)

    X = view.iloc[:, [i for i in range(view.shape[1]) if view.columns[i] in target_days.columns]]
    X = X.drop(columns=['Date']).values
    y = view.AverageTemperature.values

    reg = LinearRegression().fit(X, y)
    out = reg.predict(target_days.drop(columns=['Date']).values)
    return pd.DataFrame({'Date': target_days.Date, 'AverageTemperature': out})

def prediction_plot(df, city, prediction):
    """
    Plots the most recent history of temperature in a city, together with the prediction.

    df:         city temperature dataframe
    city:       city name (string)
    prediction: prediction calculated by the predict_climate() function
    """
    view = (df
            .query('City == @city')
            .query('AverageTemperature.notna()', engine='python')
            )
    max_date = view.Date.max()
    plot_range_left = max_date - pd.DateOffset(years=3)
    view = view.query('Date >= @plot_range_left')

    plt.figure(figsize=(12, 2))
    plt.plot(view.Date, view.AverageTemperature)
    plt.plot(prediction.Date, prediction.AverageTemperature)
    plt.xlabel('Date')
    plt.ylabel('Average temperature, °C')
    plt.title(city)
    plt.legend(labels=['Actuals', 'Prediction'], loc='upper left')
    return
