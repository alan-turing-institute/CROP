def main() -> None:
    from arima.dataAccess import getTrainingData
    from arima.cleanData import cleanData
    import pickle
    import logging
    import sys

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    env_raw, energy_raw = getTrainingData(numRows=500)

    with open("dump/env_raw.pkl", "wb") as handle:
        pickle.dump(env_raw, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_raw.pkl", "wb") as handle:
        pickle.dump(energy_raw, handle, protocol=pickle.HIGHEST_PROTOCOL)

    env_clean, energy_clean = cleanData(env_raw, energy_raw)

    with open("dump/env_clean.pkl", "wb") as handle:
        pickle.dump(env_clean, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open("dump/energy_clean.pkl", "wb") as handle:
        pickle.dump(energy_clean, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    main()
