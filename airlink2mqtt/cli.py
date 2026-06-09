import logging
import os
import re
from typing import Optional

import aioairlinksms.udp
import asyncclick as click
import yaml

from .const import MQTT_DEFAULT_HOST, MQTT_DEFAULT_PORT, MQTT_DEFAULT_TOPIC_PREFIX
from .matcher import MatchCondition, Matcher
from .mqtt import AirlinkMqttClient

logger = logging.getLogger("airlink2mqtt")


def process_config(
    ctx: click.Context, param: click.Option, value: Optional[str]
) -> Optional[str]:
    if value and os.path.exists(value):
        try:
            with open(value, "r") as f:
                config = yaml.safe_load(f) or {}
            if not isinstance(config, dict):
                raise ValueError("Config file must contain a dictionary.")
            ctx.default_map = ctx.default_map or {}
            ctx.default_map.update(config)
        except (yaml.YAMLError, ValueError) as e:
            raise click.BadParameter(f"Invalid config file: {e}")
    return value


@click.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    callback=process_config,
    is_eager=True,
    help="Path to a YAML configuration file.",
)
@click.option(
    "-m",
    "--match-cond-file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Path to a YAML file containing match conditions.",
)
@click.option(
    "-h",
    "--mqtt-host",
    help="MQTT broker host",
    default=MQTT_DEFAULT_HOST,
    show_default=True,
)
@click.option("-u", "--mqtt-user", help="MQTT username")
@click.option("-p", "--mqtt-password", help="MQTT password")
@click.option(
    "-t",
    "--mqtt-topic-prefix",
    help="MQTT topic prefix",
    default=MQTT_DEFAULT_TOPIC_PREFIX,
    show_default=True,
)
@click.option(
    "-o",
    "--mqtt-port",
    type=int,
    default=MQTT_DEFAULT_PORT,
    show_default=True,
    help="MQTT broker port",
)
@click.option("-H", "--airlink-host", help="AirLink modem host")
@click.option("-P", "--airlink-port", type=int, help="AirLink modem port")
@click.option("-L", "--airlink-listen-port", type=int, help="AirLink modem listen port")
@click.option(
    "-A",
    "--airlink-bind-addr",
    default="0.0.0.0",
    show_default=True,
    help="Address to bind to for AirLink modem",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging.")
async def main(
    config: Optional[str],
    match_cond_file: Optional[str],
    mqtt_host: str,
    mqtt_user: Optional[str],
    mqtt_password: Optional[str],
    mqtt_topic_prefix: str,
    mqtt_port: int,
    airlink_host: str,
    airlink_port: int,
    airlink_listen_port: int,
    airlink_bind_addr: str,
    verbose: bool,
) -> None:
    """A tool to bridge AirLink modem data to MQTT.

    This function sets up the MQTT client and AirLink UDP handler,
    then runs the forwarding loop.
    """

    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)

    required_params = {
        "airlink-host": airlink_host,
        "airlink-port": airlink_port,
        "airlink-listen-port": airlink_listen_port,
    }
    missing_params = [
        param for param, value in required_params.items() if value is None
    ]
    if missing_params:
        param_list = ", ".join(f"--{p}" for p in missing_params)
        raise click.BadParameter(
            message=f"The following options are required either via command line or config file: {param_list}",
        )

    logger.info("Starting airlink2mqtt...")
    logger.debug(f"MQTT Broker Host: {mqtt_host}")
    logger.debug(f"MQTT Broker Port: {mqtt_port}")
    logger.debug(f"MQTT Username: {mqtt_user}")
    logger.debug(f"MQTT Topic Prefix: {mqtt_topic_prefix}")
    logger.debug(f"AirLink Modem Host: {airlink_host}")
    logger.debug(f"AirLink Modem Port: {airlink_port}")
    logger.debug(f"AirLink Modem Listen Port: {airlink_listen_port}")
    logger.debug(f"AirLink Modem Bind Address: {airlink_bind_addr}")

    matcher = None
    if match_cond_file:
        try:
            with open(match_cond_file, "r") as f:
                config = yaml.safe_load(f) or {}
            if not isinstance(config, dict):
                raise ValueError("Match conditions file must contain a dictionary of name: regex.")
            conditions = [MatchCondition(n, r) for n, r in config.items()]
            matcher = Matcher(conditions)
            logger.info(f"Loaded {len(conditions)} match conditions from {match_cond_file}")
        except (yaml.YAMLError, ValueError, re.error) as e:
            raise click.BadParameter(f"Invalid match conditions file: {e}")
    
    mqtt_client = AirlinkMqttClient(
        hostname=mqtt_host,
        port=mqtt_port,
        username=mqtt_user,
        password=mqtt_password,
        mqtt_topic_prefix=mqtt_topic_prefix,
        matcher=matcher,
    )
    async with aioairlinksms.udp.create_message_handler(
        remote_addr=airlink_host,
        remote_port=airlink_port,
        local_bind_addr=airlink_bind_addr,
        local_bind_port=airlink_listen_port,
    ) as airlink:
        logger.info("Started Airlink SMS listener...")
        await mqtt_client.run(airlink)


if __name__ == "__main__":
    main(_anyio_backend="asyncio")
