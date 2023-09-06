import datetime

from syscore.exceptions import missingData
from syscore.constants import named_object, success
from sysdata.base_data import baseData
from syslogdiag.log_to_screen import logtoscreen


class priceUpdateInfoData(baseData):
    def __init__(self, log=logtoscreen("priceUpdateInfoData")):
        super().__init__(log=log)
        self._update_info_store = dict()

    def get_dict_of_control_processes(self):
        list_of_names = self.get_list_of_instruments()
        output_dict = dict(
            [
                (instrument, self.get_update_info_for_instrument(instrument))
                for instrument in list_of_names
            ]
        )

        return output_dict

    def get_list_of_instrument(self) -> list:
        return list(self._update_info_store.keys())

    def get_update_info_for_instrument(self, instrument):
        try:
            update_info = self._get_update_info_for_instrument_without_default(instrument)
        except missingData:
            return {}
        else:
            return update_info

    def _get_update_info_for_instrument_without_default(
        self, instrument
    ):
        try:
            update_info = self._update_info_store[instrument]
        except KeyError:
            raise missingData("price update info %s not found in control store" % instrument)
        return update_info

    def _update_update_info_for_instrument(self, instrument, new_update_info_object):
        try:
            self._get_update_info_for_instrument_without_default(instrument)
        except missingData:
            self._add_update_info_for_instrument(instrument, new_update_info_object)
        else:
            self._modify_existing_update_info_for_instrument(
                instrument, new_update_info_object
            )

    def _add_update_info_for_instrument(self, instrument, new_update_info_object):
        self._update_info_store[instrument] = new_update_info_object

    def _modify_existing_update_info_for_instrument(
        self, instrument, new_update_info_object
    ):
        self._update_info_store[instrument] = new_update_info_object

    def delete_update_info_for_instrument(self, instrument):
        raise NotImplementedError
