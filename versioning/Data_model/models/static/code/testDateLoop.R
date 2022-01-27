get_date_days_ago = function(numDays = 1, today = "2021-06-14 04:00:00 GMT") {
  today = as.POSIXct(today)
  today - (numDays*SECONDS.PERDAY)
} 

daysOfPredictions = 5
for (d in 1:DaysOfPredictions){
  print (get_date_days_ago(numDays=d))
}
