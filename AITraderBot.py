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
            emas.append(sum(values[0:window]) / window)
        elif c > window:
            emas.append(close * (2 / (window + 1)) + emas[-1] * (1 - (2 / (window + 1))))
        if len(emas) > window + 50:
            del (emas[0])
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
            movAv.append(sum(values[-3:]) / window)
    return movAv


def oscillator(close, low, high):
    return 100 * (close - min(low[-14:])) / (max(high[-14:]) - min(low[-14:]))


def buyingTime(period):
    try:
        print "Gathering coin information..."
        timeStamp1 = time.mktime(datetime.now().timetuple())
        timeNow = str(int(timeStamp1))
        timeStamp2 = time.mktime((datetime.now() - timedelta(days=1)).timetuple())
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
            # MACDCrossZero = False
            # MACDCrossSig = False
            volumecheck = True
            lastpair = dic.keys()[dic.values().index(j)]
            if lastpair in dontBuy:
                pass
            else:
                historicalData = conn.api_query("returnChartData",
                                                {"currencyPair": lastpair,
                                                 "start": timePast, "end": timeNow, "period": period})
                for count, i in enumerate(historicalData):
                    lowdata.append(i["low"])
                    highdata.append(i["high"])
                    if count > 20:
                        kData.append(oscillator(i["close"], lowdata, highdata))
                    emadata.append(i["close"])
                    if count > 264:  # Last 2 hour Volume Check for if its zero
                        if float(i["volume"]) == 0:
                            volumecheck = False
                histog = HIST(MACD(SEMA(emadata, 12), SEMA(emadata, 26)), SIG(MACD(SEMA(emadata, 12), SEMA(emadata, 26))))
                print lastpair
                # print "oscillator value: {}".format(float(MovingAv(kData, 3)[-1]))
                # if SEMA(emadata, 10)[-2] < SEMA(emadata, 40)[-2] and SEMA(emadata, 10)[-1] > SEMA(emadata, 40)[-1] and volumecheck and float(MovingAv(kData, 3)[-1]) < 20:
                if SEMA(emadata, 10)[-1] < SEMA(emadata, 40)[-1] and volumecheck and float(MovingAv(kData, 3)[-1]) < 20 and iscoingoesup(lastpair, 300, 6) > 0:
                    point += (20 - float(MovingAv(kData, 3)[-1]))
                    point += iscoingoesup(lastpair, 300, 6)
                    if (SEMA(emadata, 10)[-2] - SEMA(emadata, 40)[-2]) < (SEMA(emadata, 10)[-1] - SEMA(emadata, 40)[-1]):
                        point += 20
                    if histog[-4] <= histog[-3] <= histog[-2] < 0 < histog[-1]:
                        point += 20
                    possiblebuyList.append([lastpair, point])
                    if not coin:
                        coin = [lastpair, point]
                    elif point > coin[1]:
                        coin = [lastpair, point]

                # if SEMA(emadata, 10)[-1] < SEMA(emadata, 40)[-1] and volumecheck and float(
                #        MovingAv(kData, 3)[-1]) < 20 and iscoingoesup(lastpair, 300, 6) > 0:
                    ########### NOT HERE ###############
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
            possiblebuyList = []
            return None
        else:
            print possiblebuyList
            possiblebuyList = []
            return coin[0]
    except Exception as e:
        print e.__doc__
        print e.message
    finally:
        pass


def sellingTime(pair, period, boughtprice, lastprice):
    days = 1
    timeStamp1 = time.mktime(datetime.now().timetuple())
    timeNow = str(int(timeStamp1))
    timeStamp2 = time.mktime((datetime.now() - timedelta(days=days)).timetuple())
    timePast = str(int(timeStamp2))
    emadata = []
    lowdata = []
    highdata = []
    kData = []
    count = 0
    try:
        if (boughtprice * 1.003) < lastprice:  # %0,003 Fee cut calculated
            historicalData = conn.api_query("returnChartData",
                                            {"currencyPair": pair,
                                             "start": timePast, "end": timeNow, "period": period})
            for count, i in enumerate(historicalData):
                emadata.append(i["close"])
                lowdata.append(i["low"])
                highdata.append(i["high"])
                if count > 20:
                    kData.append(oscillator(i["close"], lowdata, highdata))
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

            # BURASI ESKI HALI VE CALISIYOR #
            if SEMA(emadata, 10)[-1] >= SEMA(emadata, 10)[-2] or (SEMA(emadata, 10)[-2] - SEMA(emadata, 40)[-2]) < (SEMA(emadata, 10)[-1] - SEMA(emadata, 40)[-1]):
                print "oscillator value: {}".format(float(MovingAv(kData, 3)[-1]))
                if float(MovingAv(kData, 3)[-1]) > 80:
                    return True
                else:
                    return False
            else:
                return True
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
    liveTestBuyingAmount = 0.01
    liveTestBtcBalance = 0.01
    liveTestAltBalance = 0
    liveTestAltBuyRate = 0
    period = 300
    buyingAmountinBTC = btcforBuying
    fee = .9975
    timebuyingtime = time.time()
    # bought = False
    # pair = None
    if liveTest:
        with open("AITraderLog.txt", "r") as logfile:
            log = str(logfile.readlines()[-1])
            if "BUY" in log:
                bought = True
                pair = log.split('#')[1]
                liveTestAltBalance = float(log.split('#')[7]) * fee
                liveTestAltBuyRate = float(log.split('#')[3])
                liveTestBuyingAmount = float(log.split('#')[5])
                print "Already Bought: {}".format(pair)
            else:
                print "New coin searching"
                bought = False
                pair = None
                liveTestAltBalance = 0
                liveTestAltBuyRate = 0
    else:
        with open("AITraderLog.txt", "r") as logfile:
            log = str(logfile.readlines()[-1])
            if "BUY" in log:
                bought = True
                pair = log.split('#')[1]
                altfee = float(log.split('#')[9])
                altBuyAmountTotal = float(log.split('#')[7]) * (1 - altfee)
                altBuyRate = float(log.split('#')[3])
                print "Already Bought: {}".format(pair)
            elif "SELL" in log:
                print "New coin searching"
                bought = False
                pair = None
                altBuyAmountTotal = 0
                altBuyRate = 0
            elif "PARTIAL" in log:
                print "Partial Sell Detected"
                bought = True
                pair = log.split('#')[1]
                altfee = float(log.split('#')[9])
                altBuyAmountTotal = float(log.split('#')[11]) * (1 - altfee)
                buyingAmountinBTC = float(log.split('#')[13])
                altBuyRate = float(log.split('#')[15])
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
            try:
                if pair is not None:
                    print "### {} ###".format(pair)
                    # mydata = DataAndTarget(pair, period, days)
                    # dfData = pd.DataFrame(mydata.returnData())
                    # dfTarget = pd.DataFrame(mydata.returnTarget())
                    # pd.DataFrame(dfData).to_csv('data_X_train.csv')
                    # predictions = predictor(dfData, dfTarget)

                    connection = conn.returnTicker()[pair]
                    lastpairprice = float(connection["last"])
                    print "*** Testing ***"
                    print "{}: {} Amount: {:.8f}, BTC Value: {:.8f}".format(datetime.now().replace(microsecond=0),
                                                                            pair,
                                                                            liveTestAltBalance,
                                                                            liveTestAltBalance * lastpairprice)

                    if bought:
                        print "Bought rate:\t{:.8f}".format(liveTestAltBuyRate)
                        if liveTestAltBuyRate < lastpairprice:
                            print "\t\t{:.8f} Raising %{:.2f}".format(lastpairprice - liveTestAltBuyRate,
                                                                      ((
                                                                               lastpairprice - liveTestAltBuyRate) / liveTestAltBuyRate) * 100)
                        elif liveTestAltBuyRate > lastpairprice:
                            print "\t\t{:.8f} Falling %{:.2f}".format(lastpairprice - liveTestAltBuyRate,
                                                                      ((
                                                                               lastpairprice - liveTestAltBuyRate) / liveTestAltBuyRate) * 100)
                        else:
                            print "\t\t\t{:.8f}".format(lastpairprice - liveTestAltBuyRate)
                        print "Lastpair rate:\t{:.8f}\n".format(lastpairprice)
                        # Buyin Selling StopLoss section
                        # StopLoss
                        if (liveTestAltBalance * lastpairprice) < liveTestBuyingAmount * .95:
                            liveTestBtcBalance += liveTestAltBalance * lastpairprice * fee
                            print "TEST STOPLOSS Sell Complete!\n"
                            print "\n{} #{}# TEST STOPLOSS rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#" \
                                .format(datetime.now().replace(microsecond=0), pair, lastpairprice,
                                        liveTestAltBalance * lastpairprice * fee, liveTestAltBalance)
                            with open("AITraderLog.txt", "a") as logfile:
                                logfile.write(
                                    "\n{} #{}# TEST STOPLOSS rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#"
                                    .format(datetime.now().replace(microsecond=0), pair, lastpairprice, liveTestAltBalance * lastpairprice * fee, liveTestAltBalance))
                            liveTestAltBalance = 0
                            pair = None
                            bought = False
                            timebuyingtime = time.time()
                        # Selling
                        # Prediction, Bought, Fee Passed.
                        # SellingTime Desicion method: buyAmount here is the amount of altcoin that bought below
                        elif (liveTestAltBalance * lastpairprice * .995) > liveTestBuyingAmount:  # and int(predictions[-1, 0]) == 0
                            if sellingTime(pair, period, lastpairprice, liveTestAltBuyRate):
                                liveTestBtcBalance += liveTestAltBalance * lastpairprice * fee
                                print "TEST Sell Order Complete!\n"
                                print "\n{} #{}# TEST SELL rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#" \
                                    .format(datetime.now().replace(microsecond=0), pair, lastpairprice,
                                            liveTestAltBalance * lastpairprice * fee, liveTestAltBalance)
                                with open("AITraderLog.txt", "a") as logfile:
                                    logfile.write(
                                        "\n{} #{}# TEST SELL rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#"
                                        .format(datetime.now().replace(microsecond=0), pair, lastpairprice, liveTestAltBalance * lastpairprice * fee, liveTestAltBalance))
                                liveTestAltBalance = 0
                                pair = None
                                bought = False
                                timebuyingtime = time.time()
                    # BUY BUY BUYING TIME
                    elif timebuyingtime + 300 >= time.time():
                        if bought is False:
                            liveTestAltBalance = (liveTestBuyingAmount / lastpairprice) * fee
                            liveTestAltBuyRate = lastpairprice
                            print " TEST Buy Order Complete\n"
                            bought = True
                            print "\n{} #{}# TEST BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#" \
                                .format(datetime.now().replace(microsecond=0), pair, liveTestAltBuyRate,
                                        liveTestBuyingAmount, liveTestAltBalance)
                            print ""
                            # Logging to a file
                            with open("AITraderLog.txt", "a") as logfile:
                                logfile.write("\n{} #{}# TEST BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}#"
                                              .format(datetime.now().replace(microsecond=0), pair,
                                                      liveTestAltBuyRate, liveTestBuyingAmount, liveTestAltBalance))
                            liveTestBtcBalance -= liveTestBuyingAmount
                    else:
                        timebuyingtime = time.time()
                        pair = None

                else:
                    timebuyingtime = time.time()
                    pair = buyingTime(period)

            except Exception as e:
                print e.__doc__
                print e.message
            finally:
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
                        # Buyin Selling StopLoss section
                        # StopLoss
                        if (altBuyAmountTotal * lastpairprice) < buyingAmountinBTC * .95:
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
                                pair = None
                                bought = False
                                altBuyAmountTotal = 0
                                altBuyRate = 0
                                timebuyingtime = time.time()
                            else:
                                print str(orderNumber["error"])
                        # Selling
                        # Prediction, Bought, Fee Passed.
                        # SellingTime Desicion method: buyAmount here is the amount of altcoin that bought below
                        # elif (altBuyAmountTotal * lastpairprice * .997) > buyingAmountinBTC:  # and int(predictions[-1, 0]) == 0:
                        if sellingTime(pair, period, altBuyRate, lastpairprice):
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
                                        bought = True
                                        altBuyAmountTotal = sellAmount - altSoldAmountTotal
                                        buyingAmountinBTC = buyingAmountinBTC - altSoldBTCTotal
                                        print "\n{} #{}# PARTIAL rate: #{:.8f}# val: #{:.8f}#(BTC) " \
                                              "amount: #{:.8f}# Fee: #{:.4f}# AltRemaining: #{:.8f}# BTC Remaining :#{:.8f}# AltBuyRate: #{}"\
                                            .format(datetime.now().replace(microsecond=0), pair, altSoldRate,
                                                    altSoldBTCTotal, altSoldAmountTotal, altfee, altBuyAmountTotal, buyingAmountinBTC, altBuyRate)
                                        with open("AITraderLog.txt", "a") as logfile:
                                            logfile.write("\n{} #{}# PARTIAL rate: #{:.8f}# val: #{:.8f}#(BTC) amount: "
                                                          "#{:.8f}# Fee: #{:.4f}# AltRemaining: #{:.8f}# BTC Remaining :#{:.8f}# AltBuyRate: #{}"
                                                          .format(datetime.now().replace(microsecond=0), pair, altSoldRate,
                                                                  altSoldBTCTotal, altSoldAmountTotal, altfee,
                                                                  altBuyAmountTotal, buyingAmountinBTC, altBuyRate))
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
                                        pair = None
                                        bought = False
                                        altBuyAmountTotal = 0
                                        buyingAmountinBTC = btcforBuying
                                        altBuyRate = 0
                                        timebuyingtime = time.time()
                                elif "error" in orderNumber:
                                    print orderNumber["error"]
                                else:
                                    print "Cancelling {} Sell Order".format(pair)
                                    conn.cancel(pair, orderNumber["orderNumber"])
                                    bought = True
                            else:
                                print "Could't find any Ask position for " + str(pair) + "\n"
                    elif timebuyingtime + 300 >= time.time():
                        # Buying
                        # Choosing best coin with buyingtime method
                        if bought is False:
                            bidrate = bidratefinder(pair, conn)
                            if bidrate:
                                orderNumber = conn.buy(pair, bidrate, (buyingAmountinBTC / bidrate), 0, 1)
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
                                            altBuyBTCTotal += altBuyBTCvalue
                                        if round(altBuyAmountTotal, 7) >= round(((buyingAmountinBTC / bidrate) * (1 - altfee)), 7):
                                            break
                                        time.sleep(1)
                                    print "\n{} #{}# BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}#" \
                                          .format(datetime.now().replace(microsecond=0), pair, altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee)
                                    print ""
                                    # Logging to a file
                                    with open("AITraderLog.txt", "a") as logfile:
                                        logfile.write("\n{} #{}# BUY rate: #{:.8f}# val: #{:.8f}#(BTC) amount: #{:.8f}# Fee: #{:.4f}#"
                                                      .format(datetime.now().replace(microsecond=0), pair, altBuyRate, altBuyBTCTotal, altBuyAmountTotal, altfee))
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
                        timebuyingtime = time.time()
                        pair = None

                else:
                    timebuyingtime = time.time()
                    pair = buyingTime(period)

            except Exception as e:
                print e.__doc__
                print e.message
            finally:
                pass


if __name__ == "__main__":
    main()
