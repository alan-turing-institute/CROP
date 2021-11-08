# all functions required to run model
# 
constructLights <- function(tobj){
  # lights typically come on at 4pm. So a farm cycle starts at 4pm. This algortihm identifies the likely time that the lights came on in the farm.
  tobj$FarmDateNew <- as.Date(tobj$FarmTime - 16*60*60)
  #tobjmean <- (tobj %>% group_by(FarmDateNew) %>% dplyr::summarise(meanE=mean(EnergyCP, na.rm=TRUE)))
  tobjmean <- (tobj %>% group_by(FarmDateNew) %>% dplyr::summarise(meanE=mean(EnergyCP)))
  tobj$Lights <- rep(0, length(tobj$FarmDateNew))
  
  ii = 4768
  tobj$EnergyCP[ii] > 0.9*tobjmean[which(tobjmean$FarmDateNew==tobj$FarmDateNew[ii]),2]
  # identify rows where energyCP 
  for(ii in 1:length(tobj$Lights)){
    print(ii)
    if(tobj$EnergyCP[ii] > 0.9*tobjmean[which(tobjmean$FarmDateNew==tobj$FarmDateNew[ii]),2]){
      if(tobj$EnergyCP[ii] >15){
        tobj$Lights[ii] <- 1
      }
    }
  }
  for(tt in 2:(length(tobj$Lights)-1)){
    if((tobj$Lights[tt]==0)&(tobj$Lights[tt+1]==1)){
      #current off, next one on
      ldif2 <- tobj$EnergyCP[tt+1] - tobj$EnergyCP[tt]
      ldif1 <- tobj$EnergyCP[tt] - tobj$EnergyCP[tt-1]
      if(0.6*ldif2<ldif1){
        tobj$Lights[tt] <- 1
      }
    }
  }
  return(tobj$Lights)
}


fill_data<-function(tobj){
  # the aim of this function is to add typical values for the time of month and year if there is missing data
  # this is a rapid way of filling in missing data but it requires the old dataset to be loaded. can be changed after another year of sensing.
  my_time <- data.frame(FarmTime = seq(from=min(tobj$FarmTime), to=max(tobj$FarmTime),by="1 hour"))
  tobj <- left_join(my_time, tobj)
  tobj$Hour <- hour(tobj$FarmTime)
  tobj$Month <- month(tobj$FarmTime)
  tobj$WeekDay <- weekdays(tobj$FarmTime)
  
  tobj<-tobj %>% group_by(Month, Hour,WeekDay) %>%
    mutate(
      TypE= mean(EnergyCP,na.rm = T),
      TypT=mean(Sensor_temp, na.rm = T)
    )
  
  tobj$EnergyCP<- ifelse(is.na(tobj$EnergyCP), tobj$TypE,tobj$EnergyCP )
  tobj$Sensor_temp<- ifelse(is.na(tobj$Sensor_temp), tobj$TypT,tobj$Sensor_temp )
  
  tobj$Lights <- constructLights(tobj)
  return(tobj)
}

fill_data_mean = function(tobj){
  # the aim of this function is to add typical values for the time of month and year if there is missing data
  # this is a rapid way of filling in missing data but it requires the old dataset to be loaded. can be changed after another year of sensing.
  my_time <- data.frame(FarmTime = seq(from=min(tobj$FarmTime), to=max(tobj$FarmTime),by="1 hour"))
  tobj <- left_join(my_time, tobj)
  tobj$Hour <- hour(tobj$FarmTime)
  tobj$Month <- month(tobj$FarmTime)
  tobj$WeekDay <- weekdays(tobj$FarmTime)
  
  tobj = tobj %>% group_by(Month, Hour,WeekDay)
  TypE = mean(tobj$EnergyCP,na.rm = T)
  TypT = mean(tobj$Sensor_temp,na.rm = T)
  
  tobj$EnergyCP<- ifelse(is.na(tobj$EnergyCP), TypE,tobj$EnergyCP )
  tobj$Sensor_temp<- ifelse(is.na(tobj$Sensor_temp), TypT,tobj$Sensor_temp )
  
  tobj$Lights <- constructLights(tobj)
  return(tobj)
}


runbsts_live <- function(starttm, testtm, tobj,sensor_name){


  
  print("Selecting data")

  #tsel is selection from start to end of forecasting period
  tsel <- dplyr::filter(tobj, FarmTime >= (starttm) & FarmTime <= (testtm+48*60*60))

  fullcov <- constructCov(tsel$Lights, tsel$FarmTime)
  # indices for training
  trainsel <- 1:(which(tsel$FarmTime==(testtm))-1)
  # indices for forecasting
  testsel <-rep((which(tsel$FarmTime==(testtm))-24):(which(tsel$FarmTime==(testtm))-1),2)
  
  ## Dynamic model --
  print("Training the dynamic model")
  
  
  mc <- list()
  mc <- AddLocalLevel(mc, y=tsel$Sensor_temp[trainsel])
  mc <- AddDynamicRegression(mc, tsel$Sensor_temp[trainsel]~fullcov[trainsel,-c(26)]) #remove the hour that usually happens before the lights are on
  #this centres the mean towards the lower part of the day so the model is easier to explain
  dynamic_fit <<- bsts(tsel$Sensor_temp[trainsel], mc, niter=1000) #iter 1000
  
  
  filename <- paste("dynamic_fit_",sensor_name,"_",as.Date(testtm), ".RDS", sep="")
  save(dynamic_fit, file=filename)
  
  ## Static model --
  print("Training the Static model")

    predarima3 <- try(Arima(tsel$Sensor_temp[trainsel], xreg =  tsel$Lights[trainsel],
                          order = c(4,1,2),
                          seasonal = list(order=c(1,1,0),period=24),method = "CSS"))

  # Making the forecasts
  print("Generating the 24hour forecast")
  
  newcovtyp <- constructCovTyp(tsel$FarmTime[testsel])
  predtyp <- predict(dynamic_fit, burn=200, newdata=newcovtyp[,-c(26)],48) #burn 200
  
  pred_412_L <- forecast(predarima3,xreg= tsel$Lights[testsel],h=48)
  
  
save_pred <- list(predtyp, pred_412_L)
return(save_pred)

}


print_warning_message <- function(stats_save){
  message(paste0("Based on the conditions yesterday, in the next 24 hours: \n \n",
                 "There is a ",stats_save$h24_p*100,"% probabibility that it will be over 25degC for ",stats_save$h24,"h. \n",
                 "There is a ",stats_save$h18_p*100,"% probabibility that it will be under 17degC for ",stats_save$h18,"h.\n"))
  
  save_message<-paste("Based on the conditions yesterday, in the next 24 hours: \n \n",
                      "There is a ",stats_save$h24_p*100,"% probabibility that it will be over 25degC for ",stats_save$h24,"h. \n",
                      "There is a ",stats_save$h18_p*100,"% probabibility that it will be under 17degC for ",stats_save$h18,"h.\n")
  return(save_message)
  
}



sim_stats_bsts<- function(predct){
  x12samplesbt <- t(predct$distribution[,1:24])
  sim_stats <- data.frame(
    #average number of hours above 24deg if nothing changes
    h24 = mean(apply(x12samplesbt>25, 2, sum)),
    #prob of hitting 24 deg
    h24_p = mean(apply(x12samplesbt>25, 2, max)),
    # for at least 3 hours
    h24_p2 = mean(ifelse(apply(x12samplesbt>25, 2, sum)>=3,1,0),na.rm=T ) ,
    
    #average number of hours under 18degC if nothing changes
    h18 = mean(apply(x12samplesbt<18, 2, sum)),
    #prob of hitting 18degC
    h18_p = mean(apply(x12samplesbt<18, 2, max)),
    # for at least 3 hours
    h18_p2 = mean(ifelse(apply(x12samplesbt<18, 2, sum)>=3,1,0),na.rm=T )
  )
  return(sim_stats)}


sim_stats_arima<- function(predct){
  #using uppper and lower bounds
  x12samplesbt <-data.frame(predct$mean[1:24],predct$upper[1:24,1],predct$lower[1:24,1])
  sim_stats <- data.frame(
    #average number of hours above 24deg if nothing changes
    h24 = mean(apply(x12samplesbt>25, 2, sum)),
    #prob of hitting 24 deg
    h24_p = mean(apply(x12samplesbt>25, 2, max)),
    # for at least 3 hours
    h24_p2 = mean(ifelse(apply(x12samplesbt>25, 2, sum)>=3,1,0),na.rm=T ) ,
    
    #average number of hours under 18degC if nothing changes
    h18 = mean(apply(x12samplesbt<18, 2, sum)),
    #prob of hitting 18degC
    h18_p = mean(apply(x12samplesbt<18, 2, max)),
    # for at least 3 hours
    h18_p2 = mean(ifelse(apply(x12samplesbt<18, 2, sum)>=3,1,0),na.rm=T )
  )
  return(sim_stats)}



# Construct the lights covariate matrix  ==================
constructCov <- function(lights, times){
  covmatN <- matrix(0, nrow=length(lights), ncol=67)
  for(tt in c(25:nrow(covmatN))){
    if(sum(covmatN[tt,])==0){#only deal with time points not yet dealt with
      if(lights[tt]){
        if(all(c(lights[tt-1]==0, sum(lights[tt-(5:1)])<2))){#previous was off, and 4/5 of previous were off
          covmatN[tt,1] <- 1
          for(ii in 1:19){
            if(tt+ii<=nrow(covmatN)){
              if(sum(covmatN[tt+ii,])==0){
                if(sum(lights[tt:(tt+ii)])==(ii+1)){#lights continually on since the start of on period
                  covmatN[tt+ii,1+ii] <- 1
                }else{#off since the start of the on period
                  if((lights[tt+ii]==0)&(tt+ii+4<=nrow(covmatN))){
                    #could be start of the off period
                    if(all(lights[tt+ii+(1:4)]==0)){#first off, with 4 following it
                      covmatN[tt+ii,21] <- 1
                      covmatN[tt+ii+1,22] <- 1
                      covmatN[tt+ii+2,23] <- 1
                      covmatN[tt+ii+3,24] <- 1
                      covmatN[tt+ii+4,25] <- 1
                      if(tt+ii+8<=nrow(covmatN)){
                        for(jj in 5:8){
                          if(all(lights[tt+ii+(1:jj)]==0)){
                            covmatN[tt+ii+jj, 21+jj] <- 1
                          }
                        }
                      }
                      
                    }else{#following 4 values are not all off
                      if(all(lights[tt+ii+1:2]==1)){#at least following two are on
                        covmatN[tt+ii,30] <- 1 #off during an on
                        covmatN[tt+ii+1,31] <- 1 #on after off in an on
                        covmatN[tt+ii+2,32] <- 1 #second on after off in on
                        for(jj in 3:11){
                          if(all(lights[tt+ii+1:jj]==1)){
                            covmatN[tt+ii+jj,30+jj] <- 1
                          }
                        }
                      }
                      
                    }
                    #or could be an off on the middle of the on (dealt with before)
                    
                  }
                }
              }
            }
            
          }
        }else{
          if(tt+2<=nrow(covmatN)){
            if(all(c(sum(covmatN[tt,]==0),sum(lights[tt+(-2:2)])<3))){#on in an off, max one other in 5 hour interval is on
              covmatN[tt,42] <- 1
              if(all(c(lights[tt+1]==0, sum(covmatN[tt+1,])==0))){#back off after on in off
                covmatN[tt+1,43] <- 1
                if(all(c(lights[tt+2]==0, sum(covmatN[tt+2,])==0))){#2nd off after on in off
                  covmatN[tt+2,44] <- 1
                  if(tt+3<=nrow(covmatN)){
                    if(all(c(lights[tt+3]==0, sum(covmatN[tt+3,])==0))){
                      covmatN[tt+3,45] <- 1
                    }
                  }
                }
              }
            }
          }
          
        }
        
      }else{#lights off
        if(all(c(lights[tt-1]==1, sum(lights[tt-(6:1)])>4))){#first hour lights are off following 4/6 hours on
          covmatN[tt,21] <- 1
          for(jj in 1:8){
            if(tt+jj<=nrow(covmatN)){
              if(sum(covmatN[tt+jj,])==0){
                if(all(lights[tt+(1:jj)]==0)){
                  covmatN[tt+jj, 21+jj] <- 1
                }
              }
            }
          }
        }
      }
    }
    
  }
  
  for(tt in c(25:nrow(covmatN))){
    if(sum(covmatN[tt,])==0){#only deal with time points not yet dealt with
      if(lights[tt]){
        if(all(c(lights[tt-1]==0, sum(lights[tt-(5:1)])<4))){#previous was off, and 2/5 of previous were off, on following short off
          covmatN[tt,46] <- 1
          for(ii in 1:19){
            if(tt+ii<=nrow(covmatN)){
              if(sum(covmatN[tt+ii,])==0){
                if(sum(lights[tt:(tt+ii)])==(ii+1)){#lights continually on since the start of on period
                  covmatN[tt+ii,46+ii] <- 1
                }
                
              }
            }
            
          }
        }
      }
    }
  }
  
  covmatN[,1:20] <- covmatN[,1:20] + covmatN[,46:65] #combine short off values with rest
  covmatN <- covmatN[,-c(46:65)]
  stt <- which(covmatN[,1]==1)[1]
  covmatN[1:(stt-1),] <- constructCovTyp(times[1:(stt-1)])
  covmatN[which(((rowSums(covmatN)==0)*(lights==0))==1),46] <- 1 #remaining lights off
  covmatN[which(((rowSums(covmatN)==0)*(lights==1))==1),47] <- 1 #remaining lights on
  
  return(covmatN)
}


constructCovTyp <- function(times){
  covmatT <- matrix(0, nrow=length(times), ncol=47)
  farmhour <- hour(times)
  for(tt in 1:18){
    covmatT[,tt] <- ifelse(farmhour==((tt+16)%%24), 1, 0)
  }
  for(tt in 1:6){
    covmatT[,20+tt] <- ifelse(farmhour==((tt+10)%%24), 1, 0)
  }
  return(covmatT)
}
