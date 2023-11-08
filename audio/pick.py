"""
pick up sound from microphone
"""
import copy
import logging
import time
import threading
import sounddevice as sd

import wavio
import numpy as np

logger = logging.getLogger(__name__)


class SoundPicker:
    def __init__(self, file_base_url: str = "", record_norm_volume_threshold: int = 5, sample_rate: int = 44100,
                 block_size: int = 512 * 1024, how_much_small_volumes_stop_record: int = 10):
        self.cfg_record_norm_volume_threshold = record_norm_volume_threshold  # 需要调优的值，触发采集的最小归一化声音幅度值。设置大杂音小，设置小灵敏高
        self.cfg_sample_rate = sample_rate  # 采样率
        self.cfg_block_size = block_size  # 这个值不确定是不是真的有用
        self.cfg_file_base_url = file_base_url
        self.cfg_how_much_small_volumes_stop_record = how_much_small_volumes_stop_record

        self.buff_data = []  # 待写入wave文件的缓冲区

        self.flag_should_record_wave_file = False  # 写文件标记
        self.flag_consecutive_zero_count = 0  # 连零数

    def record(self):
        default_input = self._find_first_input_dev()  # 用来标定默认的音频输入设备
        if default_input is None:
            logger.error("no input device")
            return

        sd.InputStream(device=default_input['index'], samplerate=self.cfg_sample_rate,
                       channels=default_input['max_input_channels'], blocksize=self.cfg_block_size)

        # Use a breakpoint in the code line below to debug your script.
        with sd.Stream(callback=self._save_sound_call_back):
            print("Recording... Press Ctrl+C to stop.")
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                print("Recording stopped.")

    @staticmethod
    def _find_first_input_dev():
        input_devices = sd.query_devices()
        # 这里有坑，sd.query_devices返回的可能是字典，也可能是字典列表
        # 找第一个单纯输入设备
        for device in input_devices:
            if device['max_input_channels'] != 0 and device['max_output_channels'] == 0:
                default_input = device
                return default_input

        return None

    def _save_sound_call_back(self, in_data, out_data, frames, usage_time, status):
        # indata是强度数值, frames是采样的桢数当前是512
        # global Num_data
        # global should_record_wave_file
        # global consecutive_zero_count

        volume_norm = np.linalg.norm(in_data) * 10
        # print_sound_amplitude

        value = int(volume_norm)
        """
        幅度不是0的需要写入文件，如果连零数不超过cfg_how_much_small_volumes_stop_record，写入不中断。
        当有cfg_how_much_small_volumes_stop_record个连零的时候，一个文件写入完成。
        连零结束后第一个非零值，触发生成新的文件。
        """
        if value > self.cfg_record_norm_volume_threshold:
            self.flag_should_record_wave_file = True
            self.flag_consecutive_zero_count = 0
        else:
            self.flag_consecutive_zero_count = self.flag_consecutive_zero_count + 1

        if self.flag_consecutive_zero_count > 65535:
            self.flag_consecutive_zero_count = 100

        if self.flag_should_record_wave_file:
            if self.buff_data is None:
                self.buff_data = in_data
            else:
                self.buff_data = np.append(self.buff_data, in_data)

        if self.flag_should_record_wave_file \
                and self.flag_consecutive_zero_count > self.cfg_how_much_small_volumes_stop_record:
            self.flag_should_record_wave_file = False
            print(f"volume_norm={value} consecutive_zero_count={self.flag_consecutive_zero_count} file saved")

            file_data = copy.copy(self.buff_data)
            self.buff_data = None

            thread = threading.Thread(target=_save_file, args=(self, file_data))
            thread.start()

        if status:
            # 缓存overflow会出现在这里
            print(f"Audio callback status: {status}")

    @staticmethod
    def _print_sound_amplitude(volume_norm):
        """
        打印归一化的声音幅度
        """
        if int(volume_norm) > 0:
            print("|" * int(volume_norm))


def _save_file(sp: SoundPicker, indata):
    now = int(time.time() * 1000 * 1000)
    file_name = sp.cfg_file_base_url + str(now) + "_audio.wav"
    logger.debug(f"save to file {file_name} Len={len(indata)}")

    wavio.write(file_name, indata, sp.cfg_sample_rate, sampwidth=2)
