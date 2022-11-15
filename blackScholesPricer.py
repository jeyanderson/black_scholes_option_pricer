import requests
from math import log, sqrt, exp
from scipy.stats import norm
from datetime import datetime
import numpy as np
import json
import pandas_datareader.data as web

def callData(S,K,T,r,sigma):
    return norm.cdf(d1(S,K,T,r,sigma))
def callGamma(S,K,T,r,sigma):
    return norm.pdf(d1(S,K,T,r,sigma))/(S*sigma*sqrt(T))
def callVega(S,K,T,r,sigma):
    return 0.01*(S*norm.pdf(d1(S,K,T,r,sigma))*sqrt(T))
def callTheta(S,K,T,r,sigma):
    return 0.01*(-(S*norm.pdf(d1(S,K,T,r,sigma))*sigma)/(2*sqrt(T)) - r*K*exp(-r*T)*norm.cdf(d2(S,K,T,r,sigma)))
def callRho(S,K,T,r,sigma):
    return 0.01*(K*T*exp(-r*T)*norm.cdf(d2(S,K,T,r,sigma)))
    
def putDelta(S,K,T,r,sigma):
    return -norm.cdf(-d1(S,K,T,r,sigma))
def putGamma(S,K,T,r,sigma):
    return norm.pdf(d1(S,K,T,r,sigma))/(S*sigma*sqrt(T))
def putVega(S,K,T,r,sigma):
    return 0.01*(S*norm.pdf(d1(S,K,T,r,sigma))*sqrt(T))
def putTheta(S,K,T,r,sigma):
    return 0.01*(-(S*norm.pdf(d1(S,K,T,r,sigma))*sigma)/(2*sqrt(T)) + r*K*exp(-r*T)*norm.cdf(-d2(S,K,T,r,sigma)))
def putRho(S,K,T,r,sigma):
    return 0.01*(-K*T*exp(-r*T)*norm.cdf(-d2(S,K,T,r,sigma)))

def d1(S,K,T,r,sigma):
    return(log(S/K)+(r+sigma**2/2.)*T)/(sigma*sqrt(T))
def d2(S,K,T,r,sigma):
    return d1(S,K,T,r,sigma)-sigma*sqrt(T)


def bsCall(S,K,T,r,sigma):
    return S*norm.cdf(d1(S,K,T,r,sigma))-K*exp(-r*T)*norm.cdf(d2(S,K,T,r,sigma))
  
def bsPut(S,K,T,r,sigma):
    return K*exp(-r*T)-S*bsCall(S,K,T,r,sigma)


x = requests.get("https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=SPY&apiKey=ihk1_aM4dwnBfDSVX3fMns5YXxe5FHg3")
df = x.content
df = json.loads(df)
print(df["results"])
for dfIndex in df["results"]:
    type = dfIndex["contract_type"]
    stock = dfIndex["underlying_ticker"]
    expiry = datetime.strptime(dfIndex["expiration_date"], '%Y-%m-%d').strftime('%m-%d-%Y')
    strikePrice = dfIndex["strikePrice"]

    today = datetime.now()
    oneYearAgo = today.replace(year=today.year-1)

    df = web.DataReader(stock, 'yahoo', oneYearAgo, today)

    df = df.sort_values(by="Date")
    df = df.dropna()
    df = df.assign(close_day_before=df.Close.shift(1))
    df['returns'] = ((df.Close - df.close_day_before)/df.close_day_before)

    sigma = np.sqrt(252) * df['returns'].std()
    uty = (web.DataReader(
        "^TNX", 'yahoo', today.replace(day=today.day-1), today)['Close'].iloc[-1])/100
    lcp = df['Close'].iloc[-1]
    t = (datetime.strptime(expiry, "%m-%d-%Y") - datetime.utcnow()).days / 365

    print('The Option Price is: ', bsCall(lcp, strikePrice, t, uty, sigma))
    print('The Option Delta is: ', callData(lcp, strikePrice,t,uty,sigma))
    print('The Option Gamma is: ', callGamma(lcp, strikePrice,t,uty,sigma))
    print('The Option Vega is: ', callVega(lcp, strikePrice,t,uty,sigma))
    print('The Option Theta is: ', callTheta(lcp, strikePrice,t,uty,sigma))
    print('The Option Rho is: ', callRho(lcp, strikePrice,t,uty,sigma))

    def callImpliedVolatility(Price, S, K, T, r):
        sigma = 0.001
        while sigma < 1:
            priceImplied = S * \
                norm.cdf(d1(S, K, T, r, sigma))-K*exp(-r*T) * \
                norm.cdf(d2(S, K, T, r, sigma))
            if Price-(priceImplied) < 0.001:
                return sigma
            sigma += 0.001
        return "Not Found"

    def putImpliedVolatility(Price, S, K, T, r):
        sigma = 0.001
        while sigma < 1:
            priceImplied = K*exp(-r*T)-S+bsCall(S, K, T, r, sigma)
            if Price-(priceImplied) < 0.001:
                return sigma
            sigma += 0.001
        return "Not Found"

    print("Implied Volatility: " +
        str(100 * callImpliedVolatility(bsCall(lcp, strikePrice, t, uty, sigma,), lcp, strikePrice, t, uty,)) + " %")