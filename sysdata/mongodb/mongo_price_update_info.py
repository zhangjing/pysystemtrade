from sysdata.production.price_update_info import priceUpdateInfoData
from syscore.constants import arg_not_supplied

from sysdata.mongodb.mongo_generic import mongoDataWithSingleKey
from syslogdiag.log_to_screen import logtoscreen

PRICE_UPDATE_INFO_COLLECTION = "price_update_info"
PRICE_UPDATE_INFO_KEY = "instrument"


class mongoPirceUpdateInfoData(priceUpdateInfoData):
    """
    Read and write data class to get price update info


    """

    def __init__(
        self, mongo_db=arg_not_supplied, log=logtoscreen("mongoPriceUpdateInfoData")
    ):

        super().__init__(log=log)

        self._mongo_data = mongoDataWithSingleKey(
            PRICE_UPDATE_INFO_COLLECTION, PRICE_UPDATE_INFO_KEY, mongo_db=mongo_db
        )

    @property
    def mongo_data(self):
        return self._mongo_data

    def __repr__(self):
        return "Data connection for price update info, mongodb %s" % str(self.mongo_data)

    def get_list_of_instrument(self):
        return self.mongo_data.get_list_of_keys()

    def _get_update_info_for_instrument_without_default(
        self, instrument
    ):
        result_dict = self.mongo_data.get_result_dict_for_key_without_key_value(
            instrument
        )
        return result_dict

    def _modify_existing_update_info_for_instrument(
        self, instrument, new_update_info_object
    ):
        self.mongo_data.add_data(
            instrument, new_update_info_object, allow_overwrite=True
        )

    def _add_update_info_for_instrument(self, instrument, new_update_info_object):
        self.mongo_data.add_data(
            instrument, new_update_info_object, allow_overwrite=False
        )

    def delete_update_info_for_instrument(self, instrument):
        self.mongo_data.delete_data_without_any_warning(instrument)
