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
mqtt-host: 192.168.1.100
mqtt-user: myuser
mqtt-password: mypassword
airlink-host: 192.168.43.1
airlink-port: 8000
airlink-listen-port: 8001
```

## Example

To connect to an Airlink modem at `192.168.43.1` (that is listening on port 8000 and replying on port 8001) and an MQTT broker at `192.168.1.100`:

```bash
airlink2mqtt --airlink-host 192.168.43.1 --airlink-port 8000 --airlink-listen-port 8001 --mqtt-host 192.168.1.100 --verbose
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

## License

This project is licensed under the MIT License.
