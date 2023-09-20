import vnpy_ctp
from vnpy_ctp.api import TdApi, MdApi
import time
from threading import Lock

class CTP():

    def __init__(self, data_dir, trader_server, md_server, broker_id, auth_code, app_id, user_id, password):
        super().__init__()
        self.td_api = CtpTdApi(data_dir, trader_server, broker_id, auth_code, app_id, user_id, password)

    def connect(self):
        status, data, error = self.td_api.connect_auth_login_settlement_confirm_sync()
        return status, data, error

    def disconnect(self):
        status, data, error = self.td_api.logout_sync()
        return status, data, error


class CtpTdApi(TdApi):
    def __init__(self, data_dir, address, broker_id, auth_code, app_id, user_id, password):
        super().__init__()
        self.data_dir = data_dir
        self.address = address
        self.broker_id = broker_id
        self.auth_code = auth_code
        self.app_id = app_id
        self.user_id = user_id
        self.password = password

        self.reqid: int = 0
        self.req_dict_lock = Lock()
        self.req_dict = {}


        self.order_ref: int = 0

        self.connect_status = 0 # -1 disconnect, 0 init status; 1 connectting; 2 connected


        self.login_status: bool = False
        self.auth_status: bool = False
        self.login_failed: bool = False
        self.auth_failed: bool = False
        self.contract_inited: bool = False

        self.frontid: int = 0
        self.sessionid: int = 0
        self.order_data: List[dict] = []
        self.trade_data: List[dict] = []
        self.positions: Dict[str, PositionData] = {}
        self.sysid_orderid_map: Dict[str, str] = {}

    def get_reqid_ret(self, reqid, timeout=2, inc=0.2):
        while timeout > 0:
            with self.req_dict_lock:
                if reqid in self.req_dict:
                    data = self.req_dict[reqid]
                    #delete key
                    del self.req_dict[reqid]
                    return data
            time.sleep(inc)
            timeout = timeout - inc

        return False, {}, {"ErrorMsg" : f'timeout:{timeout}', "ErrorID" : 1}

    def push_reqid(self, reqid, data, error):
        with self.req_dict_lock:
            self.req_dict[reqid] = [('ErrorID' not in error) or (error['ErrorID'] ==0), data, error]

    def connect(self) -> None:
        if self.connect_status == 0:
            self.createFtdcTraderApi(self.data_dir)
            self.subscribePrivateTopic(0)
            self.subscribePublicTopic(0)
            self.registerFront(self.address)
            self.init()
            self.connect_status = 1

    def connect_sync(self):
        self.connect()
        sleep_time = 0
        while sleep_time < 2:
            if self.connect_status == 2:
                return True
            else:
                inc = 0.2
                sleep_time += inc
                time.sleep(inc)
        return False

    def onFrontConnected(self) -> None:
        self.connect_status = 2

    def onFrontDisconnected(self, reason: int) -> None:
        self.connect_status = -1


    def authenticate(self):
        """发起授权验证"""
        if self.auth_failed:
            return

        ctp_req: dict = {
            "UserID": self.user_id,
            "BrokerID": self.broker_id,
            "AuthCode": self.auth_code,
            "AppID": self.app_id
        }

        self.reqid += 1
        self.reqAuthenticate(ctp_req, self.reqid)
        return self.reqid


    def authenticate_sync(self):
        reqid = self.authenticate()
        return self.get_reqid_ret(reqid)


    def onRspAuthenticate(self, data: dict, error: dict, reqid: int, last: bool) -> None:
        """用户授权验证回报"""
        if not error['ErrorID']:
            with self.req_dict_lock:
                self.req_dict[reqid] = [True, data, error]
        else:
            with self.req_dict_lock:
                self.req_dict[reqid] = [False, data, error]


    def login(self):
        ctp_req: dict = {
            "UserID": self.user_id,
            "Password": self.password,
            "BrokerID": self.broker_id,
            "AppID": self.app_id
        }

        self.reqid += 1
        self.reqUserLogin(ctp_req, self.reqid)
        return self.reqid

    def login_sync(self):
        reqid = self.login()
        return self.get_reqid_ret(reqid)

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool) -> None:
        if not error["ErrorID"]:
            with self.req_dict_lock:
                self.req_dict[reqid] = [True, data, error]
            self.front_id = data["FrontID"]
            self.session_id = data["SessionID"]
        else:
            with self.req_dict_lock:
                self.req_dict[reqid] = [False, data, error]

    def logout(self):
        ctp_req: dict = {
            "UserID": self.user_id,
            "BrokerID": self.broker_id
        }
        self.reqid += 1
        self.reqUserLogout(ctp_req, self.reqid)
        return self.reqid

    def logout_sync(self):
        reqid = self.logout()
        return self.get_reqid_ret(reqid)

    def onRspUserLogout(self, data, error, reqid, last):
        self.push_reqid(reqid, data, error)

    def settlement_info_confirm(self):
        # 自动确认结算单
        ctp_req: dict = {
            "BrokerID": self.broker_id,
            "InvestorID": self.user_id
        }
        self.reqid += 1
        self.reqSettlementInfoConfirm(ctp_req, self.reqid)
        return self.reqid

    def settlement_info_confirm_sync(self):
        reqid = self.settlement_info_confirm()
        return self.get_reqid_ret(reqid)

    def onRspSettlementInfoConfirm(self, data, error, reqid, last):
        self.push_reqid(reqid, data, error)

    def connect_auth_login_settlement_confirm_sync(self):
        if self.connect_sync():
            status, data, error = self.authenticate_sync()
            if status:
                status, data, error = self.login_sync()
                if status:
                    status, data, error = self.settlement_info_confirm_sync()
            return status, data, error
        else:
            return False, {}, {}
        return status, data, error
    def trading_account(self):
        ctp_req: dict = {
            "BrokerID": self.broker_id,
            "InvestorID": self.user_id,
            "CurrencyID": "CNY"
        }
        self.reqid += 1
        self.reqQryTradingAccount(ctp_req, self.reqid)
        return self.reqid

    def trading_account_sync(self):
        reqid = self.trading_account()
        return self.get_reqid_ret(reqid)

    def onRspQryTradingAccount(self, data: dict, error: dict, reqid: int, last: bool) -> None:
        self.push_reqid(reqid, data, error)

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctp import CtpGateway


def main():
    """主入口函数"""
    #qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(CtpGateway)
    setting = {"用户名":'300014141', "密码":'iVVR@cFPV43ht3b', "经纪商代码":'4900', "交易服务器":'tcp://222.92.185.26:41206',
               "行情服务器":'tcp://222.92.185.26:41214', "产品名称":'client_pytrade_001', "授权编码":'BYB49PSHYPSKK3VR'}
    main_engine.connect(setting,'CTP')
    #main_engine.
    #main_window = MainWindow(main_engine, event_engine)
    #main_window.showMaximized()

    #qapp.exec()

if __name__ == "__main__":
    #my_ctp = CTP('flow/01', 'tcp://222.92.185.26:41206', '', '4900', 'BYB49PSHYPSKK3VR',
    #             'client_pytrade_001', '300014141', 'iVVR@cFPV43ht3b')
    #第二套
    my_ctp = CTP('flow/01', 'tcp://218.202.237.33:10203', 'tcp://218.202.237.33:10213', '9999', '0000000000000000',
                 'simnow_client_test', '214179', 'iVVR@cFPV43ht3b')
    print(my_ctp.connect())
    print(my_ctp.td_api.trading_account_sync())
    print(f'logout:{my_ctp.td_api.logout_sync()}')
    #tdapi_obj = CtpTdApi('flow/01', 'tcp://222.92.185.26:41206', '4900', 'BYB49PSHYPSKK3VR', 'client_pytrade_001', '300014141', 'iVVR@cFPV43ht3b')
    # #dongwu


    # #simnow
    # #tdapi_obj.connect('tcp://218.202.237.33:10203', '214179', 'iVVR@cFPV43ht3b', '9999', '0000000000000000', 'simnow_client_test')
    # print(tdapi_obj.reqQryTradingAccount({}, 12))
    # time.sleep(5)
    #main()


