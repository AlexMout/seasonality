from flask import Flask, render_template, request
from Engie.FlaskApp.model import database_queries

app = Flask(__name__)


@app.route('/')
def main_page():
    products, maturities, error = database_queries.get_data()
    # print(products ,maturities)
    # print(maturities)
    return render_template("index.html",
                           page_title="Seasonality Charting Tool",
                           title="PT DESK TOOL",
                           products=products,
                           contracts=["Quarters", "Months", "Cal", "Quarters Spread", "Cal Spread"],
                           maturities=maturities,
                           error_message=[error])  # dictionary => {'granularity':[list of available maturities]}


@app.route("/get_chart", methods=['POST'])
def display_chart():
    product, contract, maturity = request.form.get("product_selected", "TTF"), request.form.get("contract_selected",
                                                                                                "Cal"), request.form.get(
        "maturity_selected", "CAL14")

    overlap_data = request.form.get("overlap-checkbox") is not None
    # print(product, contract, maturity)
    quotes, dates, error, returns, volatilities, minimums, maximums, ratios = database_queries.get_prices(product,
                                                                                                          contract,
                                                                                                          maturity,
                                                                                                          overlap_data)
    """print(quotes)
    print(dates)
    print("Returns : {}".format(returns))
    print("Vol : {}".format(volatilities))
    print("Min {}".format(minimums))
    print("Error : {}".format(error))"""

    return render_template("chart_page.html", page_title="Chart " + product, quotes=quotes, dates=dates,
                           product=[product], contract=[contract], error_message=[error], returns=returns,
                           volatilities=volatilities, ratios=ratios, minimums=minimums, maximums=maximums,
                           overlap_data=[str(overlap_data)])


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error-404.html", page_title="Not found...")

if __name__ == "__main__":
    app.run()
