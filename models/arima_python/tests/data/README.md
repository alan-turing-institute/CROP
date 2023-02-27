
## Airline Dataset
The file `airline_dataset_arima.pkl` contains an airline dataset downloaded from: 'https://www.stata-press.com/data/r12/air2.dta'.
It is used to test the ARIMA code.
A seasonal ARIMA time series model is fit to the data, with non-seasonal order = (2, 1, 0) and seasonal order = (1, 1, 0, 12).
Details can be found in this notebook: `../../prepare_airline_dataset.ipynb`.

More specifically, the pickle file contains a dictionary with keys:
 - `dataset`: the airline dataset/time-series, as a pandas DataFrame
 - `predictions`: in-sample predictions of the ARIMA model fitted using train data (the first 80% of the airline time-series), as a pandas Series
 - `forecasts`: out-of-sample forecasts of the test data (the last 20% of the airline time-series), as a pandas DataFrame
 - `train_index`: a list containing the indeces of the observations of the airline time-series used for model training
 - `test_index`: a list containing the indeces of the observations of the airline time-series used for model testing
 - `rmse_forecasts`: the root-mean-square-error of the forecasts of test data
 - `r2_forecasts`: the R2 score of the forecasts of test data
