import logging
import sys
import os
from infrastructure.runner import run


def setuplogging():
    logger = logging.getLogger()

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    )
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logging.getLogger("botocore").setLevel(logging.ERROR)

    return logger


def main():
    setuplogging()
    run('StuartWakefield2016', 'definition.yml', {
        'PublicContainerClusterAmi': os.environ.get('ECS_AMI'),
        'EcsInstanceRole': os.environ.get('ECS_INSTANCE_ROLE')
    })
    return 0


if __name__ == '__main__':
    sys.exit(main())
