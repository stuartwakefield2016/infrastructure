import logging
from infrastructure.stacks.network import NetworkStack
from botocore.exceptions import ClientError


def main():
    logger = logging.getLogger()

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        logger.info('building NetworkStack')
        network = NetworkStack("StuartWakefield2016Network")
        network.build()
        logger.info('building of NetworkStack complete')
    except ClientError as err:
        logger.error(err)


if __name__ == '__main__':
    main()
