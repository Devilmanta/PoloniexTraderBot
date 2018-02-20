from __future__ import division
from wrapper import poloniex
from datetime import datetime, timedelta
import time
from sklearn.neighbors import KNeighborsRegressor
import pandas as pd
from sklearn.model_selection import train_test_split
from scipy import stats
import smtplib
from email.mime.text import MIMEText

with open("ApiKeyAndSecret.txt", "r") as logfile:
    logs = logfile.read().splitlines()
    ApiKey = logs[0]
    Secret = logs[1]
    email = logs[2]
    password = logs[3]

conn = poloniex(ApiKey, Secret)


class DataAndTarget:
    def __init__(self, paircoin, period, days):
        self.data = []
        self.target = []
        self.ema10 = []
        self.ema40 = []
        self.pair = paircoin
        self.period = period
        self.days = days
        timeStamp1 = time.mktime(datetime.now().timetuple())
        timeNow = str(int(timeStamp1))
        timeStamp2 = time.mktime((datetime.now() - timedelta(days=self.days)).timetuple())
        timePast = str(int(timeStamp2))

        historicalData = conn.api_query("returnChartData",
                                        {"currencyPair": self.pair,
                                         "start": timePast, "end": timeNow, "period": self.period})
        emadata = []

        def EMA(values, window):
            emas = []
            for c, close in enumerate(values):
                if c == window:
                    emas.append(sum(values[0:window]) / window)
                elif c > window:
                    emas.append(close * (2 / (window + 1)) + emas[-1] * (1 - (2 / (window + 1))))
                if len(emas) > window + 1:
                    del (emas[0])
            return emas

        try:
            for count, i in enumerate(historicalData):
                # self.data.append([i["weightedAverage"],i["open"],i["close"],i["high"],i["low"],i["quoteVolume"]])
                emadata.append(i["close"])
                if count >= 40:
                    if historicalData[count - 1]["weightedAverage"] < i["weightedAverage"]:
                        wa = 1
                    else:
                        wa = 0
                    if historicalData[count - 1]["open"] < i["open"]:
                        opn = 1
                    else:
                        opn = 0
                    if historicalData[count - 1]["close"] < i["close"]:
                        cls = 1
                    else:
                        cls = 0
                    if historicalData[count - 1]["high"] < i["high"]:
                        hgh = 1
                    else:
                        hgh = 0
                    if historicalData[count - 1]["low"] < i["low"]:
                        low = 1
                    else:
                        low = 0
                    if historicalData[count - 1]["quoteVolume"] < i["quoteVolume"]:
                        qvol = 1
                    else:
                        qvol = 0
                    if EMA(emadata, 10)[-1] > EMA(emadata, 40)[-1]:
                        ema = 1
                    else:
                        ema = 0
                    if i["open"] < i["close"]:
                        openclose = 1
                    else:
                        openclose = 0

                    # DATAForging
                    self.data.append([wa, opn, cls, hgh, low, qvol, ema, openclose])

                    # TargetForging
                    if count + 1 == len(historicalData):
                        self.target.append(0)
                    elif historicalData[count - 1]["close"] < i["close"]:
                        self.target.append(1)
                    else:
                        self.target.append(0)
        except Exception as e:
            print e.__doc__
            print e.message
        finally:
            pass

    def returnData(self):
        return self.data

    def returnTarget(self):
        return self.target


def createColumns(ticker):
    return [ticker + '_w', ticker + '_o', ticker + '_c', ticker + '_h', ticker + '_l', ticker + '_v', ticker + '_ema',
            ticker + '_opncls']


def sendmail(subjecttext, bodytext):
    gmail_user = email
    gmail_pass = password
    try:
        send_from = gmail_user
        to = gmail_user
        subject = subjecttext

        msg = MIMEText(bodytext, 'plain')
        msg['Subject'] = subject
        msg['From'] = send_from
        msg['To'] = to

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_pass)
        server.sendmail(send_from, to, msg.as_string())
        server.quit()
        print "Email Sent!"

    except Exception as e:
        print e.__doc__
        print e.message
    finally:
        pass


def iscoingoesup(pair, period, hours):
    timeStamp1 = time.mktime(datetime.now().timetuple())
    timeNow = str(int(timeStamp1))
    timeStamp2 = time.mktime((datetime.now() - timedelta(hours=hours)).timetuple())
    timePast = str(int(timeStamp2))
    period = period
    rawdata = []
    historicalData = conn.api_query("returnChartData",
                                    {"currencyPair": pair,
                                     "start": timePast, "end": timeNow, "period": period})
    for c, i in enumerate(historicalData):
        rawdata.append(i["close"])

    dfdata = pd.DataFrame(rawdata, columns=list('c'))
    dfdata['index'] = dfdata.index
    return stats.linregress(dfdata[["index", "c"]])[2]


def secondsReturner():
    deltaseconds = 0
    currentM = datetime.now().minute
    currentH = datetime.now().hour

    if currentM < 59:
        while currentM % 5 is not 0:
            currentM += 1
            if currentM is 60:
                currentM = 0
                if currentH < 23:
                    currentH += 1
                else:
                    currentH = 0
        target = datetime(year=datetime.now().year,
                          month=datetime.now().month,
                          day=datetime.now().day,
                          hour=currentH,
                          minute=currentM)

        now = datetime.now()
        if now > target:
            deltaseconds = 0
        else:
            diff = target - now
            deltaseconds = diff.seconds
    elif currentM == 59:
        deltaseconds = 60

    return deltaseconds + 15


def predictor(data, target):
    x_train, x_test, y_train, y_test = train_test_split(data, target, test_size=0.4, shuffle=False)
    # MLPClassifier
    # mlp = MLPClassifier(hidden_layer_sizes=(100), learning_rate='constant')
    # mlp.fit(x_train, y_train)
    # predictions = mlp.predict(x_test)

    # LinearRegression
    # lin = linear_model.LinearRegression()
    # lin.fit(dfData.iloc[:-1], dfTarget.iloc[:-1])
    # predictions = lin.predict(dfData.tail(10))
    # print(predictions)

    # MLPRegressor
    # mlp = MLPRegressor(hidden_layer_sizes=(100))
    # mlp.fit(x_train, y_train)
    # predictions = mlp.predict(x_test)

    # KNeighborsRegressor
    knr = KNeighborsRegressor(n_neighbors=1)
    knr.fit(x_train, y_train)
    predictions = knr.predict(x_test)
    return predictions


def SEMA(values, window):
    emas = []
    for c, close in enumerate(values):
        if c == window:
            emas.append(sum(values[:window]) / window)
        elif c > window:
            emas.append(values[c-1] * (2 / (window + 1)) + emas[-1] * (1 - (2 / (window + 1))))
    return emas


def MACD(ema12, ema26):
    macd = []
    del (ema26[:14])
    for i in range(0, 50):
        macd.append(ema12[i] - ema26[i])
    return macd


def SIG(macd):
    sig = SEMA(macd, 9)
    return sig


def HIST(macd, sig):
    hist = []
    del (macd[:9])
    for i in range(0, len(sig)):
        hist.append(macd[i] - sig[i])
    return hist


def MovingAv(values, window):
    movAv = []
    for c, close in enumerate(values):
        if c > window:
            movAv.append(sum(values[-window:]) / window)
    return movAv


def oscillator(close, low, high):
    if (max(high[-14:]) - min(low[-14:])) == 0:
        print "zero divider"
        return 0
    else:
        return 100 * (close - min(low[-14:])) / (max(high[-14:]) - min(low[-14:]))


def buyingTime(period):
    try:
        print "Gathering coin information..."
        timeStamp1 = time.mktime(datetime.now().timetuple())
        timeNow = str(int(timeStamp1))
        timeStamp2 = time.mktime((datetime.now() - timedelta(hours=12)).timetuple())
        timePast = str(int(timeStamp2))
        changelist = []
        coinperc = conn.returnTicker()
        dic = {}
        possiblebuyList = []
        coin = None
        dontBuy = ["BTC_DOGE", "BTC_BCN"]
        for i in coinperc:
            if i.startswith("BTC"):
                change = float(coinperc[i]["percentChange"])
                vol = float(coinperc[i]["baseVolume"])  # Vol(BTC)
                if vol > 20:
                    changelist.append(change)
                    dic[i] = change
        changelist.sort()
        for j in changelist:
            point = 0
            emadata = []
            lowdata = []
            highdata = []
            kData = []
            MACDCrossSig = False
            volumecheck = True
            lastpair = dic.keys()[dic.values().index(j)]
            if lastpair in dontBuy:
                pass
            else:
                historicalData = conn.api_query("returnChartData", {"currencyPair": lastpair, "start": timePast, "end": timeNow, "period": period})
                for count, i in enumerate(historicalData):
                    lowdata.append(i["low"])
                    highdata.append(i["high"])
                    if count > 20:
                        kData.append(oscillator(i["close"], lowdata, highdata))
                    emadata.append(i["close"])
                    if count > 264:  # Last 2 hour Volume Check for if its zero
                        if float(i["volume"]) == 0:
                            volumecheck = False
                # histog = HIST(MACD(SEMA(emadata, 12), SEMA(emadata, 26)), SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26))))
                print lastpair
                # print "oscillator value: {}".format(float(MovingAv(kData, 3)[-1]))
                # if SEMA(emadata, 10)[-2] < SEMA(emadata, 40)[-2] and SEMA(emadata, 10)[-1] > SEMA(emadata, 40)[-1] and volumecheck and float(MovingAv(kData, 3)[-1]) < 20:
                # if volumecheck and iscoingoesup(lastpair, 300, 6) > 0:
                # if volumecheck and float(MovingAv(kData, 3)[-1]) < 20 and iscoingoesup(lastpair, 300, 6) > 0:
                # if volumecheck and iscoingoesup(lastpair, 300, 6) > 0:
                if SEMA(emadata, 10)[-1] < SEMA(emadata, 40)[-1] and volumecheck and float(MovingAv(kData, 3)[-1]) < 20 and iscoingoesup(lastpair, 300, 6) > 0:
                    # if float(MovingAv(kData, 3)[-1]) < 20:
                    point += (20 - float(MovingAv(kData, 3)[-1]))
                    #     oscil = True
                    # point += iscoingoesup(lastpair, 300, 6)
                    # if (SEMA(emadata, 10)[-2] - SEMA(emadata, 40)[-2]) < (SEMA(emadata, 10)[-1] - SEMA(emadata, 40)[-1]):
                    #     point += 20
                    # if histog[-4] <= histog[-3] <= histog[-2] < 0 < histog[-1]:
                        # point += 20
                    # if MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-2] < 0 < MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-1]:
                    #     point += 10
                    #     MACDCrossZero = True
                    # if SEMA(emadata, 10)[-1] < SEMA(emadata, 40)[-1]:
                    #     if SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-1] < 0 and MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-1] < 0:
                    #             if MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-2] < SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-2] and SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-1] < MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-1]:
                    #                 MACDCrossSig = True
                    point += iscoingoesup(lastpair, 300, 6)
                    # if MACDCrossSig:
                    #     possiblebuyList.append([lastpair, point])
                    if not coin:
                        coin = [lastpair, point]
                    elif point > coin[1]:
                        coin = [lastpair, point]

                # if SEMA(emadata, 10)[-1] < SEMA(emadata, 40)[-1] and volumecheck and float(
                #        MovingAv(kData, 3)[-1]) < 20 and iscoingoesup(lastpair, 300, 6) > 0:
                    # NOT HERE ###############
                    # for i in range(1, 10):
                    #     if MACD(SEMA(emadata, 12), SEMA(emadata, 26))[(-i)-1] < 0 < MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-i]:
                    #         MACDCrossZero = True
                    #     if MACD(SEMA(emadata, 12), SEMA(emadata, 26))[(-i)-1] < SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[(-i)-1] and MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-i] > SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-i]:
                    #         MACDCrossSig = True
                    # Last Change: EMA40 > EMA10 requirements removed
                    # if histog[-4] <= histog[-3] <= histog[-2] < 0 < histog[-1] and volumecheck:
                    # if histog[-6] > histog[-5] > histog[-4] > histog[-3] > histog[-2] < histog[-1] and volumecheck:

                    # if MACDCrossZero and MACDCrossSig and float(MovingAv(kData, 3)[-1]) < 20:
                    ####################################
                    # coin = lastpair
                    # break
        if not coin:
            return None
        else:
            print possiblebuyList
            return coin[0]
    except Exception as e:
        print e.__doc__
        print e.message
    finally:
        pass


def sellingTime(pair, period, boughtBtcValue, lastprice, fee):
    days = 1
    timeStamp1 = time.mktime(datetime.now().timetuple())
    timeNow = str(int(timeStamp1))
    timeStamp2 = time.mktime((datetime.now() - timedelta(days=days)).timetuple())
    timePast = str(int(timeStamp2))
    emadata = []
    lowdata = []
    highdata = []
    semalist = []
    kData = []
    count = 0
    try:
        sellAmount = float(conn.returnBalances()[pair.split("_")[1]])
        if sellAmount * lastprice * (1 - fee) > boughtBtcValue:
        #elif (boughtprice * 1.003) < lastprice:  # %0,003 Fee cut calculated
            historicalData = conn.api_query("returnChartData",
                                            {"currencyPair": pair,
                                             "start": timePast, "end": timeNow, "period": period})
            for count, i in enumerate(historicalData):
                emadata.append(i["close"])
                lowdata.append(i["low"])
                highdata.append(i["high"])
                # if count > 20:
                #     kData.append(oscillator(i["close"], lowdata, highdata))
            # if float(lastprice) > (float(boughtprice) * 1.02) and (
            #         SEMA(emadata, 10)[-1] >= SEMA(emadata, 10)[-2] or (SEMA(emadata, 10)[-2] - SEMA(emadata, 40)[-2]) < (
            #         SEMA(emadata, 10)[-1] - SEMA(emadata, 40)[-1])):

            # new system not working
            # if (SEMA(emadata, 10)[-2] - SEMA(emadata, 40)[-2]) < (SEMA(emadata, 10)[-1] - SEMA(emadata, 40)[-1]):
            #     if float(MovingAv(kData, 3)[-1]) > 80:
            #         print "oscillator value: {}".format(float(MovingAv(kData, 3)[-1]))
            #         if float(MovingAv(kData, 3)[-1]) == 100:
            #             return True
            #         elif float(MovingAv(kData, 3)[-1]) > 90:
            #             for i in range(1, 6):
            #                 if float(MovingAv(kData, 3)[-i]) > 90:
            #                     count += 1
            #             if count > 2:
            #                 return True
            #             else:
            #                 return False
            #         else:
            #             return False
            #     else:
            #         return False
            # else:
            #     return True
            print "Last 5 MACD: {}".format(MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-5:])
            print "Last EMA10: {}".format(SEMA(emadata, 10)[-5:])
            print "Last EMA10: {}".format(SEMA(emadata, 40)[-5:])
            for i in range(2, 8):
                if SEMA(emadata, 10)[-i] > SEMA(emadata, 40)[-i]:
                    semalist.append(True)
                else:
                    semalist.append(False)

            # HODL
            if SEMA(emadata, 10)[-1] > SEMA(emadata, 40)[-1]:
                if SEMA(emadata, 10)[-1] < SEMA(emadata, 10)[-2]:
                    if MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-2] > 0 > MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-1]:
                        print "MACD pass through zero SELL"
                        return True
                    else:
                        return False
                # elif SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-1] > 0 and MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-1] > 0:
                #     if MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-2] >= SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-2] and MACD(SEMA(emadata, 12), SEMA(emadata, 26))[-1] < SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26)))[-1]:
                #         print "MACD pass down through SIG SELL"
                #         return True
                #     else:
                #         return False
                else:
                    return False
                # print "oscillator value: {}".format(float(MovingAv(kData, 3)[-1]))
            elif SEMA(emadata, 10)[-1] < SEMA(emadata, 40)[-1]:
                if False in semalist:
                    return False
                else:
                    print "EMA10 pass down through EMA40 SELL"
                    return True
            else:
                return False

            # BURASI ESKI HALI VE AZ DA OLSA CALISIYOR #
            # if SEMA(emadata, 10)[-1] >= SEMA(emadata, 10)[-2] or (SEMA(emadata, 10)[-2] - SEMA(emadata, 40)[-2]) < (SEMA(emadata, 10)[-1] - SEMA(emadata, 40)[-1]):
            #     print "oscillator value: {}".format(float(MovingAv(kData, 3)[-1]))
            #     if float(MovingAv(kData, 3)[-1]) > 80:
            #         return True
            #     else:
            #         return False
            # else:
            #     return True
        else:
            return False
    except Exception as e:
        print e.__doc__
        print e.message
    finally:
        pass


def bidratefinder(pair, connection):
    minusone = 0.00000001
    bidrate = 0
    biddic = connection.returnOrderBook(pair)["bids"]
    if 0.00000001 / float(biddic[0][0]) < 0.003:
        bidrate = float(biddic[0][0]) + minusone
        return bidrate
    else:
        for i in range(0, 5):
            if round(float(biddic[i][0]) - minusone, 8) != round(float(biddic[i+1][0]), 8):
                bidrate = (float(biddic[i][0]) - minusone)
                break
        if bidrate == 0:
            return None
        else:
            return bidrate


def askratefinder(pair, connection):
    plusone = 0.00000001
    askrate = 0
    askdic = connection.returnOrderBook(pair)["asks"]
    if (0.00000001 / float(askdic[0][0])) < 0.003:
        askrate = float(askdic[0][0]) - plusone
        return askrate
    else:
        for i in range(0, 5):
            if round(float(askdic[i][0]) + plusone, 8) != round(float(askdic[i+1][0]), 8):
                askrate = (float(askdic[i][0]) + plusone)
                break
        if askrate == 0:
            return None
        else:
            return askrate


def main():
    liveTest = False
    btcforBuying = 0.01
    period = 300
    buyingAmountinBTC = btcforBuying
    fee = .9975
    btcValue = 0
    firstBuyRate = 0
    pair = None
    if liveTest:
        pass
    else:
        with open("AITraderLog.txt", "r") as logfile:
            log = str(logfile.readlines()[-1])
            if "PARTIALBUY" in log:
                bought = True
                pair = log.split('#')[1]
                altfee = float(log.split('#')[9])
                btcValue = float(log.split('#')[11])
                firstBuyRate = float(log.split('#')[13])
                altBuyAmountTotal = float(log.split('#')[7]) * (1 - altfee)
                altBuyRate = float(log.split('#')[3])
                print "Already Bought: {}".format(pair)
            elif "PARTIALSELL" in log:
                print "Partial Sell Detected"
                bought = True
                pair = log.split('#')[1]
                altfee = float(log.split('#')[9])
                btcValue = float(log.split('#')[17])
                altBuyAmountTotal = float(log.split('#')[11]) * (1 - altfee)
                buyingAmountinBTC = float(log.split('#')[13])
                altBuyRate = float(log.split('#')[15])
            elif "BUY" in log:
                bought = True
                pair = log.split('#')[1]
                altfee = float(log.split('#')[9])
                btcValue = float(log.split('#')[11])
                firstBuyRate = float(log.split('#')[13])
                altBuyAmountTotal = float(log.split('#')[7]) * (1 - altfee)
                altBuyRate = float(log.split('#')[3])
                print "Already Bought: {}".format(pair)
            elif "SELL" in log:
                print "New coin searching"
                bought = False
                pair = None
                altBuyAmountTotal = 0
                altBuyRate = 0
            else:
                print "New coin searching"
                bought = False
                pair = None
                altBuyAmountTotal = 0
                altBuyRate = 0
    while True:
        time.sleep(5)
        # ---  TEST --- ##################################################
        if liveTest:
            pass

        # ---  PRODUCTION --- ##########################################
        else:
            try:
                if pair is not None:
                    print "### {} ###".format(pair)
                    connection = conn.returnTicker()[pair]
                    lastpairprice = float(connection["last"])
                    print "{}: {} Amount: {:.8f}, BTC Value: {:.8f}".format(datetime.now().replace(microsecond=0),
                                                                            pair,
                                                                            altBuyAmountTotal,
                                                                            altBuyAmountTotal * lastpairprice)

                    if bought:
                        print "Bought rate:\t{:.8f}".format(altBuyRate)
                        if altBuyRate < lastpairprice:
                            print "\t\t{:.8f} Raising %{:.2f}".format(lastpairprice - altBuyRate,
                                                                      ((lastpairprice - altBuyRate) / altBuyRate) * 100)
                        elif altBuyRate > lastpairprice:
                            print "\t\t{:.8f} Falling %{:.2f}".format(lastpairprice - altBuyRate,
                                                                      ((lastpairprice - altBuyRate) / altBuyRate) * 100)
                        else:
                            print "\t\t\t{:.8f}".format(lastpairprice - altBuyRate)
                        print "Lastpair rate:\t{:.8f}\n".format(lastpairprice)
                        # StopLoss
                        if lastpairprice < (firstBuyRate * .85):
                            print "STOPLOSS SELLING"
                            # altSellAmount = float(conn.returnBalances()[pair.split("_")[1]])
                            altSellAmount = altBuyAmountTotal
                            orderNumber = conn.sell(pair, lastpairprice, altSellAmount, 1, 0)
                            if "orderNumber" in orderNumber:
                                print "STOPLOSS SELL Complete!\n"
                                altSoldBTCTotal = 0
                                for i in orderNumber["resultingTrades"]:
                                    altSoldAmount = float(i["amount"])
                                    altSoldRate = float(i["rate"])
                                    altSoldBTCvalue = float(i["total"])
                                    altSoldBTCTotal += altSoldBTCvalue
                                    print "\n{} #{}# STOPLOSS rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#" \
                                        .format(datetime.now().replace(microsecond=0), pair, altSoldRate,
                                                altSoldBTCvalue * fee, altSoldAmount)
                                    with open("AITraderLog.txt", "a") as logfile:
                                        logfile.write(
                                            "\n{} #{}# STOPLOSS rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#"
                                            .format(datetime.now().replace(microsecond=0), pair, altSoldRate,
                                                    altSoldBTCvalue * fee,
                                                    altSoldAmount))
                                    with open("AITraderLog.txt", "r") as logfile:
                                        bodytext = str(logfile.readlines()[-1]) + "\n\nBTC Balance: " + str(conn.returnBalances()['BTC'])
                                        sendmail('TraderBot STOPLOSS Information', bodytext)
                                btcValue = 0
                                firstBuyRate = 0
                                pair = None
                                bought = False
                                altBuyAmountTotal = 0
                                altBuyRate = 0
                            else:
                                print str(orderNumber["error"])
                        # Recover Buy
                        if lastpairprice < (altBuyRate * .95):
                            bought = False
                            bidrate = bidratefinder(pair, conn)
                            if bidrate:
                                orderNumber = conn.buy(pair, bidrate, (buyingAmountinBTC / bidrate), 0, 1)
                                boughtall = False
                                print "BUY Order Given for {} Bidrate: {:.8f} Waiting for completion...\n".format(pair, bidrate)
                                orderWaitingTime = time.time() + 300
                                while orderWaitingTime > time.time():
                                    if "error" in orderNumber:
                                        break
                                    elif "error" not in conn.returnOrderTrades(orderNumber["orderNumber"]):
                                        bought = True
                                        break
                                    else:
                                        time.sleep(1)
                                if bought:
                                    buyComplateWaitingTime = time.time() + 600
                                    while buyComplateWaitingTime > time.time():
                                        altBuyAmount, altBuyAmountTotal, altBuyRate, altBuyBTCvalue, altBuyBTCTotal, altfee = 0, 0, 0, 0, 0, 0
                                        for i in conn.returnOrderTrades(orderNumber["orderNumber"]):
                                            altfee = float(i["fee"])
                                            altBuyAmount = float(i["amount"])
                                            altBuyAmountTotal += (altBuyAmount * (1 - altfee))
                                            altBuyRate = float(i["rate"])
                                            altBuyBTCvalue = float(i["total"])
                                            altBuyBTCTotal += (altBuyBTCvalue * (1 - altfee))
                                        if round(altBuyAmountTotal, 7) >= round(((buyingAmountinBTC / altBuyRate) * (1 - altfee)), 7):
                                            boughtall = True
                                            break
                                        time.sleep(1)
                                    if boughtall is False:
                                        btcValue += altBuyBTCTotal
                                        print "\n{} #{}# PARTIALBUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#" \
                                            .format(datetime.now().replace(microsecond=0), pair,
                                                    altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate)
                                        print ""
                                        # Logging to a file
                                        with open("AITraderLog.txt", "a") as logfile:
                                            logfile.write("\n{} #{}# PARTIALBUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#"
                                                          .format(datetime.now().replace(microsecond=0), pair,
                                                                  altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate))
                                        with open("AITraderLog.txt", "r") as logfile:
                                            bodytext = str(logfile.readlines()[-1]) + "\n\nBTC Balance: " + \
                                                       str(float(conn.returnBalances()['BTC']) + (float(conn.returnBalances()[pair.split("_")[1]]) * lastpairprice))
                                            sendmail('TraderBot PARTIALBUY Information', bodytext)
                                    else:
                                        btcValue += altBuyBTCTotal
                                        print "\n{} #{}# BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#" \
                                            .format(datetime.now().replace(microsecond=0), pair,
                                                    altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate)
                                        print ""
                                        # Logging to a file
                                        with open("AITraderLog.txt", "a") as logfile:
                                            logfile.write("\n{} #{}# BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#"
                                                          .format(datetime.now().replace(microsecond=0), pair,
                                                                  altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate))
                                        with open("AITraderLog.txt", "r") as logfile:
                                            bodytext = str(logfile.readlines()[-1]) + "\n\nBTC Balance: " + \
                                                       str(float(conn.returnBalances()['BTC']) + (float(conn.returnBalances()[pair.split("_")[1]]) * lastpairprice))
                                            sendmail('TraderBot BUY Information', bodytext)
                                elif "error" in orderNumber:
                                    bought = True
                                    print orderNumber["error"]
                                else:
                                    bought = True
                                    print "Cancelling {} Buy Order".format(pair)
                                    conn.cancel(pair, orderNumber["orderNumber"])
                                print str(orderNumber["error"])
                        # Selling
                        # Prediction, Bought, Fee Passed.
                        # SellingTime Desicion method: buyAmount here is the amount of altcoin that bought below
                        # elif (altBuyAmountTotal * lastpairprice * .997) > buyingAmountinBTC:  # and int(predictions[-1, 0]) == 0:
                        if sellingTime(pair, period, btcValue, lastpairprice, altfee):
                            askrate = askratefinder(pair, conn)
                            if askrate:
                                print "Askrate: {:.8f}".format(askrate)
                                sellAmount = float(conn.returnBalances()[pair.split("_")[1]])
                                orderNumber = conn.sell(pair, askrate, sellAmount, 0, 1)
                                print "SELL Order Given for {} Askrate: {:.8f} Waiting for completion...\n".format(pair, askrate)
                                orderWaitingTime = time.time() + 300
                                while orderWaitingTime > time.time():
                                    if "error" in orderNumber:
                                        break
                                    elif "error" not in conn.returnOrderTrades(orderNumber["orderNumber"]):
                                        bought = False
                                        break
                                    else:
                                        time.sleep(1)
                                if bought is False:
                                    altSoldAmount, altSoldAmountTotal, altSoldRate, altSoldBTCvalue, altSoldBTCTotal = 0, 0, 0, 0, 0
                                    soldAll = False
                                    sellComplateWaitingTime = time.time() + 600
                                    while sellComplateWaitingTime > time.time():
                                        altSoldAmount, altSoldAmountTotal, altSoldRate, altSoldBTCvalue, altSoldBTCTotal = 0, 0, 0, 0, 0
                                        for i in conn.returnOrderTrades(orderNumber["orderNumber"]):
                                            altfee = float(i["fee"])
                                            altSoldAmount = float(i["amount"])
                                            altSoldAmountTotal += altSoldAmount
                                            altSoldRate = float(i["rate"])
                                            altSoldBTCvalue = float(i["total"]) * (1 - altfee)
                                            altSoldBTCTotal += altSoldBTCvalue
                                        if round(altSoldAmountTotal, 7) == round(sellAmount, 7):
                                            soldAll = True
                                            break
                                        time.sleep(1)
                                    if soldAll is False:
                                        print "Cancelling {} Sell Order".format(pair)
                                        conn.cancel(pair, orderNumber["orderNumber"])
                                        btcValue -= altSoldBTCTotal
                                        bought = True
                                        altBuyAmountTotal = sellAmount - altSoldAmountTotal
                                        buyingAmountinBTC = buyingAmountinBTC - altSoldBTCTotal
                                        print "\n{} #{}# PARTIALSELL rate: #{:.8f}# val: #{:.8f}#(BTC) " \
                                              "amount: #{:.8f}# Fee: #{:.4f}# AltRemaining: #{:.8f}# BTC Remaining :#{:.8f}# AltBuyRate: #{} btcValue: #{:.8f}#"\
                                            .format(datetime.now().replace(microsecond=0), pair, altSoldRate,
                                                    altSoldBTCTotal, altSoldAmountTotal, altfee, altBuyAmountTotal, buyingAmountinBTC, altBuyRate, btcValue)
                                        with open("AITraderLog.txt", "a") as logfile:
                                            logfile.write("\n{} #{}# PARTIALSELL rate: #{:.8f}# val: #{:.8f}#(BTC) amount: "
                                                          "#{:.8f}# Fee: #{:.4f}# AltRemaining: #{:.8f}# BTC Remaining :#{:.8f}# AltBuyRate: #{} btcValue: #{:.8f}#"
                                                          .format(datetime.now().replace(microsecond=0), pair, altSoldRate,
                                                                  altSoldBTCTotal, altSoldAmountTotal, altfee,
                                                                  altBuyAmountTotal, buyingAmountinBTC, altBuyRate, btcValue))
                                        with open("AITraderLog.txt", "r") as logfile:
                                            sendmail('TraderBot PARTIALSELL Information', str(logfile.readlines()[-1]))

                                    else:
                                        print "\n{} #{}# SELL rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}" \
                                            .format(datetime.now().replace(microsecond=0), pair, altSoldRate, altSoldBTCTotal, altSoldAmountTotal, altfee)
                                        with open("AITraderLog.txt", "a") as logfile:
                                            logfile.write("\n{} #{}# SELL rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}"
                                                          .format(datetime.now().replace(microsecond=0),
                                                                  pair, altSoldRate, altSoldBTCTotal, altSoldAmountTotal, altfee))
                                        with open("AITraderLog.txt", "r") as logfile:
                                            bodytext = str(logfile.readlines()[-1]) + "\n\nBTC Balance: " + str(conn.returnBalances()['BTC'])
                                            sendmail('TraderBot SELL Information', bodytext)
                                        btcValue = 0
                                        firstBuyRate = 0
                                        pair = None
                                        bought = False
                                        altBuyAmountTotal = 0
                                        buyingAmountinBTC = btcforBuying
                                        altBuyRate = 0
                                elif "error" in orderNumber:
                                    print orderNumber["error"]
                                else:
                                    print "Cancelling {} Sell Order".format(pair)
                                    conn.cancel(pair, orderNumber["orderNumber"])
                                    bought = True
                            else:
                                print "Could't find any Ask position for " + str(pair) + "\n"
                    # Buying
                    # Choosing best coin with buyingtime method
                    elif bought is False:
                        bidrate = bidratefinder(pair, conn)
                        if bidrate:
                            orderNumber = conn.buy(pair, bidrate, (buyingAmountinBTC / bidrate), 0, 1)
                            boughtall = False
                            print "BUY Order Given for {} Bidrate: {:.8f} Waiting for completion...\n".format(pair, bidrate)
                            orderWaitingTime = time.time() + 300
                            while orderWaitingTime > time.time():
                                if "error" in orderNumber:
                                    break
                                elif "error" not in conn.returnOrderTrades(orderNumber["orderNumber"]):
                                    bought = True
                                    break
                                else:
                                    time.sleep(1)
                            if bought:
                                buyComplateWaitingTime = time.time() + 600
                                while buyComplateWaitingTime > time.time():
                                    altBuyAmount, altBuyAmountTotal, altBuyRate, altBuyBTCvalue, altBuyBTCTotal, altfee = 0, 0, 0, 0, 0, 0
                                    for i in conn.returnOrderTrades(orderNumber["orderNumber"]):
                                        altfee = float(i["fee"])
                                        altBuyAmount = float(i["amount"])
                                        altBuyAmountTotal += (altBuyAmount * (1 - altfee))
                                        altBuyRate = float(i["rate"])
                                        altBuyBTCvalue = float(i["total"])
                                        altBuyBTCTotal += (altBuyBTCvalue * (1 - altfee))
                                    if round(altBuyAmountTotal, 7) >= round(((buyingAmountinBTC / altBuyRate) * (1 - altfee)), 7):
                                        boughtall = True
                                        break
                                    time.sleep(1)
                                if boughtall is False:
                                    btcValue = altBuyBTCTotal
                                    firstBuyRate = altBuyRate
                                    print "\n{} #{}# PARTIALBUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#" \
                                        .format(datetime.now().replace(microsecond=0), pair,
                                                altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate)
                                    print ""
                                    # Logging to a file
                                    with open("AITraderLog.txt", "a") as logfile:
                                        logfile.write("\n{} #{}# PARTIALBUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#"
                                                      .format(datetime.now().replace(microsecond=0), pair,
                                                              altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate))
                                    with open("AITraderLog.txt", "r") as logfile:
                                        bodytext = str(logfile.readlines()[-1]) + "\n\nBTC Balance: " + \
                                                   str(float(conn.returnBalances()['BTC']) + (float(conn.returnBalances()[pair.split("_")[1]]) * lastpairprice))
                                        sendmail('TraderBot PARTIALBUY Information', bodytext)
                                else:
                                    btcValue = altBuyBTCTotal
                                    firstBuyRate = altBuyRate
                                    print "\n{} #{}# BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#" \
                                          .format(datetime.now().replace(microsecond=0), pair,
                                                  altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate)
                                    print ""
                                    # Logging to a file
                                    with open("AITraderLog.txt", "a") as logfile:
                                        logfile.write("\n{} #{}# BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}# btcValue: #{:.8f}# firstBuyRate: #{:.8f}#"
                                                      .format(datetime.now().replace(microsecond=0), pair,
                                                              altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee, btcValue, firstBuyRate))
                                    with open("AITraderLog.txt", "r") as logfile:
                                        bodytext = str(logfile.readlines()[-1]) + "\n\nBTC Balance: " + \
                                                   str(float(conn.returnBalances()['BTC']) + (float(conn.returnBalances()[pair.split("_")[1]]) * lastpairprice))
                                        sendmail('TraderBot BUY Information', bodytext)
                            elif "error" in orderNumber:
                                print orderNumber["error"]
                            else:
                                print "Cancelling {} Buy Order".format(pair)
                                conn.cancel(pair, orderNumber["orderNumber"])
                        else:
                            print "Could't find any bid position for " + str(pair) + "\n"
                    else:
                        pair = None
                else:
                    pair = buyingTime(period)

            except Exception as e:
                print e.__doc__
                print e.message
            finally:
                pass


if __name__ == "__main__":
    main()
