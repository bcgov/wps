import logging

from app import configure_logging

logger = logging.getLogger(__name__)

def main():
    logger.info("***************Cron job started**************")

if __name__ == '__main__':
    configure_logging()
    main()