from inversion import *
import inversion.kernels as kernels

def LikelihoodRatio(xModel, xData, yModel, yData, tModel, theta, thetastar, sigmaY, nugget, lambda_e):
    
    # xmodel and xdata are coordinates
    # ymodel and ydata are outputs
    # tmodel is calibration parameters
    # theta and thetastar are the current state of calibration parameter vector and proposal calibration parameter vector
    # last value of each should be lengthscale
    # T is temperature
    
    # initialize and fit gps
    gp_theta = fitGP(xModel, xData, yModel, yData, tModel, theta, sigmaY, nugget, lambda_e)
    gp_thetastar = fitGP(xModel, xData, yModel, yData, tModel, thetastar, sigmaY, nugget, lambda_e)
	
    # extract marginal likelihoods
    H_theta = gp_theta.log_marginal_likelihood_value_
    H_thetastar = gp_thetastar.log_marginal_likelihood_value_
    
    # find likelihood ratio
    alpha = H_thetastar - H_theta
    
    return alpha

def fitGP(xModel, xData, yModel, yData, tModel, tData, sigmaY, nugget, lambda_e):
    
    # initialize and fit multi output gaussian process
	
    # multioutput gp noise vector
    noiseVector = np.concatenate((np.ones(np.shape(yModel)[0] * len(xModel)) * nugget, np.ones(np.shape(yData)[0] * len(xData)) * (sigmaY ** 2)))
    
    # initialize gps
    gp = GaussianProcessRegressor(kernel=kernels.customRBF(length_scale = tData[-1], alpha=lambda_e), alpha=noiseVector)
	
    # structure training data
    xTraining, yTraining = mogpTraining(xModel, xData, yModel, yData, tModel, tData)
	
    # fit gps
    gp.fit(xTraining, yTraining)
	
    return(gp)
	

def mogpTraining(xModel, xData, yModel, yData, tModel, tData):
    
    # structures training data for mogp
    # dimensions: xModel (d1), xData (d2), yModel (N x d1), yData (M x d2), tModel (N x e1), tData (e1 + 1)
	
    # convert tData to M samples - only one 'true' parameter for all observation sets
    tDatas = np.repeat(np.reshape(tData, ((1, len(tData)))), np.shape(yData)[0] * len(xData), axis=0)
	
    # append exact lengthscale in tModel - last component of tData
    tModels = np.zeros((0, np.shape(tModel)[1] + 1))
    yModels = np.zeros(0)
    yDatas = np.zeros(0)
    for i in range(np.shape(tModel)[0]):
        tModels = np.vstack((tModels, np.hstack((np.repeat(np.reshape(tModel[i, :], ((1, np.shape(tModel)[1]))), len(xModel), axis=0),
                                                 np.repeat(np.reshape(tData[-1], ((1, 1))), len(xModel), axis=0)))))
        yModels = np.concatenate((yModels, yModel[i, :]))
    for i in range(np.shape(yData)[0]):
        yDatas = np.concatenate((yDatas, yData[i, :]))
	
    # repeat coordinates for all parameter values
    #xModels = np.repeat(np.reshape(xModel, ((1, len(xModel)))), np.shape(yModel)[0], axis=0)
    #xDatas = np.repeat(np.reshape(xData, ((1, len(xData)))), np.shape(yData)[0], axis=0)
    xModels = np.reshape(np.repeat(xModel, np.shape(yModel)[0]), ((len(xModel) * np.shape(yModel)[0], 1)))
    xDatas = np.reshape(np.repeat(xData, np.shape(yData)[0]), ((len(xData) * np.shape(yData)[0], 1)))
	
    # construct training data sets
    xTrain = np.hstack((np.vstack((xModels, xDatas)),
                        np.vstack((tModels, tDatas))))
    yTrain = np.concatenate((yModels, yDatas))
	
    return(xTrain, yTrain)