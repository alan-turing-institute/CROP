# from CalibrationV2 import LatestTime
from TestScenarioV2 import testScenario

if __name__ == '__main__':
  results = testScenario()
  print(results['T_air'])
  print(results['RH_air'])