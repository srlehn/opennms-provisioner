"""
opennms-provisioner main module

This is the main module of opennms-provisioner

:license: MIT, see LICENSE for more details
:copyright: (c) 2018 by Michael Batz, see AUTHORS for more details
"""
import argparse
import os
import sys
import logging
import logging.config
import pkg_resources
import provisioner.config
import provisioner.executor

def main():
    """main function"""

    # get config and JobUtilty
    appconfig = provisioner.config.AppConfig(pkg_resources.resource_filename(__name__, "data/etc/appconfig.conf"))
    jobutil = provisioner.executor.JobUtility(appconfig)

    # get logging
    logging.basedir = pkg_resources.resource_filename(__name__, "data/logs")
    logconfig = pkg_resources.resource_filename(__name__, "data/etc/logging.conf")
    logging.config.fileConfig(logconfig)
    logger = logging.getLogger("app")

    # parse arguments
    parser = argparse.ArgumentParser(description="Helper for OpenNMS Provisioning")
    parser.add_argument("jobname", help="name of the provisioning job")
    args = parser.parse_args()

    # get job
    try:
        job = jobutil.create_job(args.jobname)
        job.execute()
    except provisioner.executor.ConfigException as e:
        logger.error("Configuration Error: %s", e)
        sys.exit(-1)
    except provisioner.executor.SourceException as e:
        logger.error("Source Error: %s", e)
        sys.exit(-1)
    except provisioner.executor.TargetException as e:
        logger.error("Target Error: %s", e)
        sys.exit(-1)


if __name__ == "__main__":
    main()
