"""
An example interface designed to be imported in your projects as a library.
"""

import urllib.request
import ssl
import json
from typing import List, Dict, Any
import pandas as pd
import numpy as np


class APIError(Exception):
    def __init__(self, message: str, correlation_id: str = None):
        self.message = message
        self.correlation_id = correlation_id
        super().__init__(message)


class FinancialDataAPI:
    def __init__(self, certificate_path: str):
        self.url = "https://web.api.six-group.com/api/findata"
        self.headers = {"accept": "application/json"}
        self.context = ssl.SSLContext()
        self.context.load_cert_chain(
            f"{certificate_path}/signed-certificate.pem",
            f"{certificate_path}/private-key.pem",
        )

    def _http_request(
        self, end_point: str, query_string: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make an HTTP request and send the raw response.
        """
        complete_url = f"{self.url}{end_point}?{urllib.parse.urlencode(query_string)}"
        try:
            request = urllib.request.Request(complete_url, headers=self.headers)
            with urllib.request.urlopen(request, context=self.context) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as err:
            correlation_id = err.headers.get("X-CorrelationID")
            raise APIError(
                "An error occurred during the API request.", correlation_id
            ) from err

    def _http_request_with_scheme_id(
        self, end_point: str, scheme: str, ids: List[str]
    ) -> Dict[str, Any]:
        """
        Make an HTTP request using scheme and ids.
        """
        query_string = {"scheme": scheme, "ids": ",".join(ids)}
        return self._http_request(end_point, query_string)

    def instrumentBase(self, scheme: str, instruments: List[str]) -> Dict[str, Any]:
        """
        Retrieve instrument basic attributes using scheme and ids.
        """
        end_point = "/v1/listings/referenceData/instrumentBase"  # "/v1/instruments/referenceData/instrumentBase"
        return self._http_request_with_scheme_id(end_point, scheme, instruments)

    def instrumentMarkets(self, scheme: str, instruments: List[str]) -> Dict[str, Any]:
        """
        Retrive markets in which instruments are listed
        """
        end_point = "/v1/instruments/referenceData/instrumentMarkets"
        return self._http_request_with_scheme_id(end_point, scheme, instruments)

    def endOfDayHistory(
        self,
        scheme: str,
        listings: List[str],
        dateFrom: str,
        dateTo: str = "",
    ) -> Dict[str, Any]:
        """
        Retrieve End of Day Timeseries data.
        """
        end_point = "/v1/listings/marketData/endOfDayHistory"
        query_string = {
            "scheme": scheme,
            "ids": ",".join(listings),
            "dateFrom": dateFrom,
            "dateTo": dateTo,
        }
        return self._http_request(end_point, query_string)


def get_data(
    financial_object: FinancialDataAPI,
    instruments: list[str],
    start_date: str,
    end_date: str,
):
    """
    inputs:
        financial_object: instance of FinancialDataAPI
        instruments: list of intruments (with BC suffix)
        start_date/end_date: range time
    output:
        data: dictionary {lookup, lookupStatus, marketData}
    """

    # get data
    data = financial_object.endOfDayHistory(
        "ISIN_BC", instruments, start_date, end_date
    )
    data = json.dumps(data, sort_keys=True, indent=4)
    data = json.loads(data)["data"]["listings"]

    return data


def get_markets_correct_currency(
    financial_object: FinancialDataAPI,
    scheme: str,
    instruments: list[str],
    accessible_markets: list[int],
    currency: str = "CHF",
):
    """get the markets bc in which the fund is in the given currency"""
    # get instrument with bc on all markets
    instruments_bc_all_markets = [
        [instruments[i] + f"_{bc}" for i, bc in enumerate(accessible_markets[j])]
        for j in range(len(accessible_markets))
    ]

    # flatten
    instruments_bc_all_markets = [
        item for sublist in instruments_bc_all_markets for item in sublist
    ]

    # get data
    data = financial_object.instrumentBase(
        scheme,
        [markets for markets in instruments_bc_all_markets],
    )

    def get_currency(data):
        try:
            return data["lookup"]["listingCurrency"] == currency
        except:
            return False

    # keep currency given
    to_keep = list(
        map(
            lambda dict_: get_currency(dict_),
            data["data"]["listings"],
        )
    )
    data = list(
        set(
            [
                market
                for i, market in enumerate(instruments_bc_all_markets)
                if to_keep[i]
            ]
        )
    )

    # keep only one from market
    data = list(
        map(
            lambda l: "_".join(l),
            pd.DataFrame(list(map(lambda s: s.split("_"), data)))
            .drop_duplicates(subset=[0])
            .to_numpy(),
        )
    )

    return data


def get_accessible_markets_bc(
    financial_object: FinancialDataAPI,
    scheme: str,
    instruments: list[str],
    accessible_markets: pd.DataFrame,
) -> list[str]:
    """
    get usable bc of instruments
    """

    def get_bc(dict_):
        return list(map(lambda val: val["bc"], dict_))

    data = financial_object.instrumentMarkets(scheme, instruments)
    all_markets_bc = list(
        map(
            lambda inst_dict: get_bc(inst_dict["referenceData"]["instrumentMarkets"]),
            data["data"]["instruments"],
        )
    )

    def check_accessible(markets: list[int], accessible_markets: list[int]):
        return [bc for bc in markets if bc in accessible_markets]

    return list(map(lambda x: check_accessible(x, accessible_markets), all_markets_bc))


def get_financial_ts(data):
    """return only financial time series

    input:
        data: dictionary
    """

    def get_price(dict_):
        try:
            return list(
                map(lambda l: l["close"], dict_["marketData"]["endOfDayHistory"])
            )
        except:
            return [-1]

    prices = list(map(lambda dict_: get_price(dict_), data))
    prices = np.array([item for sublist in prices for item in sublist])

    temp = list(
        map(
            lambda l: (
                np.full(len(l["marketData"]["endOfDayHistory"]), get_instrument_name(l))
                if len(l["marketData"]["endOfDayHistory"]) != 0
                else [1]
            ),
            data,
        )
    )

    def get_date(dict_):
        try:
            # print(dict_)
            return list(map(lambda l: l["sessionDate"], dict_))
        except:
            return [-1]

    dates = list(map(lambda l: get_date(l["marketData"]["endOfDayHistory"]), data))
    dates = np.array([item for sublist in dates for item in sublist])

    temp = np.array([item for sublist in temp for item in sublist])

    # inst = np.array(
    #     list(
    #         map(
    #             lambda dict_: (
    #                 np.full(
    #                     len(dict_["marketData"]["endOfDayHistory"]),
    #                     dict_["requestedId"],
    #                 )
    #                 if len(dict_["marketData"]["endOfDayHistory"]) != 0
    #                 else [1]
    #             ),
    #             data,
    #         )
    #     )
    # )
    return dates, prices, temp

    # instrument_isin = data["requestedId"].split("_")[0]
    # instrument_name = f"{get_instrument_name(data)} ({instrument_isin})"
    # data_plot = pd.DataFrame(
    #     columns=["date", "close_price", "instrument_isin", "instrument_name"]
    # )
    # for i, dict_ in enumerate(data["marketData"]["endOfDayHistory"]):
    #     try:
    #         tmp = pd.DataFrame(
    #             [
    #                 [
    #                     dict_["sessionDate"],
    #                     dict_["close"],
    #                     instrument_isin,
    #                     instrument_name,
    #                 ]
    #             ],
    #             columns=data_plot.columns,
    #         )
    #         data_plot = pd.concat([data_plot, tmp], axis=0)
    #     except:
    #         pass
    # return data_plot.reset_index(drop=True)


def get_instrument_name(data_instrument: Dict) -> str:
    """returns the name of the instrument given"""
    return data_instrument["lookup"]["listingShortName"]

def get_instrument_name(data_instrument: Dict):
    return data_instrument["lookup"]["listingShortName"]


if __name__ == "__main__":
    dir = "SIXWebAPI/CH52991-hackathon7"
    findata = FinancialDataAPI(dir)

    sample1 = findata.instrumentBase("ISIN", ["BE6342120662"])
    print(json.dumps(sample1, sort_keys=True, indent=4))
