from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.CTP.ctp_connection import connectionCTP
from sysbrokers.CTP.client.ctp_client import ctpClient
from sysbrokers.broker_static_data import brokerStaticData
from sysdata.data_blob import dataBlob


class ctpStaticData(brokerStaticData):
    def __init__(
        self,
        ctpconnection: connectionCTP,
        data: dataBlob,
        log=logtoscreen("ctpStaticData"),
    ):
        super().__init__(log=log, data=data)
        self._ctpconnection = ctpconnection

    def __repr__(self):
        return "CTP static data %s" % str(self.ib_client)

    @property
    def ctpconnection(self) -> connectionCTP:
        return self._ctpconnection

    @property
    def ctp_client(self) -> ctpClient:
        client = getattr(self, "_ctp_client", None)
        if client is None:
            client = self._ctp_client = ctpClient(
                ctpconnection=self.ctpconnection, log=self.log
            )

        return client

    def get_broker_clientid(self) -> int:
        return 0

    def get_broker_account(self) -> str:
        return self.ctpconnection._ctp_connection_config['ctp_user_id']

    def get_broker_name(self) -> str:
        return "CTP"
