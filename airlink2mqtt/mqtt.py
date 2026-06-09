import asyncio
import json
import logging
from typing import Optional

import aiomqtt
from aioairlinksms.exceptions import (
    AirlinkSMSMessageDecodeError,
    AirlinkSMSMessageEncodeError,
)
from aioairlinksms.udp import AirlinkSMSMessage, AirlinkSMSUDPServerProtocol

from .matcher import Matcher

logger = logging.getLogger(__name__)


class AirlinkMqttClient:
    """A client that bridges AirLink SMS messages to MQTT and vice versa."""

    def __init__(
        self,
        hostname: str,
        port: int,
        mqtt_topic_prefix: str,
        username: Optional[str],
        password: Optional[str],
        reconnect_interval: int = 5,
        matcher: Optional[Matcher] = None,
    ) -> None:
        self.hostname = hostname
        self.port = port
        self.mqtt_topic_prefix = mqtt_topic_prefix
        self.username = username
        self.password = password
        self.reconnect_interval = reconnect_interval
        self.tx_topic = f"{self.mqtt_topic_prefix}/message/send"
        self.rx_topic = f"{self.mqtt_topic_prefix}/message/receive"
        self.matcher = matcher


    async def _airlink_to_mqtt(
        self,
        al_client: AirlinkSMSUDPServerProtocol,
        mq_client: aiomqtt.Client,
    ) -> None:
        """Relay messages from Airlink to MQTT."""
        async for message in al_client.messages:
            try:
                logger.debug("Received message from AirLink: %s", message)
                if self.matcher:
                    match_result = self.matcher.match(message)
                    if match_result:
                        logger.debug(f"Message matched condition: {match_result.condition.name}")
                        match_payload = json.dumps(match_result.serialize())
                        await mq_client.publish(
                            topic=f"{self.rx_topic}/match/{match_result.condition.name}",
                            payload=match_payload,
                        )
                        continue
                payload = json.dumps(message.as_dict())
                logger.debug(f"Publishing verbatim message to topic {self.rx_topic}")
                await mq_client.publish(topic=self.rx_topic, payload=payload)
            except AirlinkSMSMessageDecodeError as e:
                logger.error(
                    f"Error handling AirLink message: {e.__class__.__name__}",
                    exc_info=e,
                )

    async def _mqtt_to_airlink(
        self,
        al_client: AirlinkSMSUDPServerProtocol,
        mq_client: aiomqtt.Client,
    ) -> None:
        """Relay messages from MQTT to Airlink."""
        async with mq_client.messages() as messages:
            async for message in messages:
                try:
                    if not isinstance(message.payload, bytes):
                        raise ValueError("Received invalid MQTT message payload type")
                    if str(message.topic) != self.tx_topic:
                        logger.warning(
                            f"Received message on unexpected topic: {message.topic}"
                        )
                        raise ValueError("Received message on unexpected topic")
                    payload_str = message.payload.decode()
                    logger.debug("Received message from MQTT: %s", payload_str)
                    payload = json.loads(payload_str)
                    al_msg = AirlinkSMSMessage.from_dict(payload)
                    al_client.send(al_msg)
                except (
                    json.JSONDecodeError,
                    AirlinkSMSMessageEncodeError,
                    ValueError,
                ) as e:
                    logger.error(
                        f"Error processing MQTT message: {e.__class__.__name__}",
                        exc_info=e,
                    )

    async def run(
        self,
        al_client: AirlinkSMSUDPServerProtocol,
    ) -> None:
        """Run the MQTT client loop, bridging messages between AirLink and MQTT.

        Args:
            al_client: The AirLink SMS UDP server protocol instance.
        """
        logger.info(f"Connecting to MQTT broker at {self.hostname}:{self.port}")
        while True:
            try:
                async with aiomqtt.Client(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                ) as mq_client:
                    logger.info("Connected to MQTT broker")
                    await mq_client.subscribe(self.tx_topic)

                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._airlink_to_mqtt(al_client, mq_client))
                        tg.create_task(self._mqtt_to_airlink(al_client, mq_client))
            except aiomqtt.MqttError as error:
                logger.error(
                    f"MQTT error: {error}. Reconnecting in {self.reconnect_interval} seconds..."
                )
                await asyncio.sleep(self.reconnect_interval)
