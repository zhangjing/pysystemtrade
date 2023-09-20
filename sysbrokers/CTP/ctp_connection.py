"""
IB connection using ib-insync https://ib-insync.readthedocs.io/api.html

"""

import time
import datetime

from sysbrokers.CTP.ctp_insync import CTP

from sysbrokers.CTP.ctp_connection_defaults import ctp_defaults
from syscore.exceptions import missingData
from syscore.constants import arg_not_supplied

from syslogdiag.log_to_screen import logtoscreen
from syslogdiag.pst_logger import pst_logger, BROKER_LOG_LABEL, CLIENTID_LOG_LABEL

class connectionCTP(object):
    """
    Connection object for connecting CTP
    (A database plug in will need to be added for streaming prices)
    """

    def __init__(
        self,
        ctp_trader_server: str = arg_not_supplied,
        ctp_md_server: str = arg_not_supplied,
        ctp_broker_id: str = arg_not_supplied,
        ctp_app_id: str = arg_not_supplied,
        ctp_auth_code: str = arg_not_supplied,
        ctp_user_id: str = arg_not_supplied,
        ctp_password: str = arg_not_supplied,
        log: pst_logger = logtoscreen("connectionCTP"),
    ):
        """
        :param client_id: client id
        :param ipaddress: IP address of machine running IB Gateway or TWS. If not passed then will get from private config file, or defaults
        :param port: Port listened to by IB Gateway or TWS
        :param log: logging object
        :param mongo_db: mongoDB connection
        """

        # resolve defaults
        self._ctp_connection_config = ctp_defaults(ctp_trader_server=ctp_trader_server, ctp_md_server=ctp_md_server, ctp_broker_id=ctp_broker_id,
                                                   ctp_app_id=ctp_app_id, ctp_auth_code=ctp_auth_code,
                                                   ctp_user_id=ctp_user_id, ctp_password=ctp_password,)

        # If you copy for another broker include these lines
        self._init_log(log, datetime.datetime.now().strftime('%Y%m%d:%H:%M:%S'))

        self._init_connection(self._ctp_connection_config)

    def _init_log(self, log, client_id):
        new_log = log.setup_empty_except_keep_type()
        new_log.label(**{BROKER_LOG_LABEL: "CTP", CLIENTID_LOG_LABEL: client_id})
        self._log = new_log

    def _init_connection(self, ctp_connection_config):
        ctp = CTP(ctp_connection_config['ctp_data_dir'], ctp_connection_config['ctp_trader_server'],
                  ctp_connection_config['ctp_md_server'], ctp_connection_config['ctp_broker_id'],
                  ctp_connection_config['ctp_app_id'], ctp_connection_config['ctp_auth_code'],
                  ctp_connection_config['ctp_user_id'], ctp_connection_config['ctp_password'])

        status, data, error = ctp.connect()
        if not status:
            raise Exception(f'status:{status} data:{data} error:{error}')

        self._ctp = ctp
    @property
    def ctp(self):
        return self._ctp

    @property
    def log(self):
        return self._log

    def __repr__(self):
        return "CTP broker connection" + str(self._ctp_connection_config)

    def client_id(self):
        return self._ctp_connection_config["client"]

    def close_connection(self):
        self.log.msg("Terminating %s" % str(self._ctp_connection_config))
        try:
            # Try and disconnect IB client
            self.ctp.disconnect()
        except BaseException:
            self.log.warn(
                "Trying to disconnect IB client failed... ensure process is killed"
            )
