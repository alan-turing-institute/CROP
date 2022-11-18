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

t66m = result[[66]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t65m = result[[65]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t64m = result[[64]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t63m = result[[63]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t62m = result[[62]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t61m = result[[61]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t60m = result[[60]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t59m = result[[59]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t58m = result[[58]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t57m = result[[57]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t56m = result[[56]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t55m = result[[55]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t54m = result[[54]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t53m = result[[53]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t52m = result[[52]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t51m = result[[51]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t50m = result[[50]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t49m = result[[49]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t48m = result[[48]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t47m = result[[47]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t46m = result[[46]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t45m = result[[45]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t44m = result[[44]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t43m = result[[43]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t42m = result[[42]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t41m = result[[41]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t40m = result[[40]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t39m = result[[39]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t38m = result[[38]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t37m = result[[37]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t36m = result[[36]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t35m = result[[35]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t34m = result[[34]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t33m = result[[33]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t32m = result[[32]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t31m = result[[31]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t30m = result[[30]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t29m = result[[29]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t28m = result[[28]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t27m = result[[27]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t26m = result[[26]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t25m = result[[25]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t24m = result[[24]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t23m = result[[23]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t22m = result[[22]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t21m = result[[21]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t20m = result[[20]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t19m = result[[19]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t18m = result[[18]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t17m = result[[17]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t16m = result[[16]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t15m = result[[15]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t14m = result[[14]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t13m = result[[13]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t12m = result[[12]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t11m = result[[11]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t10m = result[[10]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t9m = result[[9]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t8m = result[[8]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t7m = result[[7]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t6m = result[[6]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t5m = result[[5]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t4m = result[[4]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t3m = result[[3]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t2m = result[[2]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values
t1m = result[[1]]$ARIMA$Temperature_FARM_16B1$records[[1]]$measure_values


test = c(t66m,t65m,t64m,t63m,t62m,t61m,t60m,t59m,t58m,t57m,t56m,t55m,t54m,t53m,t52m,t51m,t50m,t49m,t48m,t47m,t46m,
         t45m,t44m,t43m,t42m,t41m,t40m,t39m,t38m,t37m,t36m,t35m,t34m,t33m,t32m,t31m,t30m,
         t29m,t28m,t27m,t26m,t25m,t24m,t23m,t22m,t21m,t20m,t19m,t18m,t17m,t16m,t15m,t14m,
         t13m,t12m,t11m,t10m,t9m,t8m,t7m,t6m,t5m,t4m,t3m,t2m,t1m)

tt = seq(from=forecastDataStart-(66)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2 = (which(t_ee$FarmTime==(forecastDataStart - (66)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
plot(tt,t_ee$Temperature_FARM_16B1[t2], type = "l", col = "blue", main = "Temperature_FARM_16B1", ylim=c(15,30))
t3 = seq(from=forecastDataStart- (66)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")

#lines(t3,t2u,col = "red", lty = 3)
#lines(t3,t2l,col = "red", lty = 3)
#polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_FARM_16B1[t2], col = "blue")
lines(t3,test,col = "red", lty = 2)

test2 = data.frame(t3,test)

write.csv(test2,"./Farm16B1May2022.csv", row.names = FALSE)

##
t66m = result[[66]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t65m = result[[65]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t64m = result[[64]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t63m = result[[63]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t62m = result[[62]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t61m = result[[61]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t60m = result[[60]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t59m = result[[59]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t58m = result[[58]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t57m = result[[57]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t56m = result[[56]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t55m = result[[55]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t54m = result[[54]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t53m = result[[53]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t52m = result[[52]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t51m = result[[51]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t50m = result[[50]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t49m = result[[49]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t48m = result[[48]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t47m = result[[47]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t46m = result[[46]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t45m = result[[45]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t44m = result[[44]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t43m = result[[43]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t42m = result[[42]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t41m = result[[41]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t40m = result[[40]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t39m = result[[39]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t38m = result[[38]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t37m = result[[37]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t36m = result[[36]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t35m = result[[35]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t34m = result[[34]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t33m = result[[33]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t32m = result[[32]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t31m = result[[31]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t30m = result[[30]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t29m = result[[29]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t28m = result[[28]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t27m = result[[27]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t26m = result[[26]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t25m = result[[25]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t24m = result[[24]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t23m = result[[23]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t22m = result[[22]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t21m = result[[21]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t20m = result[[20]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t19m = result[[19]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t18m = result[[18]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t17m = result[[17]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t16m = result[[16]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t15m = result[[15]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t14m = result[[14]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t13m = result[[13]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t12m = result[[12]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t11m = result[[11]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t10m = result[[10]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t9m = result[[9]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t8m = result[[8]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t7m = result[[7]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t6m = result[[6]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t5m = result[[5]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t4m = result[[4]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t3m = result[[3]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t2m = result[[2]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values
t1m = result[[1]]$ARIMA$Temperature_Farm_16B2$records[[1]]$measure_values


test = c(t66m,t65m,t64m,t63m,t62m,t61m,t60m,t59m,t58m,t57m,t56m,t55m,t54m,t53m,t52m,t51m,t50m,t49m,t48m,t47m,t46m,
         t45m,t44m,t43m,t42m,t41m,t40m,t39m,t38m,t37m,t36m,t35m,t34m,t33m,t32m,t31m,t30m,
         t29m,t28m,t27m,t26m,t25m,t24m,t23m,t22m,t21m,t20m,t19m,t18m,t17m,t16m,t15m,t14m,
         t13m,t12m,t11m,t10m,t9m,t8m,t7m,t6m,t5m,t4m,t3m,t2m,t1m)

tt = seq(from=forecastDataStart-(66)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2 = (which(t_ee$FarmTime==(forecastDataStart - (66)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
plot(tt,t_ee$Temperature_Farm_16B2[t2], type = "l", col = "blue", main = "Temperature_Farm_16B2", ylim=c(15,30))
t3 = seq(from=forecastDataStart- (66)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")

#lines(t3,t2u,col = "red", lty = 3)
#lines(t3,t2l,col = "red", lty = 3)
#polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_Farm_16B2[t2], col = "blue")
lines(t3,test,col = "red", lty = 2)

test2 = data.frame(t3,test)

write.csv(test2,"./Farm16B2May2022.csv", row.names = FALSE)


##
t66m = result[[66]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t65m = result[[65]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t64m = result[[64]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t63m = result[[63]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t62m = result[[62]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t61m = result[[61]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t60m = result[[60]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t59m = result[[59]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t58m = result[[58]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t57m = result[[57]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t56m = result[[56]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t55m = result[[55]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t54m = result[[54]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t53m = result[[53]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t52m = result[[52]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t51m = result[[51]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t50m = result[[50]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t49m = result[[49]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t48m = result[[48]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t47m = result[[47]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t46m = result[[46]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t45m = result[[45]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t44m = result[[44]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t43m = result[[43]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t42m = result[[42]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t41m = result[[41]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t40m = result[[40]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t39m = result[[39]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t38m = result[[38]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t37m = result[[37]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t36m = result[[36]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t35m = result[[35]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t34m = result[[34]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t33m = result[[33]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t32m = result[[32]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t31m = result[[31]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t30m = result[[30]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t29m = result[[29]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t28m = result[[28]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t27m = result[[27]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t26m = result[[26]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t25m = result[[25]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t24m = result[[24]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t23m = result[[23]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t22m = result[[22]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t21m = result[[21]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t20m = result[[20]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t19m = result[[19]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t18m = result[[18]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t17m = result[[17]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t16m = result[[16]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t15m = result[[15]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t14m = result[[14]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t13m = result[[13]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t12m = result[[12]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t11m = result[[11]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t10m = result[[10]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t9m = result[[9]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t8m = result[[8]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t7m = result[[7]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t6m = result[[6]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t5m = result[[5]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t4m = result[[4]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t3m = result[[3]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t2m = result[[2]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values
t1m = result[[1]]$ARIMA$Temperature_Farm_16B4$records[[1]]$measure_values


test = c(t66m,t65m,t64m,t63m,t62m,t61m,t60m,t59m,t58m,t57m,t56m,t55m,t54m,t53m,t52m,t51m,t50m,t49m,t48m,t47m,t46m,
         t45m,t44m,t43m,t42m,t41m,t40m,t39m,t38m,t37m,t36m,t35m,t34m,t33m,t32m,t31m,t30m,
         t29m,t28m,t27m,t26m,t25m,t24m,t23m,t22m,t21m,t20m,t19m,t18m,t17m,t16m,t15m,t14m,
         t13m,t12m,t11m,t10m,t9m,t8m,t7m,t6m,t5m,t4m,t3m,t2m,t1m)

tt = seq(from=forecastDataStart-(66)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")
t2 = (which(t_ee$FarmTime==(forecastDataStart - (66)*SECONDS.PERDAY ))):(which(t_ee$FarmTime==(forecastDataStart- (0)*SECONDS.PERDAY))-1)
plot(tt,t_ee$Temperature_Farm_16B4[t2], type = "l", col = "blue", main = "Temperature_Farm_16B4", ylim=c(15,30))
t3 = seq(from=forecastDataStart- (66)*SECONDS.PERDAY, to=forecastDataStart-(0)*SECONDS.PERDAY-1, by="1 hour")

#lines(t3,t2u,col = "red", lty = 3)
#lines(t3,t2l,col = "red", lty = 3)
#polygon(c(t3, rev(t3)), c(t2l, rev(t2u)), col = "mistyrose1", lty=0)
lines(tt,t_ee$Temperature_Farm_16B4[t2], col = "blue")
lines(t3,test,col = "red", lty = 2)

test2 = data.frame(t3,test)

write.csv(test2,"./Farm16B4May2022.csv", row.names = FALSE)

##
