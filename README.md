# airlink2mqtt

An asyncio Python tool for bridging SMS traffic between Sierra Wireless Airlink modems and an MQTT broker.

This tool uses [aioairlinksms](https://github.com/nkaminski/aioairlinksms) to communicate with the Airlink modem.

#### This is under active development and is subject to breaking API and/or usage changes at any time!

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management. To install the project and dependencies, run:

```bash
poetry install
```
or
```
pip install .
```

## Usage

This project provides a command-line interface for bridging the SMS messages.

```bash
airlink2mqtt [OPTIONS]
```

### Options

- `-c`, `--config TEXT`: Path to a YAML configuration file.
- `-m`, `--match-cond-file TEXT`: Path to a YAML file containing match conditions.
- `-h`, `--mqtt-host TEXT`: MQTT broker host. (Default: `localhost`)
- `-u`, `--mqtt-user TEXT`: MQTT username.
- `-p`, `--mqtt-password TEXT`: MQTT password.
- `-t`, `--mqtt-topic-prefix TEXT`: MQTT topic prefix. (Default: `airlink`)
- `-o`, `--mqtt-port INTEGER`: MQTT broker port. (Default: 1883)
- `-H`, `--airlink-host TEXT`: AirLink modem host.
- `-P`, `--airlink-port INTEGER`: AirLink modem port.
- `-L`, `--airlink-listen-port INTEGER`: AirLink modem listen port.
- `-A`, `--airlink-bind-addr TEXT`: Address to bind to for AirLink modem. (Default: `0.0.0.0`)
- `-v`, `--verbose`: Enable verbose logging.
- `--help`: Show this message and exit.

All options can also be provided in a YAML configuration file. For example:

```yaml
mqtt_host: 192.168.1.100
mqtt_user: myuser
mqtt_password: mypassword
airlink_host: 192.168.43.1
airlink_port: 8000
airlink_listen_port: 8001
match_cond_file: /path/to/match_conditions.yaml
```

## Example

To connect to an Airlink modem at `192.168.43.1` (that is listening on port 8000 and replying on port 8001) and an MQTT broker at `192.168.1.100`:

```bash
airlink2mqtt --airlink-host 192.168.43.1 --airlink-port 8000 --airlink-listen-port 8000 --mqtt-host 192.168.1.100 --verbose
```

## MQTT Topics

This tool will publish received SMS messages to the topic `<mqtt-topic-prefix>/message/receive`.

To send an SMS message, publish a JSON payload to the topic `<mqtt-topic-prefix>/message/send`.

The JSON payload should have the following format:
```json
{
  "phone_number": "+15551234567",
  "message": "Hello from MQTT!"
}
```

## Match Conditions

You can conditionally match and route incoming SMS messages to specific MQTT topics using Python regular expressions.

To enable matching, provide a path to a YAML file containing match conditions using the `-m` / `--match-cond-file` option or through the configuration file.

### Match Conditions File Format

The match conditions file is a YAML dictionary where keys are the condition names and values are regular expression patterns. You can use named capture groups (e.g. `(?P<group_name>pattern)`) to extract specific fields from the message.

Example `match_conditions.yaml`:

```yaml
system_alert: "^ALRT\\s+(?P<message>.*)"
```

### Routing and Payload

When a received SMS matches a condition:
1. It is routed to `<mqtt-topic-prefix>/message/receive/match/<condition-name>` instead of the default `<mqtt-topic-prefix>/message/receive` topic.
2. The payload is published as a JSON object containing the matched condition name and any extracted named capture groups.

For example, if the SMS message is `ALRT Disk Full`, it matches the `system_alert` pattern and publishes the following JSON to `airlink/message/receive/match/system_alert`:

```json
{
  "name": "system_alert",
  "named_groups": {
    "message": "Disk Full"
  }
}
```

If no condition matches the message, it is published to the default topic (`<mqtt-topic-prefix>/message/receive`) as a raw message.

## Container Support

You can build and run this tool as a container using the provided `Containerfile`.

### Build the Image

To build the container image using Podman:

```bash
podman build -t airlink2mqtt .
```

### Run the Container

To run the container, pass your configuration file (or command-line arguments) and mount the necessary files:

```bash
podman run --rm -it \
  -v $(pwd)/config.yaml:/app/config.yaml:Z \
  -v $(pwd)/match_conditions.yaml:/app/match_conditions.yaml:Z \
  airlink2mqtt --config /app/config.yaml --match-cond-file /app/match_conditions.yaml
```

## License

This project is licensed under the MIT License.
