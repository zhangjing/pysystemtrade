from dataclasses import dataclass
import pandas as pd

from sysbrokers.IB.ib_instruments import (
    futuresInstrumentWithIBConfigData,
    NOT_REQUIRED_FOR_IB,
    ibInstrumentConfigData,
)
from syscore.constants import missing_file, missing_instrument, arg_not_supplied
from syscore.exceptions import missingData
from syscore.fileutils import resolve_path_and_filename_for_package
from syscore.genutils import return_another_value_if_nan
from syslogdiag.log_to_screen import logtoscreen
from syslogdiag.pst_logger import pst_logger
from sysobjects.instruments import futuresInstrument


class IBconfig(pd.DataFrame):
    pass


IB_FUTURES_CONFIG_FILE = resolve_path_and_filename_for_package(
    "sysbrokers.IB.config.ib_config_futures.csv"
)


def read_ib_config_from_file(log: pst_logger = logtoscreen("")) -> IBconfig:
    try:
        df = pd.read_csv(IB_FUTURES_CONFIG_FILE)
    except BaseException:
        log.warn("Can't read file %s" % IB_FUTURES_CONFIG_FILE)
        return missing_file

    return IBconfig(df)


def get_instrument_object_from_config(
    instrument_code: str, config: IBconfig = None, log: pst_logger = logtoscreen("")
) -> futuresInstrumentWithIBConfigData:

    new_log = log.setup(instrument_code=instrument_code)

    if config is None:
        config = read_ib_config_from_file()

    if config is missing_file:
        new_log.warn(
            "Can't get config for instrument %s as IB configuration file missing"
            % instrument_code
        )
        return missing_instrument

    list_of_instruments = get_instrument_list_from_ib_config(config=config, log=log)
    try:
        assert instrument_code in list_of_instruments
    except:
        new_log.warn("Instrument %s is not in IB configuration file" % instrument_code)
        return missing_instrument

    futures_instrument_with_ib_data = _get_instrument_object_from_valid_config(
        instrument_code=instrument_code, config=config
    )

    return futures_instrument_with_ib_data


def _get_instrument_object_from_valid_config(
    instrument_code: str, config: IBconfig = None
) -> futuresInstrumentWithIBConfigData:

    config_row = config[config.Instrument == instrument_code]
    symbol = config_row.IBSymbol.values[0]
    exchange = config_row.IBExchange.values[0]
    currency = return_another_value_if_nan(
        config_row.IBCurrency.values[0], NOT_REQUIRED_FOR_IB
    )
    ib_multiplier = return_another_value_if_nan(
        config_row.IBMultiplier.values[0], NOT_REQUIRED_FOR_IB
    )
    price_magnifier = return_another_value_if_nan(
        config_row.priceMagnifier.values[0], 1.0
    )
    ignore_weekly = config_row.IgnoreWeekly.values[0]

    # We use the flexibility of futuresInstrument to add additional arguments
    instrument = futuresInstrument(instrument_code)
    ib_data = ibInstrumentConfigData(
        symbol,
        exchange,
        currency=currency,
        ibMultiplier=ib_multiplier,
        priceMagnifier=price_magnifier,
        ignoreWeekly=ignore_weekly,
    )

    futures_instrument_with_ib_data = futuresInstrumentWithIBConfigData(
        instrument, ib_data
    )

    return futures_instrument_with_ib_data


@dataclass
class IBInstrumentIdentity:
    ib_code: str
    ib_multiplier: float
    ib_exchange: str
    ib_valid_exchange: str


def get_instrument_code_from_broker_instrument_identity(
    config: IBconfig,
    ib_instrument_identity: IBInstrumentIdentity,
    log: pst_logger = logtoscreen(""),
) -> str:

    ib_code = ib_instrument_identity.ib_code
    ib_multiplier = ib_instrument_identity.ib_multiplier
    ib_exchange = ib_instrument_identity.ib_exchange
    ib_valid_exchange = ib_instrument_identity.ib_valid_exchange

    config_rows = _get_relevant_config_rows_from_broker_instrument_identity_fields(
        config=config,
        ib_code=ib_code,
        ib_multiplier=ib_multiplier,
        ib_exchange=ib_exchange,
    )

    if len(config_rows) == 0:
        ## try something else
        ## might have a weird exchange, but the exchange we want is in validExchanges
        try:
            config_rows = _get_relevant_config_rows_from_broker_instrument_identity_using_multiple_valid_exchanges(
                config=config, ib_instrument_identity=ib_instrument_identity
            )

        except:
            msg = (
                "Broker symbol %s (exchange:%s, valid_exchange:%s multiplier:%f) not found in configuration file!"
                % (
                    ib_code,
                    ib_exchange,
                    ib_valid_exchange,
                    ib_multiplier,
                )
            )
            log.critical(msg)
            raise Exception(msg)

    if len(config_rows) > 1:

        msg = (
            "Broker symbol %s (%s, %f) appears more than once in configuration file!"
            % (ib_code, ib_exchange, ib_multiplier)
        )
        log.critical(msg)
        raise Exception(msg)

    return config_rows.iloc[0].Instrument


def _get_relevant_config_rows_from_broker_instrument_identity_using_multiple_valid_exchanges(
    config: IBconfig, ib_instrument_identity: IBInstrumentIdentity
) -> pd.Series:

    ib_code = ib_instrument_identity.ib_code
    ib_multiplier = ib_instrument_identity.ib_multiplier
    ib_valid_exchange = ib_instrument_identity.ib_valid_exchange

    valid_exchanges = ib_valid_exchange.split(",")

    for ib_exchange in valid_exchanges:
        config_rows = _get_relevant_config_rows_from_broker_instrument_identity_fields(
            config=config,
            ib_code=ib_code,
            ib_multiplier=ib_multiplier,
            ib_exchange=ib_exchange,
        )

        if len(config_rows) == 1:
            ## we have a match!
            return config_rows

    raise missingData


def _get_relevant_config_rows_from_broker_instrument_identity_fields(
    config: IBconfig, ib_code: str, ib_multiplier: float, ib_exchange: str
) -> pd.Series:

    config_rows = config[
        (config.IBSymbol == ib_code)
        & (config.IBMultiplier == ib_multiplier)
        & (config.IBExchange == ib_exchange)
    ]

    return config_rows


def get_instrument_list_from_ib_config(
    config: IBconfig, log: pst_logger = logtoscreen("")
):
    if config is missing_file:
        log.warn("Can't get list of instruments because IB config file missing")
        return []

    instrument_list = list(config.Instrument)

    return instrument_list
