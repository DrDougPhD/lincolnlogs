import lincolnlogs


def main():
    logger = lincolnlogs.setup(verbosity='DEBUG')
    logger.info('Hello World!')


if __name__ == '__main__':
    main()
