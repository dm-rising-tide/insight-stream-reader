import os
import sys
import logging
import logging.config
from stream_reader import InsightReader
def __parse_runtime_and_config():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', type=str, dest='base', help='app base dir', default = '')
    parser.add_argument('-d', type=str, dest='pwd', help='runtime dir', default = '')

    args = parser.parse_args()
    basepath = os.path.realpath(args.pwd)
    os.chdir(basepath)
    print basepath
    logging.config.fileConfig(basepath + '/conf/logging.conf')

    import ConfigParser

    conffile = basepath + '/conf/tide.conf'
    conf = ConfigParser.RawConfigParser()
    conf.read(conffile)

    
    conf_path =  basepath + '/conf/insight.conf'
    insight_conf = ConfigParser.RawConfigParser()
    insight_conf.read(conf_path)
    return (args, conf, insight_conf)

if __name__ == "__main__":
    args, conf, insight_conf = __parse_runtime_and_config()
    logger = logging.getLogger('tide')
    logger.info("start...")
    sys.path.append(args.base + '/lib/')
    #import log_collector
    

    worker = InsightReader(insight_conf)
    worker.run()










































