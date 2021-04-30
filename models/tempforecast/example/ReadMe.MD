# Intro

This example folder contains a standalone R model, which outputs a forecast for the latest day.

Steps to use this model:

1. Create a folder system with the following names, where mother_folder is your top folder
  - mother_folder: 
    - LatestData
    - Data_model
      - test_run_live
      - test_model: *Save the codes may_...R in this folder*
    
2. Run the Python code Download_Data.py
  - Change the name of the folder where the csv files are saved such that it corresponds to your mother_folder/LatestData folder.

3. Download the R codes in this  folder into your mother_folder
  - Install the packages with the code pasted at the bottom of this page (only needs to be run if you don't have the packages installed) or run may_installpackages.R
  - Change the mother_folder name so it represents the path on your computer in may_main.R
  - Run **may_main.R**
  - The outputs should be three figures forecasting the temperature for the three sensors in the middle of the farm - saved in folder test_run_live






```{r}
install.packages("plyr")
install.packages("ggplot2")
install.packages("lubridate")
install.packages("bsts")
install.packages("dplyr")
install.packages("reshape2")
install.packages("forecast")
`
