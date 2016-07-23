import sys
import logging
import time
from botocore.exceptions import ClientError
from infrastructure.stack import YamlTemplate, RawStack, StackEventLog


def readfile(path):
    with open(path, 'r') as f:
        return f.read()


stopped_statuses = [
    'CREATE_COMPLETE',
    'UPDATE_COMPLETE',
    'ROLLBACK_COMPLETE',
    'UPDATE_ROLLBACK_COMPLETE',
    'CREATE_FAILED',
    'ROLLBACK_FAILED',
    'UPDATE_ROLLBACK_FAILED'
]
red = '\033[31m'
yellow = '\033[33m'
green = '\033[32m'
light_grey = '\033[37m'
status_colors = {
    'CREATE_COMPLETE': green,
    'UPDATE_COMPLETE': green,
    'ROLLBACK_COMPLETE': yellow,
    'UPDATE_ROLLBACK_COMPLETE': yellow,
    'CREATE_FAILED': red,
    'ROLLBACK_FAILED': red,
    'UPDATE_ROLLBACK_FAILED': red
}
default_status_color = light_grey


def formatevent(event):
    return '{0}{1}\033[0m - {2} \033[1m{3} \033[0m{4}\n'.format(
        getstatuscolor(event['ResourceStatus']),
        event['ResourceStatus'],
        event['ResourceType'],
        event['LogicalResourceId'],
        '(' + event['PhysicalResourceId'] + ')' if event['PhysicalResourceId'] != ''
        else ''
    )


def getstatuscolor(status):
    return status_colors[status] if status in status_colors else default_status_color


def run(name, definition_path, params):
    logger = logging.getLogger(__name__)

    stack = RawStack(name, YamlTemplate(readfile(definition_path)))
    stack_event_log = StackEventLog(stack)

    try:
        logger.info('Create stack')
        stack.build(params)
        logger.info('Create successful')
    except ClientError as err:
        logger.error(err)

    while True:

        status = stack.status()
        events = stack_event_log.next_events()

        sys.stdout.write(' ' * 80 + '\r')

        for event in events:
            sys.stdout.write(formatevent(event))

        sys.stdout.write('Stack status: {0}{1}\033[0m\r'.format(
            getstatuscolor(status),
            status
        ))
        sys.stdout.flush()

        if status in stopped_statuses:
            sys.stdout.write('\n')
            break

        time.sleep(0.2)
