
import copy
import os.path as osp
import os
import struct
from traceback import format_exc

import numpy as np
import rosbag
import sensor_msgs.point_cloud2 as pc2
from cv_bridge import CvBridge

from loguru import logger
# from utils.time_utils import get_current_time
import open3d as o3d


# PCD_ASCII_TEMPLATE = """VERSION 0.7
# FIELDS x y z intensity
# SIZE 4 4 4 2
# TYPE F F F U
# COUNT 1 1 1 1
# WIDTH {}
# HEIGHT 1
# VIEWPOINT 0 0 0 1 0 0 0
# POINTS {}
# DATA ascii
# """

# PCD_BINARY_TEMPLATE = """VERSION 0.7
# FIELDS x y z intensity
# SIZE 4 4 4 4
# TYPE F F F F
# COUNT 1 1 1 1
# WIDTH {}
# HEIGHT 1
# VIEWPOINT 0 0 0 1 0 0 0
# POINTS {}
# DATA binary
# """

PCD_ASCII_TEMPLATE = """# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z
SIZE 4 4 4
TYPE F F F
COUNT 1 1 1
WIDTH {}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {}
DATA ascii
"""

PCD_BINARY_TEMPLATE = """# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z intensity ring time
SIZE 4 4 4 4 2 4
TYPE F F F F U F
COUNT 1 1 1 1 1 1
WIDTH {}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {}
DATA binary
"""


class BagExtractor:
    def __init__(self, bag_file, dst_folder):
        self.bag_file = bag_file
        self.dst_folder = dst_folder
        self.bridge = CvBridge()

    def run(self):
        """
        读取bag文件
        :return:
        """
        # 读取bag文件
        with rosbag.Bag(self.bag_file, 'r') as bag:
            # 读取bag信息
            info = bag.get_type_and_topic_info()

            # 读取pcd坐标的topic
            pcd_topic, odometry_topic, total = self.read_bag_point_topic(info)
            logger.info("pcd_topic: {}, odometry_topic: {}, total: {}".format(pcd_topic, odometry_topic, total))
            if total == 0:
                logger.error(f'{self.bag_file}  文件数据无法获取')
                raise RuntimeError(f'{self.bag_file}  文件数据无法获取')
            # 读取信息
            cur = 0
            for topic, msg, t in bag.read_messages():

                if topic == pcd_topic:
                    # 读取时间戳
                    time_str = "%.3f" % msg.header.stamp.to_sec()
                    # 文件地址
                    pcd_path = os.path.join(self.dst_folder, "{}.pcd".format(time_str))
                    cur += 1
                    progress = "%.2f" % (cur / total * 100)
                    # 转ascii码 生成文件
                    self.to_pcd_ascii(pcd_path, msg)
                    logger.info(f'文件总数：{total}, 生成第{cur}个文件：{pcd_path}, 进度：{progress}%')
                elif topic == odometry_topic:
                    time = msg.header.stamp.secs + msg.header.stamp.nsecs * (10 ** -9)
                    # 读取时间戳
                    time_str = "%.3f" % time
                    logger.info("时间戳：{}".format(time_str))
                    cur += 1
                    progress = "%.2f" % (cur / total * 100)
                    # 文件地址
                    txt_path = os.path.join(self.dst_folder, "{}.txt".format(time_str))
                    self.to_txt_ascii(txt_path, msg)
                    logger.info(f'文件总数：{total}, 生成第{cur}个文件: {txt_path}, 进度：{progress}%')

    @staticmethod
    def read_bag_point_topic(info):
        logger.info(info.topics)
        pcd_topic = None
        odometry_topic = None
        total = 0
        for topic in info.topics:
            if info.topics.get(topic).msg_type == 'nav_msgs/Odometry':
                total += info.topics.get(topic).message_count
                odometry_topic = topic
            elif info.topics.get(topic).msg_type == 'sensor_msgs/PointCloud2':
                total += info.topics.get(topic).message_count
                pcd_topic = topic
        return pcd_topic, odometry_topic, total

    @staticmethod
    def to_txt_ascii(txt_path, msg):
        """
        获取Odometry, 生成文件
        :param txt_path:
        :param msg:
        :return:
        """
        # logger.info(f'{msg}')
        with open(txt_path, mode='w', encoding='gbk') as file:
            file.write(str(msg))



    @staticmethod
    def to_pcd_ascii(pcd_path, msg):
        """
        获取坐标，利用open3d生成文件
        :param pcd_path:
        :param msg:
        :return:
        """
        points_data = list(pc2.read_points(msg))
        # logger.info(f'{points_data}')
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points_data)[:, :3]) # 只取前三列
        # logger.info(f'{pcd}')
        o3d.io.write_point_cloud(pcd_path, pcd)


    # @staticmethod
    # def to_pcd_binary(pcd_path, msg):
    #     with open(pcd_path, 'wb') as f:
    #         points_data = np.array(list(pc2.read_points(msg)))
    #         lidar = list(np.delete(points_data, np.where(np.isnan(points_data))[0], axis=0))
    #         header = copy.deepcopy(PCD_BINARY_TEMPLATE).format(len(lidar), len(lidar))
    #         f.write(header.encode())
    #         for pi in lidar:
    #             h = struct.pack('ffff', pi[0], pi[1], pi[2], pi[3])
    #             f.write(h)


def main():
    bag_file_path = r"C:\Users\Administrator\Desktop\bag_test\data_2023-11-06-17-26-14.bag"
    bag_dir = r"C:\Users\Administrator\Desktop\bag_test\data_2023-11-06-17-26-14\tmp"

    if not os.path.exists(bag_dir):
        os.mkdir(bag_dir)
    try:
        BagExtractor(bag_file_path, bag_dir).run()
    except Exception as e:
        logger.error(f'{bag_file_path} 解析失败')


if __name__ == '__main__':
    main()
