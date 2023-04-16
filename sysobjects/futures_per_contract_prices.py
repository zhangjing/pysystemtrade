import pandas as pd
import datetime
from copy import copy

from syscore.pandas.merge_data_keeping_past_data import SPIKE_IN_DATA
from syscore.pandas.frequency import (
    sumup_business_days_over_pd_series_without_double_counting_of_closing_data,
)
from syscore.pandas.merge_data_keeping_past_data import merge_newer_data
from syscore.pandas.full_merge_with_replacement import full_merge_of_existing_data

PRICE_DATA_COLUMNS = sorted(["OPEN", "HIGH", "LOW", "FINAL", "VOLUME", "OPEN_INTEREST", "TOTAL_OPEN_INTEREST"])
FINAL_COLUMN = "FINAL"
VOLUME_COLUMN = "VOLUME"
OPEN_INTEREST_COLUMN = "OPEN_INTEREST"
TOTAL_OPEN_INTEREST_COLUMN = "TOTAL_OPEN_INTEREST"
NOT_VOLUME_COLUMNS = sorted(["OPEN", "HIGH", "LOW", "FINAL"])

VERY_BIG_NUMBER = 999999.0


class futuresContractPrices(pd.DataFrame):
    """
    simData frame in specific format containing per contract information
    """

    def __init__(self, price_data_as_df: pd.DataFrame):
        """

        :param data: pd.DataFrame or something that could be passed to it
        """

        _validate_price_data(price_data_as_df)
        price_data_as_df.index.name = "index"  # for arctic compatibility
        super().__init__(price_data_as_df)

        self._as_df = price_data_as_df

    def __copy__(self):
        return futuresContractPrices(copy(self._as_df))

    @classmethod
    def create_empty(futuresContractPrices):
        """
        Our graceful fail is to return an empty, but valid, dataframe
        """

        data = pd.DataFrame(columns=PRICE_DATA_COLUMNS)

        futures_contract_prices = futuresContractPrices(data)

        return futures_contract_prices

    @classmethod
    def create_from_final_prices_only(
        futuresContractPrices, price_data_as_series: pd.Series
    ):
        price_data_as_series = pd.DataFrame(
            price_data_as_series, columns=[FINAL_COLUMN]
        )
        price_data_as_series = price_data_as_series.reindex(columns=PRICE_DATA_COLUMNS)

        futures_contract_prices = futuresContractPrices(price_data_as_series)

        return futures_contract_prices

    def return_final_prices(self):
        data = self[FINAL_COLUMN]

        return futuresContractFinalPrices(data)

    def _raw_volumes(self) -> pd.Series:
        data = self[VOLUME_COLUMN]

        return data

    def inverse(self):
        new_version = copy(self)
        for colname in NOT_VOLUME_COLUMNS:
            new_version[colname] = 1 / self[colname]

        return futuresContractPrices(new_version)

    def multiply_prices(self, multiplier: float):
        new_version = copy(self)
        for colname in NOT_VOLUME_COLUMNS:
            new_version[colname] = multiplier * self[colname]

        return futuresContractPrices(new_version)

    def add_offset_to_prices(self, offset: float):
        new_version = copy(self)
        for colname in NOT_VOLUME_COLUMNS:
            new_version[colname] = offset + self[colname]

        return futuresContractPrices(new_version)

    def daily_volumes(self) -> pd.Series:
        volumes = self._raw_volumes()

        # stop double counting
        daily_volumes = (
            sumup_business_days_over_pd_series_without_double_counting_of_closing_data(
                volumes
            )
        )

        return daily_volumes

    def daily_open_interest(self) -> pd.Series:
        data = self[OPEN_INTEREST_COLUMN]
        return data

    def total_open_interest(self) -> pd.Series:
        data = self[TOTAL_OPEN_INTEREST_COLUMN]
        return data

    def merge_with_other_prices(
        self,
        new_futures_per_contract_prices,
        only_add_rows=True,
        check_for_spike=True,
        keep_older: bool = True,
    ):
        """
        Merges self with new data.
        If only_add_rows is True,
        Otherwise: Any Nan in the existing data will be replaced (be careful!)

        :param new_futures_per_contract_prices: another futures per contract prices object
        :param keep_older: bool. Keep older data if not NaN (default). False : overwrite older data with non-NaN values. Applicable only to full merge (only_add_rows=False)
        :param check_for_spike Checks for data spikes.
        :return: merged futures_per_contract object
        """
        if only_add_rows:
            return self.add_rows_to_existing_data(
                new_futures_per_contract_prices, check_for_spike=check_for_spike
            )
        else:
            return self._full_merge_of_existing_data(
                new_futures_per_contract_prices,
                check_for_spike=check_for_spike,
                keep_older=keep_older,
            )

    def _full_merge_of_existing_data(
        self,
        new_futures_per_contract_prices,
        check_for_spike=False,
        keep_older: bool = True,
    ):
        """
        Merges self with new data.
        Any Nan in the existing data will be replaced (be careful!)

        :param new_futures_per_contract_prices: the new data
        :param check_for_spike Checks for data spikes.
        :param keep_older: bool. Keep older data (default).
        :return: updated data, doesn't update self
        """

        merged_data = full_merge_of_existing_data(
            self,
            new_futures_per_contract_prices,
            keep_older=keep_older,
            check_for_spike=check_for_spike,
            column_to_check_for_spike=FINAL_COLUMN,
        )

        if merged_data is SPIKE_IN_DATA:
            return SPIKE_IN_DATA

        return futuresContractPrices(merged_data)

    def remove_zero_volumes(self):
        drop_it = self[VOLUME_COLUMN] == 0
        new_data = self[~drop_it]
        return futuresContractPrices(new_data)

    def remove_zero_prices(self):
        drop_it = self[FINAL_COLUMN] == 0.0
        new_data = self[~drop_it]
        return futuresContractPrices(new_data)

    def remove_negative_prices(self):
        drop_it = self[FINAL_COLUMN] < 0.0
        new_data = self[~drop_it]
        return futuresContractPrices(new_data)

    def remove_future_data(self):
        new_data = futuresContractPrices(self[self.index < datetime.datetime.now()])

        return new_data

    def add_rows_to_existing_data(
        self,
        new_futures_per_contract_prices,
        check_for_spike=True,
        max_price_spike: float = VERY_BIG_NUMBER,
    ):
        """
        Merges self with new data.
        Only newer data will be added

        :param new_futures_per_contract_prices: another futures per contract prices object

        :return: merged futures_per_contract object
        """

        merged_futures_prices = merge_newer_data(
            pd.DataFrame(self),
            new_futures_per_contract_prices,
            check_for_spike=check_for_spike,
            max_spike=max_price_spike,
            column_to_check_for_spike=FINAL_COLUMN,
        )

        if merged_futures_prices is SPIKE_IN_DATA:
            return SPIKE_IN_DATA

        merged_futures_prices = futuresContractPrices(merged_futures_prices)

        return merged_futures_prices


class futuresContractFinalPrices(pd.Series):
    """
    Just the final prices from a futures contract
    """

    def __init__(self, data):
        super().__init__(data)


def _validate_price_data(data: pd.DataFrame):
    data_present = sorted(data.columns)

    try:
        assert data_present == PRICE_DATA_COLUMNS
    except AssertionError:
        raise Exception("futuresContractPrices has to conform to pattern")
