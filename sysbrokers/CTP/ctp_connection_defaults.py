from sysdata.config.production_config import get_production_config
from syscore.constants import arg_not_supplied

LIST_OF_CTP_PARAMS = ['ctp_data_dir', "ctp_trader_server", "ctp_md_server", "ctp_user_id", 'ctp_broker_id',
                      'ctp_password', 'ctp_app_id', 'ctp_auth_code']


def ctp_defaults(**kwargs):
    """
    Returns ib configuration with following precedence
    1- if passed in arguments: ipaddress, port, idoffset - use that
    2- if defined in private_config file, use that. ib_ipaddress, ib_port, ib_idoffset
    3 - if defined in system defaults file, use that

    :return: mongo db, hostname, port
    """

    # this will include defaults.yaml if not defined in private
    passed_param_names = list(kwargs.keys())
    output_dict = {}
    config = get_production_config()
    for param_name in LIST_OF_CTP_PARAMS:
        if param_name in passed_param_names:
            param_value = kwargs[param_name]
        else:
            param_value = arg_not_supplied

        if param_value is arg_not_supplied:
            param_value = getattr(config, param_name)

        output_dict[param_name] = param_value

    # Get from dictionary


    return output_dict
