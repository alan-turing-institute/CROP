# Plot results


for (d in 1:daysOfPredictions){

  t2m = result[[d]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
  t2u = result[[d]]$ARIMA$Temperature_FARM_16B1$records[[2]]$measure_values
  t2l = result[[d]]$ARIMA$Temperature_FARM_16B1$records[[3]]$measure_values

  tt = seq(from=forecastDataStart-(d-1)*SECONDS.PERDAY, to=forecastDataStart-(d-2)*SECONDS.PERDAY-1, by="1 hour")
  t2 = (which(t_ee$FarmTime==(forecastDataStart - (d-1)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (d-2)*SECONDS.PERDAY))-1)
  plot(tt,t_ee$Temperature_FARM_16B1[t2], type = "l", col = "blue", main = "Temperature_FARM_16B1", ylim=c(15,30))
  t3 = seq(from=forecastDataStart- (d-1)*SECONDS.PERDAY, to=forecastDataStart-(d-2)*SECONDS.PERDAY-1, by="1 hour")

  lines(t3,t2u,col = "red", lty = 3)
  lines(t3,t2l,col = "red", lty = 3)
  polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
  lines(tt,t_ee$Temperature_FARM_16B1[t2], col = "blue")
  lines(t3,t2m,col = "red", lty = 2)
}

#
# Concatenate in reverse order
#


t5m = result[[5]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t4m = result[[4]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t3m = result[[3]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t2m = result[[2]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t1m = result[[1]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values


test = c(t5m,t4m,t3m,t2m,t1m)

tt = seq(from=forecastDataStart-(5)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2 = (which(t_ee$FarmTime==(forecastDataStart - (5)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
plot(tt,t_ee$Temperature_FARM_16B1[t2], type = "l", col = "blue", main = "Temperature_FARM_16B1", ylim=c(15,30))
t3 = seq(from=forecastDataStart- (5)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")

#lines(t3,t2u,col = "red", lty = 3)
#lines(t3,t2l,col = "red", lty = 3)
#polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_FARM_16B1[t2], col = "blue")
lines(t3,test,col = "red", lty = 2)

test2 = data.frame(t3,test,tt,t_ee$Temperature_FARM_16B1[t2])

#write.csv(test2,"./Farm16B1Oct2021.csv", row.names = FALSE)

ttrain = seq(from=forecastDataStart-(10)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2train = (which(t_ee$FarmTime==(forecastDataStart - (10)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
testtrain = data.frame(ttrain,t_ee$Temperature_FARM_16B1[t2train])
write.csv(testtrain,"./Farm16B1Oct2021train.csv", row.names = FALSE)


##

t5m = result[[5]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t4m = result[[4]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t3m = result[[3]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t2m = result[[2]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t1m = result[[1]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values


test = c(t5m,t4m,t3m,t2m,t1m)

tt = seq(from=forecastDataStart-(5)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2 = (which(t_ee$FarmTime==(forecastDataStart - (5)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
plot(tt,t_ee$Temperature_Farm_16B2[t2], type = "l", col = "blue", main = "Temperature_Farm_16B2", ylim=c(15,30))
t3 = seq(from=forecastDataStart- (5)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")

#lines(t3,t2u,col = "red", lty = 3)
#lines(t3,t2l,col = "red", lty = 3)
#polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_Farm_16B2[t2], col = "blue")
lines(t3,test,col = "red", lty = 2)

test2 = data.frame(t3,test)

#write.csv(test2,"./Farm16B2Oct2021.csv", row.names = FALSE)


##

t5m = result[[5]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t4m = result[[4]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t3m = result[[3]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t2m = result[[2]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t1m = result[[1]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values


test = c(t5m,t4m,t3m,t2m,t1m)

tt = seq(from=forecastDataStart-(5)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2 = (which(t_ee$FarmTime==(forecastDataStart - (5)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
plot(tt,t_ee$Temperature_Farm_16B4[t2], type = "l", col = "blue", main = "Temperature_Farm_16B4", ylim=c(15,30))
t3 = seq(from=forecastDataStart- (5)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")

#lines(t3,t2u,col = "red", lty = 3)
#lines(t3,t2l,col = "red", lty = 3)
#polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_Farm_16B4[t2], col = "blue")
lines(t3,test,col = "red", lty = 2)

test2 = data.frame(t3,test)

#write.csv(test2,"./Farm16B4Oct2021.csv", row.names = FALSE)

##
