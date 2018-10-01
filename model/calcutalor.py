import pandas as pd
import numpy as np

class Calculator:

    @staticmethod
    def fillna_mean(dataset):
        """This method takes in argument a vector of price containing some missing values and fills
         them with the mean"""
        if dataset:
            data = pd.DataFrame(dataset, columns=["close"])
            data.replace(0, np.NaN, inplace=True)
            data.fillna(data.mean(), inplace=True)
            return list(data["close"])
        return dataset

    @staticmethod
    def fillna_linear_interp(dataset):
        """This method fills the missing values with linear interpolation"""
        if dataset:
            data = pd.DataFrame(dataset, columns=["close"])
            data.replace(0, np.NaN, inplace=True)
            data.interpolate(method='linear', inplace=True)
            return list(data["close"])
        return dataset

    @staticmethod
    def get_statistics(dataset):
        """This method computes some statistics for each maturity inside the dataset"""
        returns, volatilities, minimums, maximums, ratios = {}, {}, {}, {}, {}

        for keys in dataset:
            if dataset[keys]:
                price = pd.DataFrame(dataset[keys], columns=['close'])
                price["return"] = price['close'].pct_change()
                returns[keys] = round((price["close"].iloc[-1] - price["close"].iloc[0]) / price["close"].iloc[0], 2)
                volatilities[keys] = round(price["return"].std() * np.sqrt(252), 3)
                minimums[keys] = round(price["close"].min(), 2)
                maximums[keys] = round(price["close"].max(), 2)
                ratios[keys] = round(price[price["return"] >= 0].shape[0] / price[price["return"] < 0].shape[0], 2)

        return returns, volatilities, minimums, maximums, ratios
