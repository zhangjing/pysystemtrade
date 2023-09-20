from sysbrokers.CTP.ctp_connection import connectionCTP
from sysbrokers.broker_capital_data import brokerCapitalData
from sysdata.data_blob import dataBlob
from syscore.constants import arg_not_supplied

from sysobjects.spot_fx_prices import listOfCurrencyValues, currencyValue

from syslogdiag.pst_logger import pst_logger
from syslogdiag.log_to_screen import logtoscreen


class ctpCapitalData(brokerCapitalData):
    def __init__(
        self,
        ctpconnection: connectionCTP,
        data: dataBlob,
        log: pst_logger = logtoscreen("ctpCapitalData"),
    ):
        super().__init__(log=log, data=data)
        self._ctpconnection = ctpconnection

    @property
    def ctp_connection(self) -> connectionCTP:
        return self._ctpconnection

    @property
    def ctp_client(self):
        return self._ctpconnection.ctp

    def __repr__(self):
        return "CTP capital data"

    def get_account_value_across_currency(
        self, account_id: str = arg_not_supplied
    ) -> listOfCurrencyValues:
        status, data, error = self.ctp_client.td_api.trading_account_sync()
        if status:
            return [currencyValue('CNH', data['PreDeposit'])]
        else:
            return None

    def get_excess_liquidity_value_across_currency(
        self, account_id: str = arg_not_supplied
    ) -> listOfCurrencyValues:
        status, data, error = self.ctp_client.td_api.trading_account_sync()
        if status:
            return [currencyValue('CNH', data['PreDeposit'])]
        else:
            return None

    """
    Can add other functions not in parent class to get IB specific stuff which could be required for
      strategy decomposition
    """
