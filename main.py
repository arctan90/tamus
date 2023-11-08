import copy
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from audio.pick import SoundPicker

import logging

consecutive_zero_count = 0  # 连零数
sample_rate = 44100
block_size = 512 * 1024
Num_data = []  # 待写入wave文件的缓冲区
should_record_wave_file = False
record_volume_threshold = 5

if __name__ == '__main__':
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # 配置按时间分割的日志处理程序
    timed_handler = TimedRotatingFileHandler('./logfile.log', when='midnight', interval=1, backupCount=7)
    timed_handler.setFormatter(log_formatter)

    # 配置按文件大小分割的日志处理程序
    size_handler = RotatingFileHandler('./logfile.log', maxBytes=400 * 1024 * 1024, backupCount=7)
    size_handler.setFormatter(log_formatter)

    logging.basicConfig(
        level=logging.DEBUG,  # 设置日志级别
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            timed_handler,
            size_handler,
        ]
    )

    sp = SoundPicker()
    sp.record()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
