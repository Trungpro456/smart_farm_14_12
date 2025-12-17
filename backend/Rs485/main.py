import paho.mqtt.client as mqtt
from src.constant.init import Constant
from src.mqtt import Mqtt


def main():
    client = mqtt.Client()
    client.on_connect = Mqtt.on_connect
    client.on_message = Mqtt.on_message

    client.connect(Constant.BROKER, Constant.PORT, 60)
    Mqtt.check_timeout(client)
    client.loop_forever()


if __name__ == "__main__":
    main()
