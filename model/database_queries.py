from pydocumentdb import document_client
from Engie.FlaskApp.model import parameters as keys
from Engie.FlaskApp.model import calcutalor
import datetime as dt
import itertools

client = document_client.DocumentClient(keys.COSMOSDB_HOST, {'masterKey': keys.COSMOSDB_KEY})

def get_data():
    """Function that retrieves all the available contracts and maturities for each products in the Azure database"""
    products = []
    maturities = {}
    error_message = ""
    try:
        # GET THE DATABASE LINK :
        db_query = "SELECT * FROM database WHERE database.id = '{0}'".format(keys.COSMOSDB_DATABASE)
        db = list(client.QueryDatabases(db_query))[0]
        db_link = db["_self"]

        # GET ALL THE COLLECTIONS IDs :
        coll_query = "SELECT collections.id FROM collections"
        coll = list(client.QueryCollections(db_link, coll_query))
        print(coll)

        # If nothing has been found
        if not coll:
            raise ValueError("No collection retrieved.")

        for data in coll:
            products.append(data["id"].split("_")[0])

        # GET THE COLLECTION LINK
        coll_query = "SELECT * FROM collections WHERE collections.id = '{0}'".format(products[0] + "_prices")
        coll = list(client.QueryCollections(db_link, coll_query))[0]
        coll_link = coll["_self"]

        # GET ALL THE DOCUMENTS IDs INSIDE THE COLLECTION :
        doc_query = "SELECT r.id FROM r"

        docs = list(client.QueryDocuments(coll_link, doc_query))
        # [{'id': 'TTF_Months_Fixed_Contracts'}, {'id': 'TTF_Quarters_Fixed_Contracts'}, {'id': 'TTF_Cal_Fixed_Contracts'}]

        if not docs:
            raise ValueError("No document found in the database!")

        for data in docs:
            maturities[data["id"].split("_")[1]] = []  # ex : maturities["Months"] = []

            doc_query = "SELECT r.timeseriesData FROM r WHERE r.id = '{}'".format(data["id"])
            docs_query = list(client.QueryDocuments(coll_link, doc_query))[0]

            # For each type of contracts (cal, month, quarters), we add all the maturities availables to the corresponding list
            for timeSeries in docs_query["timeseriesData"]:
                if data["id"].split("_")[1] == "Months":
                    maturities[data["id"].split("_")[1]].append(timeSeries["maturity"][0:3])
                elif data["id"].split("_")[1] == "Quarters":
                    maturities[data["id"].split("_")[1]].append(timeSeries["maturity"][0:2])
                else:
                    maturities[data["id"].split("_")[1]].append(timeSeries["maturity"])

            # We keep unique elements :
            maturities[data["id"].split("_")[1]] = sorted(list(set(maturities[data["id"].split("_")[1]])))

        # Retrieve all the spread fields :
        maturities = get_spread_field(maturities)

    except Exception as e:
        error_message = e.args + "\nFile : database_queries.py / Function : get_data"

    finally:
        return products, maturities, error_message


def get_spread_field(maturities):
    """Functions that build the list of available spreads for each kind of spread :

    ex : Quarters Spread : Q1xQ2 Q1xQ3 Q1xQ4 Q2xQ3...

    """
    quarters_spreads = list(itertools.combinations(maturities["Quarters"], 2))
    quarters_spreads = ["{0}x{1}".format(elem[0], elem[1]) for elem in quarters_spreads]
    maturities["Quarters Spread"] = quarters_spreads
    return maturities


def get_prices(product, contract, maturity, overlap_data):
    """Retrieve all the quotes for the selected contract. The data are sent to a javascript function that generates
    an interactive plot with plotly."""

    quotes = {}
    dates = {}
    returns = {}
    volatilities = {}
    ratios = {}
    minimums = {}
    maximums = {}
    error_message = ""
    DAYS_IN_YEAR_CNST = 365.2425

    try:
        # GET THE DATABASE LINK : MarketData
        db_query = "SELECT * FROM database WHERE database.id = '{0}'".format(keys.COSMOSDB_DATABASE)
        db = list(client.QueryDatabases(db_query))[0]
        db_link = db["_self"]

        # GET THE COLLECTION LINK : ex : TTF_prices
        coll_query = "SELECT * FROM collections WHERE collections.id = '{0}'".format(product + "_prices")
        coll = list(client.QueryCollections(db_link, coll_query))[0]
        coll_link = coll["_self"]

        # Boolean variable that indicates whether we are looking for a spread or not
        # If contract is "Quarters Spread" we put "Quarters" instead in order to make the query to azure
        is_spread = contract in ["Quarters Spread", "Cal Spread"]
        contract = contract.split(" ")[0] if "Spread" in contract else contract

        # GET ALL THE DATA FROM A DOCUMENT :
        doc_query = "SELECT r.timeseriesData FROM r WHERE r.id = '{0}'".format(
            product + "_" + contract + "_Fixed_Contracts")
        doc = list(client.QueryDocuments(coll_link, doc_query))[0]

        index_string = 3
        if contract == "Quarters":
            index_string = 2

        for data in doc["timeseriesData"]:
            close_prices = []
            datetime = []
            date = None
            # We take only the data that matches the selected quarter (Q1, Q2, Q3 or Q4) or Month (Jan, Feb...) or CAL
            if (not is_spread and data["maturity"][0:index_string] == maturity[0:3]) or (
                    is_spread and (data["maturity"][0:index_string] in maturity.split("x") or data["maturity"][
                                                                                              0:index_string] == "CAL")) and \
                    data[
                        "dataPoints"]:

                for daily_prices in data["dataPoints"]:
                    # Get rid of None value => raise Error when given to HTML template
                    price = daily_prices[4] if daily_prices[4] is not None else 0
                    date = daily_prices[0]
                    if overlap_data:
                        # If the user choose to overlap the curves, we artificially set the same year for every price
                        # dataset and then we only display the month on the chart
                        date = dt.datetime.strptime(daily_prices[0][0:10], "%Y-%m-%d")
                        date -= dt.timedelta(days=int(data["maturity"][index_string:]) * DAYS_IN_YEAR_CNST)
                        date = date.strftime("%Y-%m-%d")
                    # datetime.append(dt.datetime.strptime(daily_prices[0][0:10], "%Y-%m-%d").strftime("%d %b"))
                    datetime.append(date)
                    close_prices.append(price)

                # Filling missing values for closing price with a linear interpolation :
                close_prices = calcutalor.Calculator.fillna_linear_interp(dataset=close_prices)

                quotes[data["maturity"]] = close_prices
                dates[data["maturity"]] = datetime

        if is_spread:
            dates, quotes = get_spread(quotes, dates, contract)

        # We compute some basic stats on the closing prices for each maturity
        returns, volatilities, minimums, maximums, ratios = calcutalor.Calculator.get_statistics(dataset=quotes)

    except Exception as e:
        error_message = e.args + "\nFile : database_queries.py / Function : get_prices"
        print(error_message)
        quotes = {}
        dates = {}
        returns = {}
        volatilities = {}
        ratios = {}
        minimums = {}
        maximums = {}

    finally:
        return quotes, dates, error_message, returns, volatilities, minimums, maximums, ratios


def get_spread(quotes, dates, contract):
    """Methods that computes the quarters spreads given the quotes and dates. It has to find the dates that are
    in both quarter time series. Example, for Q1xQ2, we compute the spread only for the dates that exist in the Q1 and Q2
    time series.

    Comments in code below are done for an example for Q1 and Q2
    """

    # for quarter1, quarter2 in zip(list(dates.keys()), list(dates.keys()[1:])):

    new_quotes = {}
    new_dates = {}

    dates_keys = list(dates.keys())

    step = 2 if contract == "Quarters" else 1

    for index in range(0, len(dates_keys) - 1, step):
        current_key = dates_keys[index]  # Q1 key
        key_after = dates_keys[index + 1]  # Q2 key

        first_date = dates[key_after][0]  # Get the first date of the Q2 time series

        try:
            index_first_date = dates[current_key].index(first_date)
            key_spread = "{}x{}".format(current_key, key_after)

            new_dates[key_spread] = []
            new_quotes[key_spread] = []

            offset_1 = 0
            offset_2 = 0

            # we go through all the days in the Q2 days list and add the common days and spread into the new lists
            for index_days in range(len(dates[key_after])):
                if dates[current_key][index_first_date + index_days + offset_1] == dates[key_after][
                    index_days + offset_2]:
                    new_dates[key_spread].append(dates[key_after][index_days + offset_1])
                    new_quotes[key_spread].append(
                        quotes[current_key][index_first_date + index_days + offset_1] - quotes[key_after][
                            index_days + offset_2])

                else:
                    date_1 = dt.datetime.strptime(dates[current_key][index_first_date + offset_1], "%Y-%m-%dT00:00:00Z")
                    date_2 = dt.datetime.strptime(dates[key_after][index_first_date + offset_2], "%Y-%m-%dT00:00:00Z")

                    while date_1 != date_2 and offset_1 < 10 and offset_2 < 10:
                        if date_1 > date_2:
                            offset_2 += 1
                        else:
                            offset_1 += 1

                    if date_1 != date_2:
                        continue

                    new_dates[key_spread].append(dates[key_after][index_days + offset_1])
                    new_quotes[key_spread].append(
                        quotes[current_key][index_first_date + index_days + offset_1] - quotes[key_after][
                            index_days + offset_2])


            #check_date(new_dates,new_quotes,quotes,dates)
        except IndexError:
            continue
        except Exception as e:
            print("Exception : {}".format(e.args))
            print("No overlap for {} and {}".format(current_key, key_after))
            continue

    return new_dates, new_quotes


def check_date(new_dates, new_quotes, quotes, dates):
    key = list(new_dates.keys())[0]
    print("Check dates..")
    for index in new_dates[key]:
        d1 = new_dates[key][index]
        p1 = new_quotes[key][index]
        try:
            index_real = dates[key].index(d1)
            p_real = quotes[key][index_real]
            if p1 != p_real:
                print("Date : {} - Real price : {} - Retrieved price : {}".format(d1, p_real, p1))
        except:
            print("Problem with {}".format(new_dates[key][index]))
